import os, tweepy
from supabase import Client
from app.storage.supabase_client import get_client

def _latest_token(account_id: str | None = None):
    sb: Client = get_client()
    if account_id:
        res = sb.table("oauth_tokens").select("*").eq("provider","twitter").eq("account_id", account_id).order("created_at", desc=True).limit(1).execute()
    else:
        res = sb.table("oauth_tokens").select("*").eq("provider","twitter").order("created_at", desc=True).limit(1).execute()
    rows = res.data or []
    if not rows:
        raise RuntimeError("No oauth token found in Supabase. Complete OAuth2 first.")
    return rows[0]

def client_for(account_id: str | None = None) -> tweepy.Client:
    tok = _latest_token(account_id)
    return tweepy.Client(access_token=tok["access_token"])

def publish_now(text: str, account_id: str | None = None):
    client = client_for(account_id)
    resp = client.create_tweet(text=text)
    return {"status":"ok","id": str(resp.data.get("id"))}
