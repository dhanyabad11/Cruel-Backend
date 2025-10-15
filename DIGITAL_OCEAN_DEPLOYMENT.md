# Digital Ocean Deployment Guide

## 🚀 Deploying AI Cruel Backend to Digital Ocean

This guide covers deploying your FastAPI backend to Digital Ocean App Platform with all features (Celery, Redis, Portal Scraping, Notifications).

---

## 📋 Prerequisites

Before deploying, ensure you have:

- [ ] Digital Ocean account ([Sign up here](https://cloud.digitalocean.com/registrations/new))
- [ ] GitHub repository pushed with latest code
- [ ] Supabase project created ([Supabase Dashboard](https://supabase.com/dashboard))
- [ ] Redis instance (Upstash free tier or DO Managed Redis)
- [ ] Twilio account for SMS/WhatsApp ([Twilio Console](https://console.twilio.com/))
- [ ] SMTP credentials for email (Gmail App Password recommended)

---

## 🎯 Deployment Options

### Option 1: Digital Ocean App Platform (Recommended) ✅

**Pros:**
- Easy deployment from GitHub
- Auto-scaling and managed infrastructure
- Built-in SSL certificates
- Simple environment variable management
- Starting at $5/month

**Best for:** Production deployments, managed infrastructure

### Option 2: Digital Ocean Droplet (VPS)

**Pros:**
- Full control over server
- Potentially cheaper for high-traffic apps
- Can install additional services
- Starting at $4/month

**Best for:** Custom configurations, experienced DevOps users

---

## 🏗️ Option 1: Deploy to App Platform (Recommended)

### Step 1: Prepare Your Repository

Ensure your code is pushed to GitHub:

```bash
cd /Users/dhanyabad/code2/cruel/ai-cruel/backend
git add .
git commit -m "Prepare for Digital Ocean deployment"
git push origin main
```

### Step 2: Create Redis Instance

**Option A: Use Upstash (Free Tier - Recommended)**

1. Go to [Upstash Console](https://console.upstash.com/)
2. Create new Redis database
3. Select a region close to your DO region (e.g., `us-east-1`)
4. Copy the `UPSTASH_REDIS_REST_URL` (use the `rediss://` format)
5. Save for later: `rediss://default:PASSWORD@HOST:6379`

**Option B: Use Digital Ocean Managed Redis**

1. Go to [DO Databases](https://cloud.digitalocean.com/databases)
2. Click "Create" → "Database"
3. Choose Redis
4. Select smallest plan ($15/month)
5. Copy connection string

### Step 3: Deploy to App Platform

#### Via Web UI:

1. **Go to App Platform**
   - Visit [Digital Ocean App Platform](https://cloud.digitalocean.com/apps)
   - Click "Create App"

2. **Connect Repository**
   - Choose "GitHub"
   - Authorize Digital Ocean
   - Select repository: `dhanyabad11/Cruel-Backend`
   - Select branch: `main`
   - Check "Autodeploy" (deploys on every push)

3. **Configure App**
   - **Name:** `ai-cruel-backend`
   - **Region:** Choose closest to your users (e.g., `New York`)
   - **Type:** Web Service
   - **Dockerfile Path:** `Dockerfile`
   - **HTTP Port:** `8000`

4. **Set Resource Size**
   - **Basic (XXS):** $5/month - 512MB RAM, 1 vCPU (good for testing)
   - **Basic (XS):** $12/month - 1GB RAM, 1 vCPU (recommended for production)
   - **Basic (S):** $24/month - 2GB RAM, 2 vCPU (better performance)

5. **Add Environment Variables** (see below)

6. **Review and Deploy**
   - Click "Next" → "Review" → "Create Resources"
   - Wait 5-10 minutes for build and deployment

#### Via CLI (doctl):

```bash
# Install doctl
brew install doctl  # macOS
# or download from: https://docs.digitalocean.com/reference/doctl/how-to/install/

# Authenticate
doctl auth init

# Deploy using spec file
doctl apps create --spec .do/app.yaml

# Or update existing app
doctl apps update YOUR_APP_ID --spec .do/app.yaml
```

### Step 4: Configure Environment Variables

In the App Platform dashboard, add these environment variables:

#### Required Variables:

```bash
# Application
HOST=0.0.0.0
PORT=8000
DEBUG=False
ENVIRONMENT=production

# CORS (Update after frontend deployment)
ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app

# Supabase (from Supabase Dashboard > Settings > API)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-role-key

# Database (from Supabase Dashboard > Settings > Database)
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# Redis (from Upstash or DO Managed Redis)
REDIS_URL=rediss://default:PASSWORD@HOST:6379

# Twilio (from Twilio Console)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890

# Email (Gmail App Password recommended)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=AI Cruel Deadline Manager

# Security
SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
```

**💡 Tip:** Mark sensitive values as "Secret" in the DO dashboard (they'll be encrypted)

### Step 5: Configure Health Checks

App Platform should auto-detect the health check from `app.yaml`, but verify:

- **HTTP Path:** `/health`
- **Port:** `8000`
- **Initial Delay:** 60 seconds
- **Timeout:** 5 seconds

### Step 6: Verify Deployment

Once deployed, your app will be available at:
```
https://ai-cruel-backend-xxxxx.ondigitalocean.app
```

Test the endpoints:

```bash
# Health check
curl https://your-app.ondigitalocean.app/health

# API docs
curl https://your-app.ondigitalocean.app/docs

# Test signup
curl -X POST https://your-app.ondigitalocean.app/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@gmail.com","password":"Test123!","full_name":"Test User"}'
```

### Step 7: Monitor Logs

View logs in real-time:

**Via Dashboard:**
- Go to your app in App Platform
- Click "Runtime Logs" tab
- Look for Celery worker and beat messages

**Via CLI:**
```bash
doctl apps logs YOUR_APP_ID --type run --follow
```

You should see:
```
✅ Starting Celery Beat...
✅ Starting Celery Worker...
✅ Starting Uvicorn...
✅ Task app.tasks.scraping_tasks.scrape_all_portals succeeded
```

---

## 🏗️ Option 2: Deploy to Droplet (Advanced)

### Step 1: Create Droplet

1. Go to [Create Droplet](https://cloud.digitalocean.com/droplets/new)
2. Choose:
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Basic ($4/month - 512MB or $6/month - 1GB recommended)
   - **Region:** Same as Redis for low latency
   - **Authentication:** SSH key (recommended) or password
3. Click "Create Droplet"

### Step 2: SSH into Droplet

```bash
ssh root@your-droplet-ip
```

### Step 3: Install Dependencies

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Install Git
apt install git -y
```

### Step 4: Clone Repository

```bash
# Clone your repo
git clone https://github.com/dhanyabad11/Cruel-Backend.git
cd Cruel-Backend

# Create .env file
cp .env.example .env
nano .env  # Edit with your values
```

### Step 5: Build and Run with Docker

```bash
# Build image
docker build -t ai-cruel-backend .

# Run container
docker run -d \
  --name ai-cruel-backend \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  ai-cruel-backend

# Check logs
docker logs -f ai-cruel-backend
```

### Step 6: Set Up Nginx Reverse Proxy (Optional but Recommended)

```bash
# Install Nginx
apt install nginx -y

# Create Nginx config
nano /etc/nginx/sites-available/ai-cruel
```

Add this configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:

```bash
ln -s /etc/nginx/sites-available/ai-cruel /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Step 7: Set Up SSL with Certbot

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get certificate
certbot --nginx -d your-domain.com

# Auto-renewal is set up automatically
```

---

## 🔧 Post-Deployment Configuration

### 1. Update CORS Origins

After deploying frontend, update `ALLOWED_ORIGINS`:

```bash
ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://your-app.ondigitalocean.app
```

### 2. Set Up Monitoring

**App Platform has built-in monitoring:**
- CPU usage
- Memory usage
- Response times
- Error rates

**Set up alerts:**
1. Go to App Platform → Your App → Alerts
2. Add alert rules for:
   - High CPU (> 80%)
   - High memory (> 80%)
   - App restart
   - Deployment failure

### 3. Configure Backups

**Supabase:** Automatic daily backups (free tier includes 7-day retention)

**Digital Ocean:**
- App Platform: Automatic git-based rollbacks
- Droplet: Enable weekly backups ($1/month for $5 droplet)

### 4. Set Up Domain (Optional)

1. Go to your app → Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed
4. SSL certificate will be auto-provisioned

---

## 💰 Cost Breakdown

### App Platform Deployment:

| Service | Cost | Notes |
|---------|------|-------|
| DO App Platform | $5-12/month | 512MB-1GB RAM |
| Upstash Redis | Free | 10,000 commands/day |
| Supabase | Free | 500MB database |
| Twilio | Pay-as-you-go | ~$0.01/SMS |
| **Total** | **$5-12/month** | Plus usage costs |

### Droplet Deployment:

| Service | Cost | Notes |
|---------|------|-------|
| DO Droplet | $4-6/month | 512MB-1GB RAM |
| Upstash Redis | Free | 10,000 commands/day |
| Supabase | Free | 500MB database |
| Twilio | Pay-as-you-go | ~$0.01/SMS |
| **Total** | **$4-6/month** | Plus usage costs |

---

## 🐛 Troubleshooting

### Build Fails

**Error:** `Cannot find module 'X'`
```bash
# Check requirements.txt includes all dependencies
pip freeze > requirements.txt
```

**Error:** `gcc: command not found`
```bash
# Dockerfile already includes build tools
# Ensure using python:3.10-slim base image
```

### Celery Not Starting

**Check logs:**
```bash
doctl apps logs YOUR_APP_ID | grep -i celery
```

**Common issues:**
- Redis URL incorrect (check format: `rediss://` vs `redis://`)
- Missing REDIS_URL environment variable
- Redis instance not accessible from DO region

**Fix:**
- Verify REDIS_URL in App Platform settings
- Test Redis connection: `redis-cli -u $REDIS_URL ping`

### SSL Certificate Errors (rediss://)

**Error:** `ssl_cert_reqs parameter required`
- Already fixed in code (see `app/celery_app.py`)
- Ensure using latest code from GitHub

### App Crashes After Deployment

**Check health endpoint:**
```bash
curl https://your-app.ondigitalocean.app/health
```

**View runtime logs:**
- App Platform → Your App → Runtime Logs
- Look for Python errors or missing environment variables

**Common issues:**
- Missing required environment variables
- Database connection failed (check DATABASE_URL)
- Port mismatch (should be 8000)

### High Memory Usage

**Symptoms:**
- App restarts frequently
- Out of memory errors

**Solutions:**
- Upgrade to larger plan (1GB or 2GB)
- Optimize Celery worker concurrency:
  ```bash
  # In start_services.py, add:
  '--concurrency=2',  # Limit worker threads
  ```

---

## 📊 Monitoring and Maintenance

### View Logs

```bash
# Runtime logs
doctl apps logs YOUR_APP_ID --type run --follow

# Build logs
doctl apps logs YOUR_APP_ID --type build

# Deployment logs
doctl apps logs YOUR_APP_ID --type deploy
```

### Update Deployment

```bash
# Push to GitHub (auto-deploys if enabled)
git add .
git commit -m "Update backend"
git push origin main

# Or force rebuild
doctl apps create-deployment YOUR_APP_ID --force-rebuild
```

### Rollback Deployment

```bash
# List deployments
doctl apps list-deployments YOUR_APP_ID

# Rollback to previous
doctl apps create-deployment YOUR_APP_ID --revert DEPLOYMENT_ID
```

### Scale Resources

Via Dashboard:
1. Go to App Platform → Your App
2. Click "Edit Plan"
3. Select new instance size
4. Click "Save" (will redeploy)

---

## ✅ Deployment Checklist

Before going live:

- [ ] All environment variables configured
- [ ] Health check returns `{"status":"healthy"}`
- [ ] API docs accessible at `/docs`
- [ ] User signup/signin working
- [ ] Celery tasks appearing in logs
- [ ] Email notifications sending
- [ ] SMS/WhatsApp notifications working (if configured)
- [ ] Portal scraping running every 30 minutes
- [ ] CORS configured with frontend URL
- [ ] Custom domain configured (if using)
- [ ] Monitoring alerts set up
- [ ] Backup strategy confirmed

---

## 🚀 Next Steps

1. ✅ Backend deployed to Digital Ocean
2. ⏳ Deploy frontend to Vercel
3. ⏳ Update CORS with frontend URL
4. ⏳ Test end-to-end user flow
5. ⏳ Set up monitoring and alerts
6. ⏳ Configure custom domain (optional)

---

## 📚 Useful Links

- [Digital Ocean App Platform Docs](https://docs.digitalocean.com/products/app-platform/)
- [doctl CLI Reference](https://docs.digitalocean.com/reference/doctl/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Supabase Documentation](https://supabase.com/docs)
- [Upstash Redis Documentation](https://docs.upstash.com/redis)

---

## 💬 Support

If you encounter issues:

1. Check runtime logs in App Platform dashboard
2. Verify all environment variables are set
3. Test health endpoint
4. Review this troubleshooting guide
5. Check Digital Ocean community forums

---

**Your backend is ready for Digital Ocean! 🎉**
