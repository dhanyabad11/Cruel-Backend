-- Portal Scraping Database Schema for Supabase
-- Run this in your Supabase SQL Editor

-- 1. Drop existing table if you want a fresh start (CAREFUL: THIS DELETES DATA!)
-- Uncomment the next line if you want to start fresh:
-- DROP TABLE IF EXISTS portals CASCADE;

-- 2. Create portals table
CREATE TABLE IF NOT EXISTS portals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    portal_type VARCHAR(50) NOT NULL,
    url VARCHAR(500) NOT NULL,
    credentials JSONB,
    config JSONB,
    is_active BOOLEAN DEFAULT true,
    last_sync TIMESTAMP,
    sync_frequency VARCHAR(50) DEFAULT 'daily',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. If table already exists, add missing columns
ALTER TABLE portals ADD COLUMN IF NOT EXISTS portal_type VARCHAR(50) NOT NULL DEFAULT 'custom';
ALTER TABLE portals ADD COLUMN IF NOT EXISTS url VARCHAR(500);
ALTER TABLE portals ADD COLUMN IF NOT EXISTS credentials JSONB;
ALTER TABLE portals ADD COLUMN IF NOT EXISTS config JSONB;
ALTER TABLE portals ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;
ALTER TABLE portals ADD COLUMN IF NOT EXISTS last_sync TIMESTAMP;
ALTER TABLE portals ADD COLUMN IF NOT EXISTS sync_frequency VARCHAR(50) DEFAULT 'daily';

-- 4. Drop and recreate portal_id column with correct type
ALTER TABLE deadlines DROP COLUMN IF EXISTS portal_id CASCADE;
ALTER TABLE deadlines ADD COLUMN portal_id UUID;

-- 5. Add other portal-related columns to deadlines table
ALTER TABLE deadlines ADD COLUMN IF NOT EXISTS portal_task_id VARCHAR(255);
ALTER TABLE deadlines ADD COLUMN IF NOT EXISTS portal_url VARCHAR(500);
ALTER TABLE deadlines ADD COLUMN IF NOT EXISTS tags TEXT;
ALTER TABLE deadlines ADD COLUMN IF NOT EXISTS estimated_hours NUMERIC(5,2);

-- 6. Add foreign key constraint
ALTER TABLE deadlines ADD CONSTRAINT deadlines_portal_id_fkey 
    FOREIGN KEY (portal_id) REFERENCES portals(id) ON DELETE SET NULL;

-- 7. Create indexes for better performance
DO $$ 
BEGIN
    -- Only create indexes if table has the columns
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='portals' AND column_name='user_id') THEN
        CREATE INDEX IF NOT EXISTS idx_portals_user_id ON portals(user_id);
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='portals' AND column_name='portal_type') THEN
        CREATE INDEX IF NOT EXISTS idx_portals_type ON portals(portal_type);
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='portals' AND column_name='is_active') THEN
        CREATE INDEX IF NOT EXISTS idx_portals_active ON portals(is_active);
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='deadlines' AND column_name='portal_id') THEN
        CREATE INDEX IF NOT EXISTS idx_deadlines_portal_id ON deadlines(portal_id);
        CREATE INDEX IF NOT EXISTS idx_deadlines_portal_task ON deadlines(portal_id, portal_task_id);
    END IF;
END $$;

-- 8. Enable Row Level Security
ALTER TABLE portals ENABLE ROW LEVEL SECURITY;

-- 9. Create RLS Policies for portals table (drop first to avoid conflicts)
DROP POLICY IF EXISTS "Users can view own portals" ON portals;
DROP POLICY IF EXISTS "Users can create own portals" ON portals;
DROP POLICY IF EXISTS "Users can update own portals" ON portals;
DROP POLICY IF EXISTS "Users can delete own portals" ON portals;

CREATE POLICY "Users can view own portals" 
ON portals FOR SELECT 
USING (user_id = auth.uid());

CREATE POLICY "Users can create own portals" 
ON portals FOR INSERT 
WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own portals" 
ON portals FOR UPDATE 
USING (user_id = auth.uid());

CREATE POLICY "Users can delete own portals" 
ON portals FOR DELETE 
USING (user_id = auth.uid());

-- 10. Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_portals_updated_at ON portals;
CREATE TRIGGER update_portals_updated_at 
    BEFORE UPDATE ON portals 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 11. Create a view for portal statistics
CREATE OR REPLACE VIEW portal_stats AS
SELECT 
    p.id as portal_id,
    p.user_id,
    p.name as portal_name,
    p.portal_type,
    p.last_sync,
    COUNT(d.id) as total_deadlines,
    COUNT(CASE WHEN d.status = 'pending' THEN 1 END) as pending_deadlines,
    COUNT(CASE WHEN d.status = 'completed' THEN 1 END) as completed_deadlines
FROM portals p
LEFT JOIN deadlines d ON p.id = d.portal_id
GROUP BY p.id, p.user_id, p.name, p.portal_type, p.last_sync;

-- Grant access to the view
GRANT SELECT ON portal_stats TO authenticated;

-- 12. Add helpful comment
COMMENT ON COLUMN portals.portal_type IS 'Available types: github, jira, trello, canvas, blackboard, moodle, custom';

-- SUCCESS! Portal scraping database is ready.
-- Next: Test with backend and add your first portal!
