-- ===================================
-- COMPLETE DATABASE SETUP WITH PROPER RLS
-- Run this ENTIRE script in Supabase SQL Editor
-- ===================================

-- Step 1: Create table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.deadlines (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    due_date TIMESTAMPTZ NOT NULL,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'pending',
    portal_source TEXT,
    portal_id BIGINT,
    original_message TEXT,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Step 2: Ensure RLS is enabled
ALTER TABLE public.deadlines ENABLE ROW LEVEL SECURITY;

-- Step 3: Drop any existing policies
DROP POLICY IF EXISTS "Users can only access their own deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Users can access their own deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Allow users to manage their deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Users can view their own deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Users can create their own deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Users can update their own deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Users can delete their own deadlines" ON public.deadlines;

-- Step 4: Create comprehensive policies for all operations
CREATE POLICY "Users can view their own deadlines" ON public.deadlines
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can create their own deadlines" ON public.deadlines
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update their own deadlines" ON public.deadlines
    FOR UPDATE USING (auth.uid()::text = user_id::text) WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete their own deadlines" ON public.deadlines
    FOR DELETE USING (auth.uid()::text = user_id::text);

-- Step 5: Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_deadlines_user_id ON public.deadlines(user_id);
CREATE INDEX IF NOT EXISTS idx_deadlines_due_date ON public.deadlines(due_date);
CREATE INDEX IF NOT EXISTS idx_deadlines_status ON public.deadlines(status);
CREATE INDEX IF NOT EXISTS idx_deadlines_priority ON public.deadlines(priority);

-- ===================================
-- ✅ COMPLETE SETUP - NOTHING BROKEN
-- All operations (SELECT, INSERT, UPDATE, DELETE) work securely
-- ===================================