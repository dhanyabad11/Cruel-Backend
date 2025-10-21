# Backend Deployment Guide

## Current Setup

-   **Platform**: Digital Ocean Droplet
-   **IP Address**: 198.211.106.97
-   **Location**: `/var/www/ai-cruel-backend/`
-   **Deployment**: Docker + Docker Compose

## 🔴 Important: Backend Does NOT Auto-Deploy

Unlike the frontend (which auto-deploys via Vercel when you push to GitHub), the backend on Digital Ocean requires **manual updates**.

## Manual Deployment Options

### Option 1: Using the Update Script (Recommended)

```bash
cd /Users/dhanyabad/code2/cruel/ai-cruel/backend/deploy
./update-backend.sh
```

This script will:

1. SSH into your droplet
2. Pull latest code from GitHub
3. Rebuild Docker containers
4. Restart all services
5. Show container status and logs

### Option 2: Manual SSH Commands

```bash
# SSH into the droplet
ssh root@198.211.106.97

# Navigate to app directory
cd /var/www/ai-cruel-backend

# Pull latest code
git pull origin main

# Rebuild and restart containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs --tail=50
```

### Option 3: Quick Update (No Rebuild)

If you only changed Python code (no dependencies):

```bash
ssh root@198.211.106.97 "cd /var/www/ai-cruel-backend && git pull && docker-compose restart backend"
```

## Automatic Deployment (GitHub Actions)

I've created a GitHub Actions workflow at `.github/workflows/deploy-backend.yml`.

### Setup Steps:

1. **Add GitHub Secrets** (in your repository settings):

    - Go to: `Settings > Secrets and variables > Actions`
    - Add these secrets:
        - `DROPLET_IP`: `198.211.106.97`
        - `DROPLET_SSH_KEY`: Your SSH private key content

2. **Get Your SSH Private Key**:

    ```bash
    cat ~/.ssh/id_ed25519
    ```

    Copy the entire output (including `-----BEGIN` and `-----END` lines)

3. **How It Works**:

    - Triggers on push to `main` branch (only when backend files change)
    - SSHs into droplet
    - Pulls code, rebuilds, restarts
    - Runs health check

4. **Manual Trigger**:
    - Go to: `Actions > Deploy Backend to Digital Ocean > Run workflow`

## Checking Deployment Status

### View Logs

```bash
ssh root@198.211.106.97 "cd /var/www/ai-cruel-backend && docker-compose logs -f"
```

### Check Container Status

```bash
ssh root@198.211.106.97 "cd /var/www/ai-cruel-backend && docker-compose ps"
```

### Test Backend Health

```bash
curl http://198.211.106.97/health
```

## Quick Reference

| Task             | Command                                                                            |
| ---------------- | ---------------------------------------------------------------------------------- |
| Deploy updates   | `./deploy/update-backend.sh`                                                       |
| View logs        | `ssh root@198.211.106.97 "cd /var/www/ai-cruel-backend && docker-compose logs -f"` |
| Restart services | `ssh root@198.211.106.97 "cd /var/www/ai-cruel-backend && docker-compose restart"` |
| Check health     | `curl http://198.211.106.97/health`                                                |
| SSH into server  | `ssh root@198.211.106.97`                                                          |

## Comparison: Frontend vs Backend

| Feature             | Frontend (Vercel)                      | Backend (Digital Ocean)          |
| ------------------- | -------------------------------------- | -------------------------------- |
| Auto-deploy on push | ✅ Yes                                 | ❌ No (manual or GitHub Actions) |
| Platform            | Vercel                                 | Digital Ocean Droplet            |
| Deployment method   | Automatic CI/CD                        | Manual or GitHub Actions         |
| URL                 | https://cruel-frontend-aj4z.vercel.app | http://198.211.106.97            |

## Troubleshooting

### If deployment fails:

```bash
# SSH into droplet
ssh root@198.211.106.97

# Check container logs
cd /var/www/ai-cruel-backend
docker-compose logs

# Check if containers are running
docker-compose ps

# Restart specific service
docker-compose restart backend
```

### If health check fails:

```bash
# Check Nginx status
ssh root@198.211.106.97 "systemctl status nginx"

# Check Docker network
ssh root@198.211.106.97 "docker network ls"
```
