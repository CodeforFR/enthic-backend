#!/bin/sh

# INSTALL DISTANT SYNAPTIC PACKAGES
apt-get -y install nginx certbot python3-certbot-nginx

# Create enthic user
useradd enthic || echo "User already exists."

# Give socket rights to enthic user
SOCKET=/var/www/enthic
mkdir -p ${SOCKET}
chown -R enthic:enthic ${SOCKET}
chmod -R 777 ${SOCKET}

# INSTALL ENTHIC SERVICE AND ENABLE IT
REPO_DIR=`pwd` envsubst < server/enthic.service > /etc/systemd/system/enthic.service || exit 2
mkdir -p /var/www/enthic/
systemctl daemon-reload
systemctl start enthic
systemctl enable enthic

# CONFIGURE NGINX SERVER
cp server/enthic-nginx.conf /etc/nginx/sites-available/enthic.conf
ln -sf /etc/nginx/sites-available/enthic.conf /etc/nginx/sites-enabled/

systemctl enable nginx
systemctl start nginx

# CONFIGURE HTTPS
certbot --nginx

# INSTALL DAILY UPDATE CRON
touch /etc/cron.daily/enthic

daily_cron_task="0 2 * * * enthic cd `pwd` && `pwd`/venv/bin/python -m enthic.scraping.download_from_INPI --source CQuest"
echo "${daily_cron_task}" > /etc/cron.daily/enthic
