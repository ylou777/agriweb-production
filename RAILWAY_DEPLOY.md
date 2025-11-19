# Railway Deployment Trigger
# Date: 2025-09-10
# This file forces Railway to redeploy the application

DEPLOYMENT_VERSION="2.0.1"
TRIGGER_TIME="2025-09-10T$(Get-Date -Format 'HH:mm:ss')"

# AgriWeb 2.0 Production Deployment
# - Enhanced anti-loop protection
# - GeoServer ngrok tunnel configured
# - Homepage content updated
# - Security fixes applied
# - All variables configured correctly
