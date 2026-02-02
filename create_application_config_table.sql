-- SQL Script to create application configuration table
-- Run this in your PostgreSQL database

CREATE TABLE IF NOT EXISTS application_configuration (
    id SERIAL PRIMARY KEY,
    app_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    
    -- Application Details
    application_name VARCHAR(255) NOT NULL,
    description TEXT,
    target_host VARCHAR(255) NOT NULL,
    target_port INTEGER DEFAULT 80,
    base_url VARCHAR(255),
    environment VARCHAR(50) NOT NULL,
    baseline_ttl INTEGER NOT NULL,
    enable_baseline_scan BOOLEAN NOT NULL,
    baseline_start_date TIMESTAMP WITH TIME ZONE,
    
    -- Scan Configuration
    scan_scope VARCHAR(50) NOT NULL,
    selected_pages_to_scan TEXT,  -- Stores newline-separated pages when scan_scope = 'selected_pages'
    paths_to_exclude TEXT,
    
    -- Network Scan Settings
    network_cidr VARCHAR(50),
    allowed_ports VARCHAR(255),
    
    -- Audit Fields
    created_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    updated_by INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
    
    -- Tenant association (if using multi-tenancy)
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Additional metadata
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    CONSTRAINT unique_app_per_tenant UNIQUE (application_name, tenant_id)
);

-- Create index for faster queries
CREATE INDEX idx_app_config_tenant ON application_configuration(tenant_id);
CREATE INDEX idx_app_config_active ON application_configuration(is_active);
CREATE INDEX idx_app_config_environment ON application_configuration(environment);

-- Create trigger to automatically update the updated_date field
CREATE OR REPLACE FUNCTION update_updated_date_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_date = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_application_configuration_updated_date
    BEFORE UPDATE ON application_configuration
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_date_column();

COMMENT ON TABLE application_configuration IS 'Stores configuration for applications to be scanned for vulnerabilities';
