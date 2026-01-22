import subprocess
import sys

def run_script(script_path):
    """
    Execute a Python script and return its output.
    """
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "ERROR: Script execution timed out"
    except Exception as e:
        return f"ERROR: {str(e)}"
