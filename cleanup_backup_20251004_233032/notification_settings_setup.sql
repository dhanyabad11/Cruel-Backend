-- ===================================
-- NOTIFICATION SETTINGS TABLE SETUP
-- Run this in Supabase SQL Editor
-- ===================================

-- Step 1: Create notification_settings table
CREATE TABLE IF NOT EXISTS public.notification_settings (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE,
    email TEXT,
    phone_number TEXT,
    whatsapp_number TEXT,
    email_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,
    whatsapp_enabled BOOLEAN DEFAULT false,
    push_enabled BOOLEAN DEFAULT true,
    reminder_frequency TEXT DEFAULT '1_day', -- '1_hour', '6_hours', '1_day', '3_days', '1_week'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Step 2: Enable RLS
ALTER TABLE public.notification_settings ENABLE ROW LEVEL SECURITY;

-- Step 3: Create RLS policies
CREATE POLICY "Users can view their own notification settings" ON public.notification_settings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own notification settings" ON public.notification_settings
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own notification settings" ON public.notification_settings
    FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own notification settings" ON public.notification_settings
    FOR DELETE USING (auth.uid() = user_id);

-- Step 4: Create indexes
CREATE INDEX IF NOT EXISTS idx_notification_settings_user_id ON public.notification_settings(user_id);

-- Step 5: Create function to auto-create notification settings for new users
CREATE OR REPLACE FUNCTION public.create_notification_settings_for_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.notification_settings (user_id, email)
    VALUES (NEW.id, NEW.email)
    ON CONFLICT (user_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 6: Create trigger to auto-create settings when user signs up
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE PROCEDURE public.create_notification_settings_for_user();

-- ===================================
-- ✅ NOTIFICATION SETTINGS SETUP COMPLETE
-- ===================================