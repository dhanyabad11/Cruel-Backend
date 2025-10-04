-- ===================================
-- WORKING RLS POLICY FOR DEADLINES
-- This policy properly checks user_id
-- ===================================

-- Enable RLS
ALTER TABLE public.deadlines ENABLE ROW LEVEL SECURITY;

-- Drop any existing policies
DROP POLICY IF EXISTS "Users can manage their deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Authenticated users can manage their deadlines" ON public.deadlines;

-- Create policies that work with Supabase Auth
-- Use auth.jwt() to get the user ID from the JWT token
CREATE POLICY "Users can view their own deadlines" ON public.deadlines
    FOR SELECT USING (auth.jwt() ->> 'sub' = user_id::text);

CREATE POLICY "Users can insert their own deadlines" ON public.deadlines
    FOR INSERT WITH CHECK (auth.jwt() ->> 'sub' = user_id::text);

CREATE POLICY "Users can update their own deadlines" ON public.deadlines
    FOR UPDATE USING (auth.jwt() ->> 'sub' = user_id::text) WITH CHECK (auth.jwt() ->> 'sub' = user_id::text);

CREATE POLICY "Users can delete their own deadlines" ON public.deadlines
    FOR DELETE USING (auth.jwt() ->> 'sub' = user_id::text);

-- ===================================
-- ✅ THIS SHOULD WORK WITH JWT!
-- Uses auth.jwt() instead of auth.uid()
-- ===================================