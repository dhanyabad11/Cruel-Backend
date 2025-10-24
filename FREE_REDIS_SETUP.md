# 🎓 FREE Redis Setup for Students (No Credit Card!)

## 🚀 EASIEST Option: Railway.app FREE Redis

### Why Railway?

-   ✅ 100% FREE with GitHub Student Developer Pack
-   ✅ $5 monthly credit (enough for Redis)
-   ✅ No credit card required
-   ✅ 2-minute setup
-   ✅ Automatically works with your code

---

## 📋 Step-by-Step Instructions

### 1️⃣ Sign up for Railway (2 minutes)

1. Go to **https://railway.app/**
2. Click **"Login"** → **"Login with GitHub"**
3. Authorize Railway with your GitHub account
4. That's it! You get $5 free credit immediately

💡 **Student Tip**: If you have GitHub Student Developer Pack, you get $10/month free!

-   Apply at: https://education.github.com/pack

---

### 2️⃣ Deploy FREE Redis (1 minute)

1. After logging in to Railway, click **"New Project"**
2. Click **"Deploy Redis"**
3. Railway will automatically provision a Redis instance
4. Wait 30 seconds for deployment

---

### 3️⃣ Get Your Redis Connection String (1 minute)

1. Click on your **Redis service** (the box that appeared)
2. Go to the **"Connect"** tab
3. Look for **"Redis URL"** or **"REDIS_URL"**
4. Copy the entire connection string - it looks like:
    ```
    redis://default:PASSWORD@containers-us-west-xxx.railway.app:6379
    ```
5. **Copy this** - you'll need it in the next step

---

### 4️⃣ Update Your Digital Ocean App (3 minutes)

1. Go to **https://cloud.digitalocean.com/apps**
2. Click on your **"ai-cruel-backend"** app
3. In the sidebar, click **"Settings"**
4. Scroll to **"Environment Variables"** section
5. Find the variable **"REDIS_URL"**
6. Click **"Edit"** next to it
7. Replace the old Upstash URL with your new Railway Redis URL
8. Click **"Save"**
9. Digital Ocean will automatically **redeploy** your app (takes 2-3 minutes)

---

### 5️⃣ Verify It's Working (1 minute)

Wait for the deployment to finish, then run:

```bash
curl http://198.211.106.97:8000/debug/celery
```

✅ **Success looks like:**

```json
{
    "celery_configured": true,
    "workers_active": true,
    "workers_online": ["celery@..."]
}
```

❌ **If you see an error**, wait 1 more minute and try again (services need time to start)

---

### 6️⃣ Test Email Reminders (2 minutes)

1. Log into your app
2. Create a deadline that's **1 hour from now**
3. Add your email in notification settings
4. Enable "1_hour" reminder
5. Wait 5 minutes (Celery checks every 5 minutes)
6. **Check your email!** 📧

---

## 🔄 Alternative FREE Options

### Option A: Redis Labs (FREE 30MB)

-   Website: https://redis.com/try-free/
-   No credit card needed
-   30MB storage (perfect for your app)
-   Follow similar steps to get REDIS_URL

### Option B: Upstash with GitHub Education

-   Website: https://upstash.com/
-   If you have GitHub Student Pack, you get more free credits
-   Apply at: https://education.github.com/pack

---

## 💰 Cost Breakdown

| Service               | Monthly Cost | Your Cost                       |
| --------------------- | ------------ | ------------------------------- |
| Railway Redis         | ~$3-5/month  | **$0** (covered by free credit) |
| Digital Ocean Droplet | $6/month     | $6 (no change)                  |
| **Total**             |              | **$6/month**                    |

With GitHub Student Pack, Railway gives you $10/month credit, so Redis is completely free!

---

## 🆘 Troubleshooting

### "Celery not working after update"

-   Wait 5 minutes for services to fully restart
-   Check DO logs: Apps → Your App → Runtime Logs
-   Make sure REDIS_URL starts with `redis://` (not `rediss://`)

### "Still getting 'max requests limit exceeded'"

-   You might still have the old Upstash URL
-   Double-check you updated REDIS_URL in Digital Ocean
-   Click "Redeploy" in DO if needed

### "Railway says 'Out of credits'"

-   Your free $5 ran out
-   Apply for GitHub Student Pack for $10/month free
-   Or use Redis Labs free tier instead

---

## ✅ Final Checklist

-   [ ] Signed up for Railway.app with GitHub
-   [ ] Deployed Redis on Railway
-   [ ] Copied Redis connection string
-   [ ] Updated REDIS_URL in Digital Ocean environment variables
-   [ ] Waited for Digital Ocean to redeploy (2-3 minutes)
-   [ ] Verified with `/debug/celery` endpoint
-   [ ] Created test deadline to verify email reminders work

---

## 🎯 What Happens Next?

Once this is set up:

1. ✅ **Celery Beat** runs every 5 minutes checking for deadlines
2. ✅ **Email reminders** sent automatically:
    - 1 hour before deadline
    - 1 day before deadline
3. ✅ **Portal scraping** runs every 30 minutes (if you add portals)
4. ✅ **All automatic** - you don't need to do anything!

---

## 🎓 Student Pro Tip

Get the **GitHub Student Developer Pack**:

-   Free access to 100+ developer tools
-   Railway: $10/month free credit
-   Digital Ocean: $200 credit for 1 year
-   And much more!

Apply at: **https://education.github.com/pack**

---

Need help? Your email reminders will work in less than 10 minutes! 🚀
