#!/bin/bash
# Automated Redis setup for your Digital Ocean droplet
# Run this from your LOCAL machine

DROPLET_IP="198.211.106.97"

echo "🚀 Setting up FREE Redis on your droplet..."
echo "=============================================="
echo ""
echo "This script will:"
echo "1. Install Redis on your droplet"
echo "2. Configure it with a password"
echo "3. Update your app's .env file"
echo "4. Restart your services"
echo ""
read -p "Press ENTER to continue or Ctrl+C to cancel..."

# Create the installation script
cat > /tmp/setup_redis_remote.sh << 'ENDOFSCRIPT'
#!/bin/bash
set -e

echo "📦 Installing Redis..."
apt-get update -qq
apt-get install -y redis-server

echo "🔐 Configuring Redis with password..."
REDIS_PASS=$(openssl rand -base64 20)

# Configure Redis
cp /etc/redis/redis.conf /etc/redis/redis.conf.backup
echo "requirepass $REDIS_PASS" >> /etc/redis/redis.conf
sed -i 's/bind 127.0.0.1 ::1/bind 127.0.0.1/' /etc/redis/redis.conf

# Start Redis
systemctl enable redis-server
systemctl restart redis-server

# Test Redis
sleep 2
if redis-cli -a "$REDIS_PASS" ping > /dev/null 2>&1; then
    echo "✅ Redis is working!"
else
    echo "❌ Redis test failed"
    exit 1
fi

# Save the Redis URL
REDIS_URL="redis://:$REDIS_PASS@127.0.0.1:6379/0"
echo "$REDIS_URL" > /root/redis_url.txt

# Find the app directory
APP_DIR=""
for dir in /root/ai-cruel-backend /var/www/ai-cruel-backend /opt/ai-cruel-backend ~/ai-cruel-backend; do
    if [ -d "$dir" ]; then
        APP_DIR="$dir"
        break
    fi
done

if [ -z "$APP_DIR" ]; then
    echo "⚠️  Could not find app directory automatically"
    echo "📋 Your Redis URL: $REDIS_URL"
    echo "Please manually update REDIS_URL in your .env file"
    exit 0
fi

echo "📁 Found app at: $APP_DIR"

# Update .env file
if [ -f "$APP_DIR/.env" ]; then
    cp "$APP_DIR/.env" "$APP_DIR/.env.backup"
    
    # Update REDIS_URL
    if grep -q "REDIS_URL=" "$APP_DIR/.env"; then
        sed -i "s|REDIS_URL=.*|REDIS_URL=$REDIS_URL|" "$APP_DIR/.env"
        echo "✅ Updated .env file"
    else
        echo "REDIS_URL=$REDIS_URL" >> "$APP_DIR/.env"
        echo "✅ Added REDIS_URL to .env file"
    fi
fi

# Try to restart services
echo "🔄 Restarting services..."
if command -v pm2 &> /dev/null; then
    pm2 restart all && echo "✅ Restarted with PM2"
elif systemctl list-units --type=service | grep -q ai-cruel; then
    systemctl restart ai-cruel-backend && echo "✅ Restarted with systemd"
elif command -v docker-compose &> /dev/null && [ -f "$APP_DIR/docker-compose.yml" ]; then
    cd "$APP_DIR" && docker-compose restart && echo "✅ Restarted with docker-compose"
else
    echo "⚠️  Please restart your services manually"
fi

echo ""
echo "=============================================="
echo "✅ Redis Setup Complete!"
echo "=============================================="
echo ""
echo "📋 Redis URL: $REDIS_URL"
echo "💾 Saved to: /root/redis_url.txt"
echo ""
echo "🎉 Your email reminders should now work!"
ENDOFSCRIPT

echo ""
echo "📤 Uploading and running script on droplet..."
echo ""

# Upload and run the script
scp /tmp/setup_redis_remote.sh root@$DROPLET_IP:/tmp/setup_redis.sh
ssh root@$DROPLET_IP "bash /tmp/setup_redis.sh"

echo ""
echo "✅ Done! Verifying..."
sleep 3

# Verify Celery is working
echo ""
echo "🔍 Testing if Celery is working..."
CELERY_STATUS=$(curl -s http://$DROPLET_IP:8000/debug/celery 2>/dev/null)

if echo "$CELERY_STATUS" | grep -q '"celery_configured":true'; then
    echo "✅ SUCCESS! Celery is working!"
    echo ""
    echo "🎉 Your email reminders are now active!"
    echo "   - Checks every 5 minutes for upcoming deadlines"
    echo "   - Sends emails 1 hour and 1 day before deadlines"
else
    echo "⚠️  Celery might need more time to start"
    echo "   Wait 1 minute and check: curl http://$DROPLET_IP:8000/debug/celery"
fi

echo ""
echo "=============================================="
echo "All done! 🚀"
echo "=============================================="
