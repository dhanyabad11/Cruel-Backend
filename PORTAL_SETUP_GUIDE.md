# 🚀 Portal Scraping Setup Guide

## Quick Setup (15 minutes)

### Step 1: Database Setup (5 min)

1. **Go to your Supabase Dashboard**: https://supabase.com/dashboard

2. **Select your project**

3. **Go to SQL Editor** (left sidebar)

4. **Create a new query** and paste the contents of `portal_schema.sql`

5. **Run the query** (Cmd+Enter or click "Run")

6. **Verify tables created**:
    - Go to "Table Editor"
    - You should see `portals` table
    - Check `deadlines` table has new columns: `portal_id`, `portal_task_id`, `portal_url`

---

### Step 2: Get GitHub Token (3 min)

1. **Go to**: https://github.com/settings/tokens

2. **Click**: "Generate new token" → "Generate new token (classic)"

3. **Set token name**: "Cruel Portal Scraper"

4. **Select scopes**:

    - ✅ `repo` (Full control of private repositories)
    - ✅ `read:user` (Read user profile data)

5. **Click**: "Generate token"

6. **Copy the token** (starts with `ghp_...`)
    - ⚠️ Save it somewhere safe - you can't see it again!

---

### Step 3: Test Portal Scraping (5 min)

#### Option A: Test Script (Recommended)

```bash
cd /Users/dhanyabad/code2/cruel/ai-cruel/backend

# Test with your GitHub token
python test_portal_scraping.py --token ghp_YOUR_TOKEN_HERE --repo torvalds/linux

# Or test registry only (no token needed)
python test_portal_scraping.py --test-registry
```

Expected output:

```
🚀 Portal Scraping Test Suite
============================================================
📚 AVAILABLE SCRAPERS
============================================================

✅ 6 scrapers registered:
   - BLACKBOARD: BlackboardScraper
   - CANVAS: CanvasScraper
   - GITHUB: GitHubScraper
   - JIRA: JiraScraper
   - MOODLE: MoodleScraper
   - TRELLO: TrelloScraper

============================================================
🔍 TESTING GITHUB PORTAL SCRAPER
============================================================

📋 Portal Configuration:
   Type: github
   Name: Test GitHub Portal
   Repo: torvalds/linux
   Token: ghp_xxxxx...

🔄 Starting scrape...

✅ Scrape Complete!
   Status: success
   Deadlines Found: X

📅 Scraped Deadlines:
------------------------------------------------------------
1. Issue #12345: Fix kernel bug
   Due: 2025-10-20 23:59:59
   Priority: high
   ...

============================================================
✅ TEST PASSED - Portal scraping is working!
============================================================
```

#### Option B: Test via API

