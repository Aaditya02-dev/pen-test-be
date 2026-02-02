-- SQL Script to add UUID field to existing application_configuration table
-- Run this if you already have the application_configuration table created

-- Add app_uuid column with auto-generated UUIDs
ALTER TABLE application_configuration 
ADD COLUMN IF NOT EXISTS app_uuid UUID UNIQUE NOT NULL DEFAULT gen_random_uuid();

-- Create index for faster UUID lookups
CREATE INDEX IF NOT EXISTS idx_app_config_uuid ON application_configuration(app_uuid);

-- Verify column was added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'application_configuration'
  AND column_name = 'app_uuid';
