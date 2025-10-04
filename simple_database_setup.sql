-- ===================================
-- SIMPLE DATABASE SETUP FOR SUPABASE
-- Run this in Supabase SQL Editor
-- ===================================

-- Create deadlines table without complex constraints first
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

-- Add basic index for user lookups
CREATE INDEX IF NOT EXISTS idx_deadlines_user_id ON public.deadlines(user_id);

-- ===================================
-- SIMPLE SETUP COMPLETE!
-- Try this first, then we can add RLS later
-- ===================================