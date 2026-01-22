from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import os
import platform
import json
import requests
import subprocess
import sys
import shutil
import re
from pathlib import Path
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from django.db import transaction
from django.utils.text import slugify
from core.models import Tenant, UserProfile


@api_view(["POST"])
@permission_classes([AllowAny])
def oauth_exchange(request):
    code = request.data.get("code")

    if not code:
        return JsonResponse({"error": "Missing code"}, status=400)

    token_url = "http://localhost:8000/o/token/"

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://localhost:3000/auth/callback",
        "client_id": settings.OAUTH_CLIENT_ID,
        "client_secret": settings.OAUTH_CLIENT_SECRET,
    }

    r = requests.post(token_url, data=data)
    if r.status_code != 200:
        return JsonResponse({"error": "Token exchange failed", "details": r.text}, status=400)

    token_data = r.json()

    access_token = token_data.get("access_token")

    # Get user info using token
    userinfo = requests.get(
        "http://localhost:8000/o/userinfo/",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if userinfo.status_code != 200:
        return JsonResponse({"error": "Failed to fetch user info"}, status=400)

    username = userinfo.json().get("username")

    user, _ = User.objects.get_or_create(username=username)

    login(request, user)

    return JsonResponse({"status": "ok"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    user_data = {
        "username": request.user.username,
        "id": request.user.id,
        "email": request.user.email,
    }
    
    # Add tenant information if user has a profile
    try:
        profile = UserProfile.objects.select_related('tenant').get(user=request.user)
        user_data["tenant"] = {
            "id": profile.tenant.id,
            "name": profile.tenant.name,
            "slug": profile.tenant.slug,
            "role": profile.role,
        }
    except UserProfile.DoesNotExist:
        user_data["tenant"] = None
    
    return JsonResponse(user_data)


@api_view(["POST"])
@permission_classes([AllowAny])
def logout_view(request):
    logout(request)
    return JsonResponse({"status": "logged out"})

@api_view(["POST"])
@permission_classes([AllowAny])
def login_api(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return JsonResponse({"error": "Missing email or password"}, status=400)

    # If you use email as username:
    user = authenticate(request, username=email, password=password)

    if user is None:
        return JsonResponse({"error": "Invalid credentials"}, status=401)

    login(request, user)
    
    # Get tenant information
    tenant_info = None
    try:
        profile = UserProfile.objects.select_related('tenant').get(user=user)
        tenant_info = {
            "id": profile.tenant.id,
            "name": profile.tenant.name,
            "slug": profile.tenant.slug,
            "role": profile.role,
        }
    except UserProfile.DoesNotExist:
        pass

    return JsonResponse({
        "status": "ok",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        },
        "tenant": tenant_info
    })


@api_view(["POST"])
@permission_classes([AllowAny])
@transaction.atomic
def register(request):
    """Register a new user and create a tenant for them"""
    email = request.data.get("email")
    password = request.data.get("password")
    username = request.data.get("username")
    tenant_name = request.data.get("tenant_name")
    
    if not all([email, password, username, tenant_name]):
        return JsonResponse({
            "error": "Missing required fields: email, password, username, tenant_name"
        }, status=400)
    
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "Username already exists"}, status=400)
    
    if User.objects.filter(email=email).exists():
        return JsonResponse({"error": "Email already exists"}, status=400)
    
    # Create tenant
    tenant_slug = slugify(tenant_name)
    base_slug = tenant_slug
    counter = 1
    while Tenant.objects.filter(slug=tenant_slug).exists():
        tenant_slug = f"{base_slug}-{counter}"
        counter += 1
    
    tenant = Tenant.objects.create(
        name=tenant_name,
        slug=tenant_slug
    )
    
    # Create user
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    
    # Create user profile linking user to tenant
    UserProfile.objects.create(
        user=user,
        tenant=tenant,
        role='owner'  # First user is the owner
    )
    
    # Log the user in
    login(request, user)
    
    return JsonResponse({
        "status": "ok",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        },
        "tenant": {
            "id": tenant.id,
            "name": tenant.name,
            "slug": tenant.slug,
            "role": "owner"
        }
    }, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def tenant_users(request):
    """Get all users in the current tenant"""
    if not hasattr(request, 'tenant') or not request.tenant:
        return JsonResponse({"error": "No tenant associated with user"}, status=400)
    
    profiles = UserProfile.objects.filter(
        tenant=request.tenant
    ).select_related('user')
    
    users = [{
        "id": profile.user.id,
        "username": profile.user.username,
        "email": profile.user.email,
        "role": profile.role,
        "is_active": profile.is_active,
        "created_at": profile.created_at.isoformat(),
    } for profile in profiles]
    
    return JsonResponse({"users": users})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def invite_user(request):
    """Invite a user to the current tenant (admin/owner only)"""
    if not hasattr(request, 'tenant') or not request.tenant:
        return JsonResponse({"error": "No tenant associated with user"}, status=400)
    
    # Check if user is admin or owner
    try:
        user_profile = UserProfile.objects.get(user=request.user, tenant=request.tenant)
        if user_profile.role not in ['admin', 'owner']:
            return JsonResponse({"error": "Only admins and owners can invite users"}, status=403)
    except UserProfile.DoesNotExist:
        return JsonResponse({"error": "User profile not found"}, status=400)
    
    email = request.data.get("email")
    role = request.data.get("role", "member")
    
    if not email:
        return JsonResponse({"error": "Email is required"}, status=400)
    
    if role not in ['admin', 'member']:
        return JsonResponse({"error": "Invalid role. Must be 'admin' or 'member'"}, status=400)
    
    # Check if user exists
    try:
        user = User.objects.get(email=email)
        
        # Check if user is already in this tenant
        if UserProfile.objects.filter(user=user, tenant=request.tenant).exists():
            return JsonResponse({"error": "User already exists in this tenant"}, status=400)
        
        # Add user to tenant
        UserProfile.objects.create(
            user=user,
            tenant=request.tenant,
            role=role
        )
        
        return JsonResponse({
            "status": "ok",
            "message": "User added to tenant",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": role
            }
        })
        
    except User.DoesNotExist:
        # In a real app, you'd send an invitation email here
        return JsonResponse({
            "status": "pending",
            "message": "User not found. In production, an invitation email would be sent."
        }, status=200)

