# Digital Ocean Droplet Deployment - Quick Start

## 🚀 Automated Droplet Setup

I've created automated scripts to deploy your backend to a Digital Ocean Droplet in minutes!

---

## 📋 Prerequisites

1. **Digital Ocean Account**: [Sign up here](https://m.do.co/c/your-referral)
2. **doctl CLI**: Install with `brew install doctl` (macOS)
3. **SSH Key**: For secure access (optional but recommended)

---

## ⚡ Quick Deploy (2 Commands)

### Step 1: Authenticate with Digital Ocean

```bash
doctl auth init
```

Enter your API token from: https://cloud.digitalocean.com/account/api/tokens

### Step 2: Create and Setup Droplet

```bash
cd /Users/dhanyabad/code2/cruel/ai-cruel/backend
chmod +x deploy/create-droplet.sh
./deploy/create-droplet.sh
```

This script will:
- ✅ Create a new Ubuntu 22.04 droplet
- ✅ Install Docker, Nginx, and all dependencies
- ✅ Configure firewall and security
- ✅ Set up automatic deployment
- ✅ Create useful management scripts

**Total time:** ~10 minutes

---

## 🎯 What You Get

### Automated Setup Includes:

- **Docker & Docker Compose** - Containerized deployment
- **Nginx** - Reverse proxy with SSL support
- **UFW Firewall** - Ports 22, 80, 443 configured
- **Systemd Service** - Auto-start on reboot
- **Deployment Scripts** - One-command updates
- **Health Checks** - Automatic monitoring

### Directory Structure:

```
/var/www/ai-cruel-backend/
├── .env                    # Your environment variables
├── docker-compose.yml      # Container orchestration
├── Dockerfile             # Already in your repo
├── deploy.sh              # Deployment script
└── logs/                  # Application logs
```

---

## 📖 Manual Setup (If You Prefer)

### Option 1: Create Droplet via Web UI

1. Go to [Digital Ocean Droplets](https://cloud.digitalocean.com/droplets/new)
2. Select:
   - **Image:** Ubuntu 22.04 LTS
   - **Plan:** Basic - $6/month (1GB RAM recommended)
   - **Region:** Closest to your users
   - **Authentication:** SSH key or password
3. Click "Create Droplet"

### Option 2: SSH and Run Setup Script

```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Download and run setup script
curl -sSL https://raw.githubusercontent.com/dhanyabad11/Cruel-Backend/main/deploy/setup-droplet.sh -o setup.sh
sudo bash setup.sh
```

---

## ⚙️ Configuration

### 1. Edit Environment Variables

After droplet creation, SSH in and edit:

```bash
ssh root@your-droplet-ip
nano /var/www/ai-cruel-backend/.env
```

Required variables:
```bash
# Supabase (from your dashboard)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-key
SUPABASE_SERVICE_KEY=your-key

# Redis (keep using Upstash or use local)
REDIS_URL=rediss://your-upstash-url

# Twilio
TWILIO_ACCOUNT_SID=ACxxxxxx
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=+1234567890

# Email
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# CORS (update after frontend deployed)
ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app
```

### 2. Deploy Application

```bash
cd /var/www/ai-cruel-backend
./deploy.sh
```

This will:
- Pull latest code from GitHub
- Build Docker containers
- Start all services (FastAPI + Celery + Redis)
- Show logs

### 3. Verify Deployment

```bash
# Check if containers are running
docker-compose ps

# View logs
docker-compose logs -f

# Test API
curl http://localhost:8000/health
```

---

## 🌐 Access Your API

### Via IP Address:
```
http://YOUR_DROPLET_IP/
http://YOUR_DROPLET_IP/docs
http://YOUR_DROPLET_IP/health
```

### Set Up Custom Domain (Optional):

1. **Point DNS A record** to your droplet IP
2. **Update Nginx config**:
   ```bash
   nano /etc/nginx/sites-available/ai-cruel
   # Change: server_name _; to server_name yourdomain.com;
   nginx -t && systemctl reload nginx
   ```
3. **Get SSL certificate**:
   ```bash
   apt install certbot python3-certbot-nginx -y
   certbot --nginx -d yourdomain.com
   ```

---

## 🔧 Management Commands

### Deployment & Updates

```bash
# Update to latest code
/root/update-backend.sh

# Or manually:
cd /var/www/ai-cruel-backend
git pull origin main
./deploy.sh
```

### Container Management

```bash
# View all containers
docker-compose ps

# View logs
docker-compose logs -f              # All services
docker-compose logs -f backend      # Backend only

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Monitoring

```bash
# System resources
htop

# Docker stats
docker stats

# Nginx access logs
tail -f /var/log/nginx/ai-cruel-access.log

# Nginx error logs
tail -f /var/log/nginx/ai-cruel-error.log

# Application logs
docker-compose logs --tail=100
```

---

## 🔒 Security Hardening

### 1. Change SSH Port

```bash
nano /etc/ssh/sshd_config
# Change: Port 22 to Port 2222
systemctl restart sshd

# Update firewall
ufw allow 2222/tcp
ufw delete allow 22/tcp
```

### 2. Install Fail2Ban

```bash
apt install fail2ban -y
systemctl enable fail2ban
systemctl start fail2ban
```

### 3. Set Up Automatic Updates

```bash
apt install unattended-upgrades -y
dpkg-reconfigure --priority=low unattended-upgrades
```

### 4. Create Non-Root User

```bash
adduser deploy
usermod -aG sudo,docker deploy
su - deploy
```

---

## 💰 Cost Comparison

| Plan | RAM | CPU | Storage | Price/Month |
|------|-----|-----|---------|-------------|
| Basic | 512MB | 1 | 10GB | $4 |
| Basic | 1GB | 1 | 25GB | **$6** ⭐ |
| Basic | 2GB | 1 | 50GB | $12 |
| Basic | 2GB | 2 | 60GB | $18 |

**Recommended:** 1GB plan ($6/month) for production

**Additional costs:**
- Upstash Redis: Free (10k requests/day)
- Supabase: Free (500MB database)
- Total: **$6/month** + SMS/email usage

---

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Missing .env variables
nano /var/www/ai-cruel-backend/.env

# 2. Port already in use
lsof -i :8000
# Kill process: kill -9 <PID>

# 3. Build errors
docker-compose build --no-cache
```

### Nginx Errors

```bash
# Test configuration
nginx -t

# View error logs
tail -f /var/log/nginx/error.log

# Reload configuration
systemctl reload nginx
```

### Out of Memory

```bash
# Check memory usage
free -h

# Upgrade droplet
doctl compute droplet-action resize YOUR_DROPLET_ID --size s-1vcpu-2gb

# Or add swap
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
```

### Celery Not Running

```bash
# Check Redis connection
docker-compose exec backend python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"

# View Celery logs
docker-compose logs backend | grep -i celery

# Restart backend
docker-compose restart backend
```

---

## 📊 Monitoring & Logs

### View Real-Time Logs

```bash
# All services
docker-compose logs -f

# Filter by keyword
docker-compose logs -f | grep -i error

# Last 100 lines
docker-compose logs --tail=100
```

### Check Service Health

```bash
# Health endpoint
curl http://localhost:8000/health

# API docs
curl http://localhost:8000/docs

# Check Celery tasks
docker-compose exec backend celery -A app.celery_app inspect active
```

---

## 🔄 Backup & Restore

### Backup

```bash
# Backup .env and docker-compose
cd /var/www/ai-cruel-backend
tar -czf backup-$(date +%Y%m%d).tar.gz .env docker-compose.yml

# Copy to local machine
scp root@YOUR_IP:/var/www/ai-cruel-backend/backup-*.tar.gz ./
```

### Restore

```bash
# Upload backup
scp backup-20251015.tar.gz root@YOUR_IP:/root/

# SSH in and restore
ssh root@YOUR_IP
cd /var/www/ai-cruel-backend
tar -xzf /root/backup-20251015.tar.gz
./deploy.sh
```

---

## 📈 Scaling

### Vertical Scaling (Upgrade Droplet)

```bash
# Via CLI
doctl compute droplet-action resize YOUR_DROPLET_ID --size s-2vcpu-2gb --resize-disk

# Via Dashboard: Droplet → Resize → Choose new size
```

### Horizontal Scaling (Multiple Droplets)

1. Set up load balancer
2. Deploy to multiple droplets
3. Configure shared Redis/Database

---

## ✅ Deployment Checklist

After setup, verify:

- [ ] Droplet created and accessible via SSH
- [ ] Docker and Nginx installed
- [ ] Environment variables configured
- [ ] Application deployed with `./deploy.sh`
- [ ] Health endpoint returns 200: `curl http://localhost:8000/health`
- [ ] API docs accessible: `curl http://localhost:8000/docs`
- [ ] Celery tasks running (check logs)
- [ ] Nginx reverse proxy working
- [ ] Firewall configured (ports 22, 80, 443)
- [ ] SSL certificate installed (if using domain)
- [ ] Frontend CORS origin updated

---

## 🚀 Next Steps

1. ✅ Droplet created and configured
2. ⏳ Deploy frontend to Vercel
3. ⏳ Update CORS with frontend URL
4. ⏳ Set up domain and SSL
5. ⏳ Configure monitoring alerts
6. ⏳ Test all features end-to-end

---

## 📚 Resources

- [Digital Ocean Documentation](https://docs.digitalocean.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Nginx Configuration Guide](https://nginx.org/en/docs/)
- [Certbot Documentation](https://certbot.eff.org/)
- [Main Deployment Guide](./DIGITAL_OCEAN_DEPLOYMENT.md)

---

**Your droplet is ready to deploy! 🎉**

Run: `./deploy/create-droplet.sh` to get started!
