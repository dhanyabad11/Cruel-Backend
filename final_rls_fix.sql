-- ===================================
-- FINAL WORKING RLS POLICY FIX
-- Drops all existing policies first
-- ===================================

-- Drop ALL existing policies (be thorough)
DROP POLICY IF EXISTS "Users can only access their own deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Users can access their own deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Allow users to manage their deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Users can manage their deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Authenticated users can manage their deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Users can view their own deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Users can create their own deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Users can update their own deadlines" ON public.deadlines;
DROP POLICY IF EXISTS "Users can delete their own deadlines" ON public.deadlines;

-- Enable RLS
ALTER TABLE public.deadlines ENABLE ROW LEVEL SECURITY;

-- Create WORKING policies using JWT
CREATE POLICY "users_select_own_deadlines" ON public.deadlines
    FOR SELECT USING (auth.jwt() ->> 'sub' = user_id::text);

CREATE POLICY "users_insert_own_deadlines" ON public.deadlines
    FOR INSERT WITH CHECK (auth.jwt() ->> 'sub' = user_id::text);

CREATE POLICY "users_update_own_deadlines" ON public.deadlines
    FOR UPDATE USING (auth.jwt() ->> 'sub' = user_id::text) WITH CHECK (auth.jwt() ->> 'sub' = user_id::text);

CREATE POLICY "users_delete_own_deadlines" ON public.deadlines
    FOR DELETE USING (auth.jwt() ->> 'sub' = user_id::text);

-- ===================================
-- ✅ RUN THIS - Should work now!
-- ===================================