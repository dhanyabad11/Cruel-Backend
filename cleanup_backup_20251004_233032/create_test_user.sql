-- TEMPORARY: Create a real user in Supabase for the mock UUID
-- This allows smooth transition from development to production

-- Insert the test user directly into auth.users (admin operation)
-- Note: This requires service role key, not anon key

INSERT INTO auth.users (
    instance_id,
    id,
    aud,
    role,
    email,
    encrypted_password,
    email_confirmed_at,
    invited_at,
    confirmation_token,
    confirmation_sent_at,
    recovery_token,
    recovery_sent_at,
    email_change_token_new,
    email_change,
    email_change_sent_at,
    last_sign_in_at,
    raw_app_meta_data,
    raw_user_meta_data,
    is_super_admin,
    created_at,
    updated_at,
    phone,
    phone_confirmed_at,
    phone_change,
    phone_change_token,
    phone_change_sent_at,
    email_change_token_current,
    email_change_confirm_status,
    banned_until,
    reauthentication_token,
    reauthentication_sent_at,
    is_sso_user
) VALUES (
    '00000000-0000-0000-0000-000000000000',
    '62fd877b-9515-411a-bbb7-6a47d021d970',
    'authenticated',
    'authenticated',
    'testuser@gmail.com',
    '$2a$10$0123456789abcdef0123456789abcdef0123456789abcdef01', -- placeholder hash
    NOW(),
    NULL,
    '',
    NULL,
    '',
    NULL,
    '',
    '',
    NULL,
    NOW(),
    '{"provider": "email", "providers": ["email"]}',
    '{"full_name": "Test User", "email_verified": true}',
    FALSE,
    NOW(),
    NOW(),
    NULL,
    NULL,
    '',
    '',
    NULL,
    '',
    0,
    NULL,
    '',
    NULL,
    FALSE
) ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    updated_at = NOW();

-- Now insert some test deadlines for this user
INSERT INTO public.deadlines (user_id, title, description, due_date, priority, status) VALUES
('62fd877b-9515-411a-bbb7-6a47d021d970', 'Complete Project Report', 'Finish the quarterly analysis report', '2025-10-05 17:00:00+00', 'high', 'pending'),
('62fd877b-9515-411a-bbb7-6a47d021d970', 'Team Meeting Preparation', 'Prepare slides for the upcoming team meeting', '2025-10-02 09:00:00+00', 'medium', 'pending'),
('62fd877b-9515-411a-bbb7-6a47d021d970', 'Code Review', 'Review pull requests from team members', '2025-10-01 15:00:00+00', 'urgent', 'pending')
ON CONFLICT DO NOTHING;

-- Success message
SELECT 'Test user and deadlines created successfully' as message;