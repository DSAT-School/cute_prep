#!/bin/bash

# Start Practice Portal with PM2

echo "Starting Practice Portal..."

# Stop existing process if running
pm2 delete practice-portal 2>/dev/null || true

# Start the application
pm2 start ecosystem.config.js

# Save PM2 process list
pm2 save

echo ""
echo "✓ Practice Portal started successfully!"
echo ""
echo "Useful commands:"
echo "  pm2 list           - Show running processes"
echo "  pm2 logs           - View logs"
echo "  pm2 restart all    - Restart application"
echo "  pm2 stop all       - Stop application"
echo ""
