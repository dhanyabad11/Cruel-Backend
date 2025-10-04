-- ===================================
-- QUICK DATABASE SETUP FOR SUPABASE
-- Copy and paste this into Supabase SQL Editor
-- ===================================

-- Create the deadlines table
CREATE TABLE public.deadlines (
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

-- Add index for user lookups
CREATE INDEX idx_deadlines_user_id ON public.deadlines(user_id);

-- ===================================
-- DONE! Now try your API call again
-- ===================================