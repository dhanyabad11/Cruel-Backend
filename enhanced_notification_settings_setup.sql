-- ===================================
-- ENHANCED NOTIFICATION SETTINGS WITH MULTIPLE REMINDERS
-- Run this in Supabase SQL Editor
-- ===================================

-- Step 1: Create notification_reminders table for multiple reminder configurations
CREATE TABLE IF NOT EXISTS public.notification_reminders (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    reminder_time TEXT NOT NULL, -- '1_hour', '6_hours', '1_day', '3_days', '1_week'
    email_enabled BOOLEAN DEFAULT false,
    sms_enabled BOOLEAN DEFAULT false,
    whatsapp_enabled BOOLEAN DEFAULT false,
    push_enabled BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE,
    UNIQUE(user_id, reminder_time)
);

-- Step 2: Enable RLS
ALTER TABLE public.notification_reminders ENABLE ROW LEVEL SECURITY;

-- Step 3: Create RLS policies
CREATE POLICY "Users can view their own notification reminders" ON public.notification_reminders
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own notification reminders" ON public.notification_reminders
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own notification reminders" ON public.notification_reminders
    FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own notification reminders" ON public.notification_reminders
    FOR DELETE USING (auth.uid() = user_id);

-- Step 4: Create indexes
CREATE INDEX IF NOT EXISTS idx_notification_reminders_user_id ON public.notification_reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_reminders_time ON public.notification_reminders(reminder_time);

-- Step 5: Update notification_settings table to remove old reminder_frequency column
ALTER TABLE public.notification_settings DROP COLUMN IF EXISTS reminder_frequency;

-- Step 6: Create function to create default reminder settings for new users
CREATE OR REPLACE FUNCTION public.create_default_reminders_for_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Create default reminder: 1 day before via email and push
    INSERT INTO public.notification_reminders (user_id, reminder_time, email_enabled, push_enabled)
    VALUES (NEW.user_id, '1_day', true, true)
    ON CONFLICT (user_id, reminder_time) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 7: Create trigger to auto-create default reminders when notification settings are created
DROP TRIGGER IF EXISTS on_notification_settings_created ON public.notification_settings;
CREATE TRIGGER on_notification_settings_created
    AFTER INSERT ON public.notification_settings
    FOR EACH ROW EXECUTE PROCEDURE public.create_default_reminders_for_user();

-- ===================================
-- ✅ ENHANCED NOTIFICATION REMINDERS SETUP COMPLETE
-- ===================================