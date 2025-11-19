# GeoServer public endpoint via ngrok

Steps:

1) Create (or list) the Cloud Endpoint in ngrok (needs NGROK_API_KEY):

- Set API key for this session:
  $env:NGROK_API_KEY = "<your-ngrok-api-key>"

- Create endpoint for your reserved domain:
  ./scripts/create_geoserver_endpoint.ps1 -Domain agriweb-prod.ngrok-free.app

- List endpoints:
  ./scripts/create_geoserver_endpoint.ps1 -List

- Delete endpoint bound to the domain:
  ./scripts/create_geoserver_endpoint.ps1 -Domain agriweb-prod.ngrok-free.app -Delete

2) Start the local tunnel to GeoServer (authtoken must be configured):

- One-off in foreground:
  ./scripts/start_ngrok_geoserver.ps1 -Domain agriweb-prod.ngrok-free.app -LocalPort 8080

- Background:
  ./scripts/start_ngrok_geoserver.ps1 -Domain agriweb-prod.ngrok-free.app -LocalPort 8080 -Background

This sets GEOSERVER_TUNNEL_URL to https://agriweb-prod.ngrok-free.app/geoserver in your current session.

3) Restart the Flask app to pick up env var:

- Use VS Code task: Restart Flask app (run_app.py)

If your app uses GEOSERVER_TUNNEL_URL (or hard-coded fallback), it will call GeoServer through the ngrok endpoint.

Troubleshooting:
- Ensure the domain agriweb-prod.ngrok-free.app is reserved on your ngrok account.
- Make sure your plan supports Cloud Endpoints and custom domains.
- Verify GeoServer listens on http://localhost:8080.
- Check ngrok dashboard for active endpoints.
