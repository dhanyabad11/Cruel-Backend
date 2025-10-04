-- ===================================
-- COMPREHENSIVE RLS FIX FOR DEADLINES TABLE
-- This maintains security while allowing all operations
-- ===================================

-- Drop existing policies
DROP POLICY IF EXISTS "Users can only access their own deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Users can access their own deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Allow users to manage their deadlines" ON public.deadlines;

-- Create separate policies for different operations
-- SELECT policy: Users can read their own deadlines
CREATE POLICY "Users can view their own deadlines" ON public.deadlines
    FOR SELECT USING (auth.uid()::text = user_id::text);

-- INSERT policy: Users can create deadlines for themselves
CREATE POLICY "Users can create their own deadlines" ON public.deadlines
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

-- UPDATE policy: Users can update their own deadlines
CREATE POLICY "Users can update their own deadlines" ON public.deadlines
    FOR UPDATE USING (auth.uid()::text = user_id::text) WITH CHECK (auth.uid()::text = user_id::text);

-- DELETE policy: Users can delete their own deadlines
CREATE POLICY "Users can delete their own deadlines" ON public.deadlines
    FOR DELETE USING (auth.uid()::text = user_id::text);

-- ===================================
-- SECURITY MAINTAINED - ALL OPERATIONS WORK
-- ===================================