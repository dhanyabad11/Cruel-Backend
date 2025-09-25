-- ===================================
-- AI CRUEL - PRODUCTION DATABASE SETUP  
-- Run this in Supabase SQL Editor
-- ===================================

-- Enable Row Level Security
ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;

-- Create deadlines table
CREATE TABLE IF NOT EXISTS public.deadlines (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    due_date TIMESTAMPTZ NOT NULL,
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'overdue')),
    portal_source TEXT,
    portal_id BIGINT,
    original_message TEXT,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create portals table
CREATE TABLE IF NOT EXISTS public.portals (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    portal_type TEXT NOT NULL CHECK (portal_type IN ('github', 'jira', 'trello', 'whatsapp', 'manual')),
    url TEXT,
    credentials JSONB,
    config JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    last_sync TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create notifications table
CREATE TABLE IF NOT EXISTS public.notifications (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    deadline_id BIGINT REFERENCES public.deadlines(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('reminder', 'overdue', 'summary')),
    message TEXT NOT NULL,
    sent_at TIMESTAMPTZ,
    scheduled_for TIMESTAMPTZ,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'failed')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create user profiles table (extended user info)
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    university TEXT,
    year_of_study INTEGER,
    major TEXT,
    timezone TEXT DEFAULT 'UTC',
    notification_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security for all tables
ALTER TABLE public.deadlines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (users can only see their own data)
CREATE POLICY "Users can only see their own deadlines" ON public.deadlines
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can only see their own portals" ON public.portals
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can only see their own notifications" ON public.notifications
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can only see their own profile" ON public.user_profiles
    FOR ALL USING (auth.uid() = id);

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

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===================================
-- DATABASE SETUP COMPLETE! 
-- Your AI Cruel backend is now ready
-- ===================================