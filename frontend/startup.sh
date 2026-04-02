#!/bin/bash
# Startup script for Azure App Service - Node.js/React Frontend
# This script runs when the App Service starts

# Set working directory
cd /home/site/wwwroot

# Use Node.js version specified in App Service settings
echo "Node version: $(node --version)"
echo "NPM version: $(npm --version)"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm ci --prefer-offline --no-audit
fi

# Build the React application if dist doesn't exist
if [ ! -d "dist" ]; then
    echo "Building React application..."
    npm run build
fi

# For Azure App Service, we use the built dist folder
# The web server will serve from dist folder
# No need to start a dev server in production

# Create a simple Node.js server to serve the static files
# This is handled by Azure's default static file serving
# But we can optionally run a Node server:

# node -e "
# const express = require('express');
# const path = require('path');
# const app = express();
# const PORT = process.env.PORT || 3000;
# 
# app.use(express.static(path.join(__dirname, 'dist')));
# app.get('*', (req, res) => {
#   res.sendFile(path.join(__dirname, 'dist/index.html'));
# });
# 
# app.listen(PORT, () => {
#   console.log(\`Frontend running on port \${PORT}\`);
# });
# "

# For simplicity, let web.config (IIS) serve the static files
# This is the recommended approach for Azure App Service on Windows
echo "Frontend build ready. Serving static files via IIS..."
echo "App Service is ready!"
