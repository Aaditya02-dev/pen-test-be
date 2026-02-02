-- Migration script to add job_id column to track scan relationships
-- Run this script to add job_id foreign key to baseline_scans, network_scans, and vulnerabilities tables

-- Add job_id to baseline_scans
ALTER TABLE baseline_scans 
ADD COLUMN IF NOT EXISTS job_id VARCHAR(36);

-- Add job_id to network_scans
ALTER TABLE network_scans 
ADD COLUMN IF NOT EXISTS job_id VARCHAR(36);

-- Add job_id to vulnerabilities
ALTER TABLE vulnerabilities 
ADD COLUMN IF NOT EXISTS job_id VARCHAR(36);

-- Optional: Add foreign key constraints (uncomment if you want strict referential integrity)
-- ALTER TABLE baseline_scans ADD CONSTRAINT fk_baseline_scans_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;
-- ALTER TABLE network_scans ADD CONSTRAINT fk_network_scans_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;
-- ALTER TABLE vulnerabilities ADD CONSTRAINT fk_vulnerabilities_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE;

-- Optional: Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_baseline_scans_job_id ON baseline_scans(job_id);
CREATE INDEX IF NOT EXISTS idx_network_scans_job_id ON network_scans(job_id);
CREATE INDEX IF NOT EXISTS idx_vulnerabilities_job_id ON vulnerabilities(job_id);

-- Verify the columns were added
SELECT 
    'baseline_scans' as table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'baseline_scans' AND column_name = 'job_id'
UNION ALL
SELECT 
    'network_scans' as table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'network_scans' AND column_name = 'job_id'
UNION ALL
SELECT 
    'vulnerabilities' as table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'vulnerabilities' AND column_name = 'job_id';
