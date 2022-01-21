#!/bin/sh

################################################################################
# 1) UPDATE SOURCE CODE FROM GIT
git stash
git pull --rebase
git stash pop

# 2) RESTART ENTHIC SERVICE
systemctl restart enthic
