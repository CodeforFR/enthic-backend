#!/bin/sh

# INSTALL DISTANT SYNAPTIC PACKAGES
apt-get -y install nginx certbot

# Create enthic user
useradd enthic || echo "User already exists."

# Give socket rights to enthic user
SOCKET=/var/www/enthic
mkdir -p ${SOCKET}
chown -R enthic:enthic ${SOCKET}
chomd -R 006 ${SOCKET}

# INSTALL ENTHIC SERVICE AND ENABLE IT
REPO_DIR=`pwd` envsubst < server/enthic.service > /etc/systemd/system/enthic.service
mkdir -p /var/www/enthic/
systemctl start enthic
systemctl enable enthic

# CONFIGURE NGINX SERVER
cp .server/enthic-nginx.conf /etc/nginx/sites-available/enthic.conf
ln -s /etc/nginx/sites-available/enthic.conf /etc/nginx/sites-enabled/

systemctl enable nginx
systemctl start nginx

# CONFIGURE HTTPS
certbot --nginx

# INSTALL DAILY UPDATE CRON
touch /etc/cron.daily/enthic

daily_cron_task="0 2 * * * enthic cd `pwd` && `pwd`/venv/bin/python -m enthic.scraping.download_from_INPI --source CQuest"
echo "${daily_cron_task}" > /etc/cron.daily/enthic
