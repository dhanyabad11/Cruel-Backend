-- ===================================
-- COMPLETE NOTIFICATION DATABASE SETUP
-- Run this ENTIRE script in Supabase SQL Editor
-- ===================================

-- Step 1: Create notification_settings table (stores contact info)
CREATE TABLE IF NOT EXISTS public.notification_settings (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL UNIQUE,
    email TEXT,                    -- 📧 Email address for notifications
    phone_number TEXT,             -- 📱 Phone number for SMS (+91XXXXXXXXXX)
    whatsapp_number TEXT,          -- 💬 WhatsApp number (+91XXXXXXXXXX) 
    email_enabled BOOLEAN DEFAULT true,
    sms_enabled BOOLEAN DEFAULT false,
    whatsapp_enabled BOOLEAN DEFAULT false,
    push_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

-- Step 2: Create notification_reminders table (stores multiple reminder schedules)
CREATE TABLE IF NOT EXISTS public.notification_reminders (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    reminder_time TEXT NOT NULL,   -- '1_hour', '6_hours', '1_day', '3_days', '1_week'
    email_enabled BOOLEAN DEFAULT false,
    sms_enabled BOOLEAN DEFAULT false,
    whatsapp_enabled BOOLEAN DEFAULT false,
    push_enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE,
    UNIQUE(user_id, reminder_time)
);

-- Step 3: Enable RLS on both tables
ALTER TABLE public.notification_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_reminders ENABLE ROW LEVEL SECURITY;

-- Step 4: Create RLS policies for notification_settings
CREATE POLICY "Users can view their own notification settings" ON public.notification_settings
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own notification settings" ON public.notification_settings
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own notification settings" ON public.notification_settings
    FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own notification settings" ON public.notification_settings
    FOR DELETE USING (auth.uid() = user_id);

-- Step 5: Create RLS policies for notification_reminders
CREATE POLICY "Users can view their own notification reminders" ON public.notification_reminders
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own notification reminders" ON public.notification_reminders
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own notification reminders" ON public.notification_reminders
    FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own notification reminders" ON public.notification_reminders
    FOR DELETE USING (auth.uid() = user_id);

-- Step 6: Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_notification_settings_user_id ON public.notification_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_reminders_user_id ON public.notification_reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_reminders_time ON public.notification_reminders(reminder_time);

-- Step 7: Create function to auto-create notification settings for new users
CREATE OR REPLACE FUNCTION public.create_notification_settings_for_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Create default notification settings with user's email
    INSERT INTO public.notification_settings (user_id, email, email_enabled, push_enabled)
    VALUES (NEW.id, NEW.email, true, true)
    ON CONFLICT (user_id) DO UPDATE SET
        email = EXCLUDED.email,
        updated_at = NOW();
    
    -- Create default reminder: 1 day before via email and push
    INSERT INTO public.notification_reminders (user_id, reminder_time, email_enabled, push_enabled)
    VALUES (NEW.id, '1_day', true, true)
    ON CONFLICT (user_id, reminder_time) DO NOTHING;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 8: Create trigger to auto-create settings when user signs up
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE PROCEDURE public.create_notification_settings_for_user();

-- ===================================
-- ✅ DATABASE SETUP COMPLETE
-- Tables created:
-- 1. notification_settings (stores email, phone_number, whatsapp_number)
-- 2. notification_reminders (stores multiple reminder configurations)
-- Both tables have RLS enabled for security
-- ===================================