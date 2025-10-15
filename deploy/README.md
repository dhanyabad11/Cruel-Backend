# 🚀 Deploy Your Backend to Digital Ocean Droplet

## ⚡ Quick Start (One Command!)

```bash
cd /Users/dhanyabad/code2/cruel/ai-cruel/backend
./deploy/create-droplet.sh
```

This will automatically:
- ✅ Create a new Digital Ocean droplet
- ✅ Install Docker, Nginx, and all dependencies
- ✅ Configure firewall and security
- ✅ Set up auto-deployment scripts
- ✅ Get your backend running in ~10 minutes!

**Cost:** Starting at $4/month (recommended: $6/month for 1GB RAM)

---

## 📋 Prerequisites

1. **Install doctl CLI:**
   ```bash
   brew install doctl  # macOS
   ```

2. **Authenticate:**
   ```bash
   doctl auth init
   ```
   Get your API token from: https://cloud.digitalocean.com/account/api/tokens

3. **Create SSH key (optional but recommended):**
   ```bash
   doctl compute ssh-key list
   ```

---

## 📖 Documentation

- **Quick Start Guide:** [deploy/DROPLET_QUICK_START.md](./DROPLET_QUICK_START.md)
- **Full Deployment Guide:** [DIGITAL_OCEAN_DEPLOYMENT.md](./DIGITAL_OCEAN_DEPLOYMENT.md)
- **App Platform Spec:** [.do/app.yaml](../.do/app.yaml)

---

## 🎯 What's Included

### Automated Scripts:

1. **`create-droplet.sh`** - Creates and configures a new droplet
2. **`setup-droplet.sh`** - Installs all dependencies on the droplet
3. **`deploy.sh`** - Deploys/updates your application (created on droplet)

### Features:

- 🐳 **Docker** - Containerized deployment
- 🌐 **Nginx** - Reverse proxy with SSL support
- 🔒 **UFW Firewall** - Automated security configuration
- 🔄 **Auto-restart** - Systemd service for reliability
- 📊 **Health checks** - Automatic monitoring
- 📝 **Logging** - Centralized log management

---

## 🏗️ Two Deployment Options

### Option 1: Automated Droplet (Recommended) ✅

**Best for:** Full control, lower cost, custom configuration

**Steps:**
1. Run `./deploy/create-droplet.sh`
2. Wait ~10 minutes
3. SSH in and edit `.env`
4. Run `./deploy.sh`
5. Done! 🎉

**Cost:** $4-6/month

### Option 2: App Platform 🚀

**Best for:** Managed infrastructure, zero DevOps

**Steps:**
1. Push code to GitHub
2. Create app in App Platform dashboard
3. Configure environment variables
4. Deploy!

**Cost:** $5-12/month

See [DIGITAL_OCEAN_DEPLOYMENT.md](./DIGITAL_OCEAN_DEPLOYMENT.md) for details.

---

## 🔧 After Deployment

### 1. Configure Environment Variables

```bash
ssh root@YOUR_DROPLET_IP
nano /var/www/ai-cruel-backend/.env
```

### 2. Deploy Application

```bash
cd /var/www/ai-cruel-backend
./deploy.sh
```

### 3. Verify It's Working

```bash
curl http://YOUR_DROPLET_IP/health
curl http://YOUR_DROPLET_IP/docs
```

### 4. (Optional) Set Up Domain + SSL

```bash
# Point DNS to your droplet IP
# Then on droplet:
apt install certbot python3-certbot-nginx -y
certbot --nginx -d yourdomain.com
```

---

## 📊 Quick Commands

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Update to latest code
/root/update-backend.sh

# Check status
docker-compose ps
```

---

## 💰 Total Monthly Cost

| Service | Provider | Cost |
|---------|----------|------|
| Droplet (1GB) | Digital Ocean | $6/month |
| Database | Supabase | Free |
| Redis | Upstash | Free |
| Email | Gmail SMTP | Free |
| SMS/WhatsApp | Twilio | Pay-as-go (~$0.01/msg) |
| **Total** | | **~$6/month** |

---

## 🆘 Need Help?

- 📖 **Full Guide:** [DIGITAL_OCEAN_DEPLOYMENT.md](./DIGITAL_OCEAN_DEPLOYMENT.md)
- 🚀 **Quick Start:** [deploy/DROPLET_QUICK_START.md](./deploy/DROPLET_QUICK_START.md)
- 🐛 **Troubleshooting:** See troubleshooting sections in guides above

---

## ✅ Deployment Checklist

- [ ] Install doctl CLI
- [ ] Authenticate with Digital Ocean
- [ ] Run `./deploy/create-droplet.sh`
- [ ] Wait for setup to complete
- [ ] SSH in and configure `.env`
- [ ] Run `./deploy.sh`
- [ ] Test API endpoints
- [ ] Set up domain (optional)
- [ ] Get SSL certificate (optional)
- [ ] Update frontend with new API URL

---

**Ready to deploy? Run: `./deploy/create-droplet.sh`** 🚀
