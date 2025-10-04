-- ===================================
-- SIMPLIFIED RLS POLICY FIX
-- Try this if the complex policies don't work
-- ===================================

-- Drop all existing policies
DROP POLICY IF EXISTS "Users can view their own deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Users can create their own deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Users can update their own deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Users can delete their own deadlines" ON public.deadlines;

-- Create a single policy for all operations
CREATE POLICY "Users can manage their deadlines" ON public.deadlines
    FOR ALL USING (auth.uid() IS NOT NULL AND auth.uid()::text = user_id::text)
    WITH CHECK (auth.uid() IS NOT NULL AND auth.uid()::text = user_id::text);

-- ===================================
-- TEST THIS SIMPLER APPROACH
-- ===================================