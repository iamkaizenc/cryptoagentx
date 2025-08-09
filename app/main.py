import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import tweepy
from app.storage.supabase_client import get_client

X_CLIENT_ID = os.getenv("X_CLIENT_ID")
X_CLIENT_SECRET = os.getenv("X_CLIENT_SECRET")
X_CALLBACK_URL = os.getenv("X_CALLBACK_URL")
X_SCOPES = (os.getenv("X_SCOPES") or "tweet.read tweet.write users.read offline.access").split()

app = FastAPI()

def oauth2_handler():
    if not (X_CLIENT_ID and X_CALLBACK_URL):
        raise RuntimeError("Missing X_CLIENT_ID or X_CALLBACK_URL")
    return tweepy.OAuth2UserHandler(
        client_id=X_CLIENT_ID,
        redirect_uri=X_CALLBACK_URL,
        scope=X_SCOPES,
        client_secret=X_CLIENT_SECRET,  # confidential client
    )

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/twitter/oauth2/start")
def start():
    handler = oauth2_handler()
    url = handler.get_authorization_url()
    return {"auth_url": url}

class ExchangePayload(BaseModel):
    code: str
    state: Optional[str] = None

@app.post("/twitter/oauth2/exchange")
def exchange(payload: ExchangePayload):
    handler = oauth2_handler()
    try:
        token = handler.fetch_token(code=payload.code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"exchange_failed: {e}")

    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")

    # fetch user id
    client = tweepy.Client(access_token=access_token)
    me = client.get_me()
    account_id = str(me.data.id) if me and me.data else "unknown"

    # store in supabase
    sb = get_client()
    data = {
        "provider": "twitter",
        "account_id": account_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "scope": " ".join(X_SCOPES),
    }
    sb.table("oauth_tokens").insert(data).execute()
    return {"ok": True, "account_id": account_id}

class RefreshPayload(BaseModel):
    account_id: str

@app.post("/twitter/oauth2/refresh")
def refresh(p: RefreshPayload):
    sb = get_client()
    res = sb.table("oauth_tokens").select("*").eq("provider","twitter").eq("account_id", p.account_id).order("created_at", desc=True).limit(1).execute()
    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="no_token")

    refresh_token = rows[0].get("refresh_token")
    handler = oauth2_handler()
    try:
        new_tok = handler.refresh_token(refresh_token=refresh_token)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"refresh_failed: {e}")

    access_token = new_tok.get("access_token")
    new_refresh = new_tok.get("refresh_token", refresh_token)

    sb.table("oauth_tokens").insert({
        "provider": "twitter",
        "account_id": p.account_id,
        "access_token": access_token,
        "refresh_token": new_refresh,
        "scope": " ".join(X_SCOPES),
    }).execute()
    return {"ok": True}

class TweetPayload(BaseModel):
    text: str
    account_id: Optional[str] = None

@app.post("/tweet")
def tweet(p: TweetPayload):
    sb = get_client()
    if p.account_id:
        res = sb.table("oauth_tokens").select("*").eq("provider","twitter").eq("account_id", p.account_id).order("created_at", desc=True).limit(1).execute()
    else:
        res = sb.table("oauth_tokens").select("*").eq("provider","twitter").order("created_at", desc=True).limit(1).execute()
    rows = res.data or []
    if not rows:
        raise HTTPException(status_code=404, detail="no_token")
    access_token = rows[0]["access_token"]
    client = tweepy.Client(access_token=access_token)
    try:
        r = client.create_tweet(text=p.text)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"tweet_failed: {e}")
    return {"ok": True, "id": str(r.data.get("id"))}
