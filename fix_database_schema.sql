-- ===================================
-- PRODUCTION-LEVEL DATABASE SCHEMA
-- Run this in Supabase SQL Editor for REAL production deployment
-- ===================================

-- First, drop the existing deadlines table if it exists with wrong schema
DROP TABLE IF EXISTS public.deadlines CASCADE;

-- Create PRODUCTION deadlines table with proper foreign key constraints
CREATE TABLE public.deadlines (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    due_date TIMESTAMPTZ NOT NULL,
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent', 'critical')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'overdue')),
    portal_source TEXT,
    portal_id BIGINT,
    original_message TEXT,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security for deadlines table
ALTER TABLE public.deadlines ENABLE ROW LEVEL SECURITY;

-- Create RLS policy (users can only see their own deadlines)
CREATE POLICY "Users can only access their own deadlines" ON public.deadlines
    FOR ALL USING (auth.uid() = user_id);

-- Create updated_at trigger for deadlines
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_deadlines_updated_at BEFORE UPDATE ON public.deadlines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for better performance
CREATE INDEX idx_deadlines_user_id ON public.deadlines(user_id);
CREATE INDEX idx_deadlines_due_date ON public.deadlines(due_date);
CREATE INDEX idx_deadlines_status ON public.deadlines(status);
CREATE INDEX idx_deadlines_priority ON public.deadlines(priority);

-- ===================================
-- PRODUCTION DATABASE READY!
-- 
-- USERS MUST SIGN UP THROUGH YOUR APP TO CREATE DEADLINES
-- No test data - this is REAL production-level setup
-- ===================================