```bash
# Start backend
cd /Users/dhanyabad/code2/cruel/ai-cruel/backend
uvicorn main:app --reload

# In another terminal, test the API
# 1. Login first to get JWT token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "yourpassword"
  }'

# Copy the access_token from response

# 2. Create a portal
curl -X POST http://localhost:8000/api/portals/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My GitHub",
    "type": "github",
    "url": "https://github.com",
    "credentials": {
      "token": "ghp_YOUR_GITHUB_TOKEN"
    },
    "config": {
      "repos": ["torvalds/linux"],
      "include_issues": true,
      "include_prs": true
    }
  }'

# 3. Sync the portal (portal_id from previous response)
curl -X POST http://localhost:8000/api/portals/1/sync \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 4. Check deadlines
curl http://localhost:8000/api/deadlines/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### Step 4: Test Frontend (2 min)

1. **Start frontend**:

```bash
cd /Users/dhanyabad/code2/cruel/ai-cruel/frontend
npm run dev
```

2. **Open browser**: http://localhost:3000

3. **Login** with your account

4. **Go to Portals page**: http://localhost:3000/portals

5. **Click "Add Portal"**:

    - Name: "My GitHub"
    - Type: Select "GitHub"
    - URL: https://github.com
    - Token: Paste your GitHub token
    - Config:
        ```json
        {
            "repos": ["owner/repo"],
            "include_issues": true
        }
        ```

6. **Click "Connect"**

7. **Click "Sync Now"** button

8. **Go to Deadlines page** to see scraped items!

---

## Available Scrapers

### ✅ GitHub

**What it scrapes:**

-   Issues assigned to you
-   Pull Requests
-   Milestone deadlines
-   Project board due dates

**Configuration:**

```json
{
    "repos": ["owner/repo1", "owner/repo2"],
    "include_issues": true,
    "include_prs": true,
    "include_assigned_only": false
}
```

**Credentials:**

```json
{
    "token": "ghp_xxxxx"
}
```

### ✅ Jira

**What it scrapes:**

-   Issues assigned to you
-   Sprint deadlines
-   Custom due date fields

**Configuration:**

```json
{
    "project_keys": ["PROJ1", "PROJ2"],
    "include_subtasks": true,
    "jql_filter": "assignee = currentUser()"
}
```

**Credentials:**

```json
{
    "email": "you@company.com",
    "api_token": "your_jira_token"
}
```

### ✅ Trello

**What it scrapes:**

-   Cards assigned to you
-   Due dates from cards
-   Checklist items with dates

**Configuration:**

```json
{
    "boards": ["board_id_1", "board_id_2"],
    "include_all_boards": false
}
```

**Credentials:**

```json
{
    "api_key": "your_key",
    "api_token": "your_token"
}
```

### ✅ Canvas LMS

**What it scrapes:**

-   Assignments
-   Quizzes
-   Discussion due dates

**Configuration:**

```json
{
    "courses": ["course_id_1", "course_id_2"],
    "include_past_courses": false
}
```

**Credentials:**

```json
{
    "access_token": "your_canvas_token"
}
```

### ✅ Blackboard

**What it scrapes:**

-   Assignments
-   Tests/Quizzes
-   Course announcements with dates

**Configuration:**

```json
{
    "courses": ["course_id_1"],
    "include_completed": false
}
```

**Credentials:**

```json
{
    "username": "your_username",
    "password": "your_password"
}
```

### ✅ Moodle

**What it scrapes:**

-   Assignments
-   Quizzes
-   Events calendar

**Configuration:**

```json
{
    "courses": ["course_id_1"],
    "weeks_ahead": 4
}
```

**Credentials:**

```json
{
    "token": "your_moodle_token"
}
```

---

## Troubleshooting

### ❌ "Portal table not found"

**Solution**: Run the SQL schema in Supabase (Step 1)

### ❌ "Invalid credentials"

**Solution**:

-   Check token is correct
-   Verify token has required scopes
-   For GitHub: repo + read:user

### ❌ "No deadlines found"

**Solution**:

-   GitHub: Issues need milestone or due date in description
-   Add text like "deadline: 2025-10-15" or "due: 2025-10-15"
-   Or assign issues to milestones with due dates

### ❌ "Rate limit exceeded"

**Solution**:

-   GitHub without token: 60 requests/hour
-   GitHub with token: 5,000 requests/hour
-   Wait or add authentication token

### ❌ "Connection refused"

**Solution**:

-   Backend not running - start with `uvicorn main:app --reload`
-   Check port 8000 is available

---

## Production Considerations

### 🔐 Security

-   [ ] Encrypt credentials before storing (use Supabase secrets or encryption)
-   [ ] Use environment variables for sensitive data
-   [ ] Enable HTTPS only
-   [ ] Rotate tokens regularly

### 📊 Performance

-   [ ] Add rate limiting to prevent API abuse
-   [ ] Implement caching for portal metadata
-   [ ] Use background jobs (Celery) for syncing
-   [ ] Add retry logic with exponential backoff

### 🔄 Automation

-   [ ] Set up Celery beat for automatic syncing
-   [ ] Configure sync frequency per portal
-   [ ] Add webhook support for real-time updates
-   [ ] Implement smart sync (only fetch new items)

### 📈 Monitoring

-   [ ] Log scraping success/failure rates
-   [ ] Track API usage and rate limits
-   [ ] Alert on consecutive failures
-   [ ] Monitor sync duration

---

## Next Steps

1. ✅ **Test with your portals** using the guide above
2. 🔧 **Configure auto-sync** (optional - Celery setup)
3. 🎨 **Customize portal types** (add more scrapers)
4. 🚀 **Deploy to production** (Railway + Vercel)

---

## Support

If you encounter issues:

1. Check backend logs for detailed errors
2. Verify Supabase tables were created
3. Test with the test script first
4. Check the portal credentials are valid

Happy scraping! 🎉
