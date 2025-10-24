# Redis Setup Guide for Production Email Reminders

## 🚨 Current Issue

Your Upstash Redis has exceeded the free tier limit (500,000 requests), which means:

-   ❌ Email reminders are NOT working in production
-   ❌ Celery tasks are NOT being processed
-   ❌ Portal scraping is NOT running automatically

## 📊 Redis Request Usage

The high usage is likely from:

-   Celery Beat checking every 5 minutes
-   Celery Worker polling for tasks
-   Task result storage

## ✅ Solutions

### Option 1: Upgrade Upstash (Easiest)

**Cost:** ~$10-20/month for 1M-10M commands

1. Go to [Upstash Console](https://console.upstash.com/)
2. Select your Redis instance
3. Click "Upgrade Plan"
4. Choose a plan based on your needs:
    - **Pay as You Go**: $0.2 per 100K commands
    - **Pro 2M**: $10/month for 2M commands
    - **Pro 10M**: $40/month for 10M commands

**Recommended:** Pro 2M should be sufficient for your app

### Option 2: Use Redis Labs (Free 30MB)

**Cost:** Free tier available

1. Go to [Redis Cloud](https://redis.com/try-free/)
2. Sign up for free account
3. Create a new database:
    - **Name:** ai-cruel-redis
    - **Region:** Choose closest to your Digital Ocean region
    - **Plan:** Free (30MB)
4. Get your connection details:
    ```
    redis://default:<password>@<endpoint>:<port>
    ```
5. Update `REDIS_URL` in your Digital Ocean environment variables

### Option 3: Digital Ocean Managed Redis

**Cost:** $15/month minimum

1. Go to [Digital Ocean Dashboard](https://cloud.digitalocean.com/)
2. Click "Create" → "Databases"
3. Select **Redis**
4. Choose:
    - **Plan:** Basic (1 GB RAM, $15/month)
    - **Region:** Same as your backend
    - **Name:** ai-cruel-redis
5. Wait 5-10 minutes for provisioning
6. Get connection string from database overview
7. Update `REDIS_URL` in your environment variables

### Option 4: Deploy Your Own Redis on DigitalOcean Droplet

**Cost:** $4-6/month

1. Create a small droplet ($4-6/month)
2. SSH into it
3. Install Redis:
    ```bash
    sudo apt update
    sudo apt install redis-server -y
    sudo systemctl enable redis-server
    sudo systemctl start redis-server
    ```
4. Configure Redis to accept external connections:
    ```bash
    sudo nano /etc/redis/redis.conf
    # Change bind 127.0.0.1 to bind 0.0.0.0
    # Set a password: requirepass YOUR_STRONG_PASSWORD
    sudo systemctl restart redis-server
    ```
5. Update `REDIS_URL` to: `redis://:<password>@<droplet-ip>:6379/0`

## 🔧 How to Update REDIS_URL in Production

### If Using Digital Ocean App Platform:

1. Go to your app in [DO Dashboard](https://cloud.digitalocean.com/apps)
2. Click on your backend component
3. Go to "Settings" → "Environment Variables"
4. Update `REDIS_URL` with new connection string
5. Click "Save" and redeploy

### If Using Digital Ocean Droplet:

1. SSH into your droplet
2. Update `.env` file:
    ```bash
    cd /path/to/your/app
    nano .env
    # Update REDIS_URL=<new-connection-string>
    ```
3. Restart services:
    ```bash
    sudo systemctl restart ai-cruel-backend
    # Or if using PM2:
    pm2 restart all
    ```

## ✅ Verify It's Working

After updating Redis, check if Celery is working:

```bash
curl http://198.211.106.97:8000/debug/celery
```

You should see:

```json
{
    "celery_configured": true,
    "workers_active": true,
    "workers_online": ["celery@hostname"]
}
```

## 📧 Test Email Reminders

1. Create a deadline in your app that's ~1 hour from now
2. Wait 5 minutes (Celery Beat runs every 5 minutes)
3. Check your email for the reminder

## 💡 Reduce Redis Usage (Optional)

To reduce request consumption, you can:

1. **Increase Beat interval** (currently every 5 minutes):

    ```python
    # In app/celery_app.py
    'check-email-reminders': {
        'schedule': crontab(minute='*/15'),  # Change to every 15 minutes
    }
    ```

2. **Disable unused tasks**:

    - Comment out portal scraping if not needed
    - Disable features you're not using

3. **Set result expiry** (already configured):
    ```python
    result_expires=3600  # Results expire after 1 hour
    ```

## 🎯 Recommended Solution

**For Production:** Use **Upstash Pro 2M** ($10/month)

-   Most reliable
-   Managed service (no maintenance)
-   Global replication
-   Good DX with dashboard

**For Development:** Keep using local Redis (free)

## 📝 Next Steps

1. Choose a Redis solution from above
2. Get the new `REDIS_URL` connection string
3. Update environment variables in production
4. Redeploy your backend
5. Verify with `/debug/celery` endpoint
6. Create a test deadline to confirm emails are sent

---

Need help? Check the logs:

```bash
# On Digital Ocean Droplet
tail -f /var/log/ai-cruel-backend.log

# Or check runtime logs in DO App Platform dashboard
```
