-- SQL Script to add missing columns to existing application_configuration table
-- Run this if you already have the application_configuration table created

-- Add description column
ALTER TABLE application_configuration 
ADD COLUMN IF NOT EXISTS description TEXT;

-- Add target_port column with default value
ALTER TABLE application_configuration 
ADD COLUMN IF NOT EXISTS target_port INTEGER DEFAULT 80;

-- Add base_url column
ALTER TABLE application_configuration 
ADD COLUMN IF NOT EXISTS base_url VARCHAR(255);

-- Verify columns were added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'application_configuration'
  AND column_name IN ('description', 'target_port', 'base_url')
ORDER BY column_name;
