# 🚀 **Supabase Setup Guide - FREE with GitHub Student Pack**

## Step 1: Create Supabase Account

1. Go to **https://supabase.com**
2. Click **"Start your project"**
3. Sign up with your **GitHub account** (uses Student Pack benefits)
4. Verify your email if prompted

## Step 2: Create New Project

1. Click **"New Project"**
2. Choose your organization (usually your GitHub username)
3. Fill in project details:

    - **Name**: `ai-cruel-production`
    - **Database Password**: Generate a strong password (save it!)
    - **Region**: Choose closest to your location
    - **Pricing Plan**: **Free** (perfect for students)

4. Click **"Create new project"**
5. Wait 2-3 minutes for setup to complete

## Step 3: Get Your API Keys

1. In your Supabase dashboard, go to **Settings** → **API**
2. Copy these values:

```bash
# Project URL
SUPABASE_URL=https://your-project-id.supabase.co

# Public anon key (safe to use in frontend)
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Service role key (keep secret, server-side only)
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Step 4: Setup Database

1. Go to **Table Editor** in Supabase dashboard
2. The authentication tables are automatically created
3. We'll create our custom tables next

### Create Tables with SQL:

Go to **SQL Editor** and run this:

```sql
-- Enable Row Level Security
ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;

-- Create deadlines table
CREATE TABLE public.deadlines (
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
CREATE TABLE public.portals (
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
CREATE TABLE public.notifications (
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
CREATE TABLE public.user_profiles (
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
```

## Step 5: Configure Your App

1. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

2. Edit `.env` and add your Supabase credentials:

```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here
DATABASE_URL=postgresql://postgres:your-password@db.supabase.co:5432/postgres
```

## Step 6: Test the Setup

```bash
# Install new dependencies
pip install supabase

# Test the connection
python -c "
from app.supabase_client import get_supabase
client = get_supabase()
print('✅ Supabase connection successful!')
print(f'URL: {client.url}')
"
```

## Step 7: Enable Authentication

1. In Supabase dashboard, go to **Authentication** → **Settings**
2. Configure:
    - **Site URL**: `http://localhost:3000` (for development)
    - **Redirect URLs**: `http://localhost:3000/auth/callback`
3. Enable **Email** provider
4. Optionally enable **Social providers** (Google, GitHub, etc.)

## 🎉 **You're Ready!**

Your free Supabase setup includes:

-   ✅ **PostgreSQL Database** (50GB free)
-   ✅ **User Authentication** (unlimited users)
-   ✅ **Row Level Security** (automatic data isolation)
-   ✅ **Real-time subscriptions** (for live updates)
-   ✅ **File storage** (1GB free)
-   ✅ **Edge functions** (for serverless operations)

## 🔒 **Security Features**

-   **Row Level Security**: Users can only see their own data
-   **JWT Authentication**: Secure token-based auth
-   **Email verification**: Prevents fake accounts
-   **Rate limiting**: Prevents abuse
-   **Encrypted passwords**: Industry-standard security

## 📊 **Free Tier Limits** (More than enough for students!)

-   **Database**: 50GB storage, 100MB/day bandwidth
-   **Auth**: Unlimited users
-   **Storage**: 1GB files
-   **Edge Functions**: 500K invocations/month
-   **Realtime**: 2 concurrent connections

Perfect for a student project with hundreds of users! 🚀
