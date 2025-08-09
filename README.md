# cryptoagentx (Render-ready)

FastAPI service for X (Twitter) OAuth2 + Supabase token storage + tweet publishing.

## Endpoints
- GET `/health` — health check
- GET `/twitter/oauth2/start` — returns `{ auth_url }` to start OAuth2
- POST `/twitter/oauth2/exchange` — body `{ "code": "...", "state": "..." }`, stores tokens in Supabase
- POST `/twitter/oauth2/refresh` — body `{ "account_id": "..." }`, refreshes token, stores new row
- POST `/tweet` — body `{ "text": "...", "account_id": "optional" }`, posts a tweet using latest token

## Environment variables (set on Render)
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- X_CLIENT_ID
- X_CLIENT_SECRET
- X_CALLBACK_URL
- X_SCOPES (default: "tweet.read tweet.write users.read offline.access")

Deploy with `render.yaml` as a Docker web service.