@api_view(["GET"])
@permission_classes([AllowAny])
def get_csrf(request):
    return JsonResponse({"csrfToken": get_token(request)})

@api_view(["POST"])
@permission_classes([AllowAny])
def upload_file(request):
    """
    Upload file endpoint that:
    - Receives a file and appId
    - Detects OS (Windows or Linux)
    - Saves file to appropriate path
    - Runs Python scripts as needed
    - Returns success/error response
    """
    try:
        # Debug logging
        print("="*50)
        print("Upload request received")
        print(f"FILES: {request.FILES}")
        print(f"POST: {request.POST}")
        print(f"data: {request.data if hasattr(request, 'data') else 'N/A'}")
        print("="*50)
        
        # Check if file is in request
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No file provided',
                'debug': {
                    'files_keys': list(request.FILES.keys()),
                    'post_keys': list(request.POST.keys())
                }
            }, status=400)
        
        # Get the uploaded file
        uploaded_file = request.FILES['file']
        
        # Get appId from POST data
        app_id = request.POST.get('appId') or request.data.get('appId')
        if not app_id:
            return JsonResponse({
                'success': False,
                'error': 'No appId provided',
                'debug': {
                    'post_keys': list(request.POST.keys()),
                    'data_keys': list(request.data.keys()) if hasattr(request, 'data') else []
                }
            }, status=400)
        
        # Detect OS
        system = platform.system()
        
        # Determine upload path based on OS
        if system == 'Windows':
            upload_dir = 'c:/aiaptt/upload'
        else:  # Linux and other Unix-like systems
            upload_dir = '/opt/aiaptt/upload'
        
        # Create directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)
        
        # Create full file path
        file_path = os.path.join(upload_dir, uploaded_file.name)
        
        # Save the file
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)
        
        # Initialize response data
        network_scan_results = None
        orchestrator_output = None
        vulnerabilities = []
        errors = []
        
        # Try to run scripts but don't fail upload if scripts fail
        try:
            # Read uploaded file to get CIDR or scanner output
            print("[DEBUG] Reading uploaded file...")
            with open(file_path, 'r') as f:
                file_content = json.load(f)
            
            print(f"[DEBUG] File content keys: {file_content.keys()}")
            
            # 1. Run network scan if CIDR is present
            if 'cidr' in file_content:
                print(f"[DEBUG] CIDR found: {file_content['cidr']}, running network scan...")
                try:
                    from core.utils.network_scan import scan_network_to_graph
                    cidr = file_content['cidr']
                    network_graph = scan_network_to_graph(cidr)
                    network_scan_results = network_graph
                    print("[DEBUG] Network scan completed successfully")
                except Exception as scan_error:
                    print(f"[DEBUG] Network scan error: {scan_error}")
                    errors.append({
                        'source': 'network_scan',
                        'message': str(scan_error),
                        'type': type(scan_error).__name__
                    })
            else:
                print("[DEBUG] No CIDR field found, skipping network scan")
            
            # 2. Run orchestrator to process vulnerabilities
            print("[DEBUG] Starting orchestrator...")
            try:
                utils_dir = Path(__file__).parent / 'utils'
                scanner_output_path = utils_dir / 'scanner_output.json'
                
                # Copy uploaded file to scanner_output.json (orchestrator expects this file)
                print(f"[DEBUG] Copying file to: {scanner_output_path}")
                shutil.copy(file_path, scanner_output_path)
                
                # Get Python executable path
                python_exe = sys.executable
                orchestrator_script = utils_dir / 'orchestrator.py'
                
                print(f"[DEBUG] Running orchestrator: {orchestrator_script}")
                # Run orchestrator script
                result = subprocess.run(
                    [python_exe, str(orchestrator_script)],
                    cwd=str(utils_dir),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
                
                print(f"[DEBUG] Orchestrator return code: {result.returncode}")
                print(f"[DEBUG] Orchestrator stdout length: {len(result.stdout)}")
                print(f"[DEBUG] Orchestrator stderr length: {len(result.stderr)}")
                
                # Capture terminal output for frontend display
                orchestrator_output = result.stdout
                
                if result.stderr:
                    print(f"[DEBUG] Orchestrator stderr (FULL):\n{result.stderr}")
                    errors.append({
                        'source': 'orchestrator',
                        'message': result.stderr
                    })
            except Exception as orch_error:
                print(f"[DEBUG] Orchestrator exception: {orch_error}")
                errors.append({
                    'source': 'orchestrator',
                    'message': str(orch_error),
                    'type': type(orch_error).__name__
                })
            
            # Parse vulnerabilities from uploaded file
            print("[DEBUG] Parsing vulnerabilities...")
            try:
                from core.utils.scanner_parser import parse_scanner_output
                vulnerabilities = parse_scanner_output(file_content)
                print(f"[DEBUG] Found {len(vulnerabilities)} vulnerabilities")
            except Exception as parse_error:
                print(f"[DEBUG] Parser error: {parse_error}")
                errors.append({
                    'source': 'parser',
                    'message': str(parse_error),
                    'type': type(parse_error).__name__
                })
            
        except json.JSONDecodeError as json_err:
            # File is not JSON, still return success for upload but note the error
            errors.append({
                'source': 'file_upload',
                'message': 'Uploaded file is not valid JSON - scripts not executed'
            })
        except Exception as script_error:
            errors.append({
                'source': 'script_execution',
                'message': str(script_error),
                'type': type(script_error).__name__
            })
        
        # Save scan results for later retrieval (even if scripts failed)
        try:
            _save_scan_results(app_id, orchestrator_output, vulnerabilities, network_scan_results)
        except Exception as save_error:
            errors.append({
                'source': 'save_results',
                'message': str(save_error),
                'type': type(save_error).__name__
            })
        
        return JsonResponse({
            'success': True,
            'message': 'File uploaded and processed successfully',
            'data': {
                'filename': uploaded_file.name,
                'appId': app_id,
                'path': file_path,
                'os': system,
                'networkScan': network_scan_results,
                'vulnerabilities': vulnerabilities,
                'orchestratorOutput': orchestrator_output,
                'errors': errors if errors else None
            }
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def _save_scan_results(app_id, orchestrator_output, vulnerabilities, network_scan_results):
    """Helper function to save scan results for an appId"""
    system = platform.system()
    
    # Determine results path based on OS
    if system == 'Windows':
        results_dir = 'c:/aiaptt/results'
    else:
        results_dir = '/opt/aiaptt/results'
    
    os.makedirs(results_dir, exist_ok=True)
    
    results_file = os.path.join(results_dir, f'{app_id}.json')
    
    results_data = {
        'appId': app_id,
        'timestamp': datetime.utcnow().isoformat(),
        'orchestratorOutput': orchestrator_output,
        'vulnerabilities': vulnerabilities,
        'networkScan': network_scan_results
    }
    
    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_scan_results(request, app_id):
    """
    GET endpoint to retrieve scan results by appId
    Returns logs and vulnerabilities in the format expected by frontend
    """
    try:
        system = platform.system()
        
        # Determine results path based on OS
        if system == 'Windows':
            results_dir = 'c:/aiaptt/results'
        else:
            results_dir = '/opt/aiaptt/results'
        
        results_file = os.path.join(results_dir, f'{app_id}.json')
        
        if not os.path.exists(results_file):
            return JsonResponse({
                'error': 'Scan results not found for this application'
            }, status=404)
        
        with open(results_file, 'r') as f:
            results_data = json.load(f)
        
        # Format logs with timestamps
        logs = []
        if results_data.get('orchestratorOutput'):
            # Split orchestrator output into lines and add timestamps
            output_lines = results_data['orchestratorOutput'].split('\n')
            scan_timestamp = results_data.get('timestamp', datetime.utcnow().isoformat())
            
            for line in output_lines:
                if line.strip():  # Skip empty lines
                    logs.append(f"[{scan_timestamp}] {line}")
        
        # Format vulnerabilities
        formatted_vulns = []
        raw_vulns = results_data.get('vulnerabilities', [])
        
        for idx, vuln in enumerate(raw_vulns, start=1):
            formatted_vuln = {
                'id': idx,
                'severity': vuln.get('severity', 'UNKNOWN').upper(),
                'name': vuln.get('finding', 'Unknown Vulnerability'),
                'description': vuln.get('summary', ''),
                'host': vuln.get('host'),
                'port': vuln.get('port'),
                'protocol': vuln.get('protocol'),
                'scanner': vuln.get('scanner')
            }
            
            # Add CVE if available (extract from description or finding name)
            finding_text = vuln.get('finding', '') + ' ' + vuln.get('summary', '')
            if 'CVE-' in finding_text:
                cve_match = re.search(r'CVE-\d{4}-\d{4,7}', finding_text)
                if cve_match:
                    formatted_vuln['cve'] = cve_match.group(0)
            
            formatted_vulns.append(formatted_vuln)
        
        return JsonResponse({
            'logs': logs,
            'vulnerabilities': formatted_vulns,
            'networkScan': results_data.get('networkScan'),
            'timestamp': results_data.get('timestamp')
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
    
@require_http_methods(["POST"])
def start_scan(request):
    try:
        # Parse JSON body
        data = json.loads(request.body)
        target_url = data.get('url')
        
        if not target_url:
            return JsonResponse({'message': 'URL is required'}, status=400)
        
        print(f"[+] Starting scan for URL: {target_url}")
        
        # Get paths
        utils_dir = Path(__file__).parent / 'utils'
        orchestrator_script = utils_dir / 'orchestrator.py'
        
        # Get Python executable
        python_exe = sys.executable
        
        print(f"[+] Running orchestrator: {orchestrator_script}")
        
        # Run orchestrator.py script
        result = subprocess.run(
            [python_exe, str(orchestrator_script)],
            cwd=str(utils_dir),
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        
        print(f"[+] Orchestrator completed with return code: {result.returncode}")
        
        if result.stdout:
            print(f"[+] Output:\n{result.stdout}")
        
        if result.stderr:
            print(f"[!] Errors:\n{result.stderr}")
        
        # Get vulnerabilities list from orchestrator
        from core.utils.orchestrator import get_vulnerabilities_list
        vulnerabilities = get_vulnerabilities_list()
        
        # Return success response
        return JsonResponse({
            'message': 'Scan completed successfully',
            'url': target_url,
            'vulnerabilities': vulnerabilities,
            'output': result.stdout,
            'errors': result.stderr if result.stderr else None,
            'return_code': result.returncode
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({'message': 'Invalid JSON'}, status=400)
    except subprocess.TimeoutExpired:
        return JsonResponse({'message': 'Scan timeout - process took longer than 5 minutes'}, status=500)
    except Exception as e:
        return JsonResponse({'message': str(e)}, status=500)