# 🎓 FREE Redis Setup - Self-Hosted on Your Droplet

**Cost: $0** (uses your existing $6 droplet)

Since you already have a Digital Ocean droplet running at `198.211.106.97`, let's install Redis directly on it. This is completely FREE and takes 5 minutes.

---

## 📋 Quick Setup (5 minutes)

### Option 1: Automated Installation (Easiest)

1. **SSH into your droplet:**

    ```bash
    ssh root@198.211.106.97
    ```

2. **Run the installation script:**

    ```bash
    # Download the script
    curl -o install_redis.sh https://raw.githubusercontent.com/dhanyabad11/Cruel-Frontend/main/ai-cruel/backend/deploy/install_redis.sh

    # OR if that doesn't work, create it manually:
    nano install_redis.sh
    # Paste the contents from the file I just created
    # Press Ctrl+X, then Y, then Enter to save

    # Make it executable
    chmod +x install_redis.sh

    # Run it
    sudo bash install_redis.sh
    ```

3. **Copy the REDIS_URL** that appears at the end (looks like: `redis://:ABC123@127.0.0.1:6379/0`)

4. **Update your app's environment:**

    ```bash
    # Find your app directory
    cd /root/ai-cruel-backend  # Or wherever your app is

    # Edit .env file
    nano .env

    # Update the REDIS_URL line to the new one
    # Save with Ctrl+X, then Y, then Enter
    ```

5. **Restart your services:**

    ```bash
    # If using PM2:
    pm2 restart all

    # If using systemd:
    systemctl restart ai-cruel-backend

    # If using Docker:
    docker-compose restart
    ```

---

### Option 2: Manual Installation (If script doesn't work)

If the automated script doesn't work, here are the manual commands:

```bash
# SSH into your droplet
ssh root@198.211.106.97

# Update system
apt-get update

# Install Redis
apt-get install -y redis-server

# Generate a strong password
REDIS_PASSWORD=$(openssl rand -base64 32)
echo $REDIS_PASSWORD

# Configure Redis with password
echo "requirepass $REDIS_PASSWORD" >> /etc/redis/redis.conf

# Restart Redis
systemctl restart redis-server
systemctl enable redis-server

# Test it works
redis-cli -a "$REDIS_PASSWORD" ping
# Should output: PONG

# Your REDIS_URL is:
echo "redis://:$REDIS_PASSWORD@127.0.0.1:6379/0"
```

---

## ✅ Verify It's Working

After updating and restarting:

```bash
curl http://198.211.106.97:8000/debug/celery
```

Should show:

```json
{
    "celery_configured": true,
    "workers_active": true
}
```

---

## 🔧 How to Find Your App Location

If you're not sure where your app is running on the droplet:

```bash
# SSH into droplet
ssh root@198.211.106.97

# Find running processes
ps aux | grep uvicorn
ps aux | grep python

# Common locations:
ls /root/ai-cruel-backend
ls /var/www/ai-cruel-backend
ls /opt/ai-cruel-backend
ls ~/ai-cruel-backend

# Find all .env files
find / -name ".env" -type f 2>/dev/null | grep -i cruel
```

---

## 🚀 Update Environment on the Droplet

Once you find where your app is running:

```bash
cd /path/to/your/app

# Backup old .env
cp .env .env.backup

# Edit .env
nano .env

# Find the line that says:
# REDIS_URL=rediss://default:ATXsA...@complete-whale-13804.upstash.io:6379

# Replace it with your new local Redis URL:
# REDIS_URL=redis://:YOUR_PASSWORD@127.0.0.1:6379/0

# Save: Ctrl+X, then Y, then Enter

# Restart your app
pm2 restart all
# OR
systemctl restart ai-cruel-backend
# OR
docker-compose restart
```

---

## 💡 Why This is Better

✅ **FREE** - No additional cost, uses your existing droplet  
✅ **Fast** - Local connection, no network latency  
✅ **Unlimited** - No request limits like Upstash free tier  
✅ **Simple** - One less external service to manage  
✅ **Reliable** - No dependency on external Redis providers

---

## 🆘 Troubleshooting

### "Can't connect to Redis"

```bash
# Check if Redis is running
systemctl status redis-server

# If not running, start it
systemctl start redis-server

# Check logs
journalctl -u redis-server -n 50
```

### "Connection refused"

```bash
# Make sure Redis is listening on 127.0.0.1
grep "bind" /etc/redis/redis.conf

# Should show: bind 127.0.0.1
# If not, add it:
echo "bind 127.0.0.1" >> /etc/redis/redis.conf
systemctl restart redis-server
```

### "Authentication failed"

```bash
# Check your password
grep "requirepass" /etc/redis/redis.conf

# If you forgot the password, set a new one:
NEW_PASSWORD=$(openssl rand -base64 32)
sed -i "s/requirepass .*/requirepass $NEW_PASSWORD/" /etc/redis/redis.conf
systemctl restart redis-server
echo "New REDIS_URL: redis://:$NEW_PASSWORD@127.0.0.1:6379/0"
```

### "App won't start after Redis update"

```bash
# Check app logs
pm2 logs
# OR
journalctl -u ai-cruel-backend -n 50
# OR
docker-compose logs

# Common issue: Wrong REDIS_URL format
# Should be: redis://:PASSWORD@127.0.0.1:6379/0
# NOT: rediss:// (remove the extra 's')
```

---

## 📊 Redis Management Commands

```bash
# Check Redis status
systemctl status redis-server

# View Redis logs
journalctl -u redis-server -f

# Connect to Redis CLI
redis-cli -a "YOUR_PASSWORD"

# Inside Redis CLI:
> ping                    # Test connection
> INFO                    # View Redis info
> DBSIZE                  # Number of keys
> KEYS *                  # List all keys
> FLUSHALL                # Clear all data (careful!)
> exit                    # Exit CLI
```

---

## 🎯 Summary

1. SSH into your droplet: `ssh root@198.211.106.97`
2. Install Redis: `apt-get install -y redis-server`
3. Set password and get REDIS_URL
4. Update .env file in your app directory
5. Restart your app: `pm2 restart all`
6. Verify: `curl http://198.211.106.97:8000/debug/celery`

**Total cost: $0**  
**Total time: 5 minutes**

Your email reminders will work automatically after this! 🎉

---

Need help with any step? Let me know which part you're stuck on.
