-- ===================================
-- SIMPLE WORKING RLS POLICY
-- Uses auth.uid() with proper checks
-- ===================================

-- Drop all policies
DROP POLICY IF EXISTS "users_select_own_deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "users_insert_own_deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "users_update_own_deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "users_delete_own_deadlines" ON public.deadlines;

-- Enable RLS
ALTER TABLE public.deadlines ENABLE ROW LEVEL SECURITY;

-- Create simple working policies
-- Allow authenticated users to manage their data
-- The application ensures user_id is set correctly
CREATE POLICY "deadline_access_policy" ON public.deadlines
    FOR ALL USING (auth.role() = 'authenticated' AND auth.uid()::text = user_id::text)
    WITH CHECK (auth.role() = 'authenticated' AND auth.uid()::text = user_id::text);

-- ===================================
-- ✅ THIS SHOULD WORK!
-- Uses auth.uid() with auth.role() check
-- ===================================