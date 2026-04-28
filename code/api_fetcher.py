"""
API Fetcher — CricketData.org + Cricbuzz (RapidAPI) + ESPNcricinfo (RapidAPI)
All results cached in SQLite to save quota.
"""
import requests, json
from datetime import datetime, timedelta
import config
from db import get_conn, execute

BASE_CRICDATA = "https://api.cricapi.com/v1"

# ── CACHE ──────────────────────────────────────────────────────────────────────
import os

CACHE_FILE = "cache/api_cache.json"

def get_cache_db():
    if not os.path.exists("cache"): os.makedirs("cache")
    if not os.path.exists(CACHE_FILE): return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except: return {}

def save_cache_db(db):
    if not os.path.exists("cache"): os.makedirs("cache")
    with open(CACHE_FILE, "w") as f:
        json.dump(db, f)

def cache_set(key, data, ttl_minutes=30):
    db = get_cache_db()
    db[key] = {
        "data": data,
        "fetched_at": datetime.now().isoformat()
    }
    save_cache_db(db)

def cache_get(key, ttl_minutes=30):
    db = get_cache_db()
    if key in db:
        fetched = datetime.fromisoformat(db[key]["fetched_at"])
        if datetime.now() - fetched < timedelta(minutes=ttl_minutes):
            return db[key]["data"]
    return None

# ── CRICKETDATA.ORG ────────────────────────────────────────────────────────────
def cricdata_get(endpoint, params=None):
    p = {"apikey": config.CRICDATA_KEY}
    if params: p.update(params)
    try:
        r = requests.get(f"{BASE_CRICDATA}/{endpoint}", params=p, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_current_matches():
    cached = cache_get("live_matches", 5)
    if cached: return cached
    data = cricdata_get("currentMatches", {"offset": 0})
    if "error" not in data: cache_set("live_matches", data, 5)
    return data

# ── RAPIDAPI BASE ──────────────────────────────────────────────────────────────
def rapidapi_get(host, path, params=None):
    if "PASTE" in config.RAPIDAPI_KEY:
        return {"error": "RapidAPI key not set in config.py"}
    try:
        headers = {
            "X-RapidAPI-Key":  config.RAPIDAPI_KEY,
            "X-RapidAPI-Host": host
        }
        r = requests.get(f"https://{host}/{path}",
                         headers=headers, params=params or {}, timeout=10)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ── CRICBUZZ (200 hits/month — always cache 24hrs) ─────────────────────────────
def cricbuzz(path, params=None, ttl=1440):
    key = f"cb_{path}_{json.dumps(params or {})}"
    cached = cache_get(key, ttl)
    if cached: return cached
    host = getattr(config, 'CRICBUZZ_HOST', getattr(config, 'RAPIDAPI_HOST', 'cricbuzz-cricket.p.rapidapi.com'))
    data = rapidapi_get(host, path, params)
    if "error" not in data: cache_set(key, data, ttl)
    return data

def get_cricbuzz_live():       return cricbuzz("matches/live", ttl=5)
def get_cricbuzz_recent():     return cricbuzz("matches/recent", ttl=60)
def get_icc_standings():       return cricbuzz("stats/get-icc-standings", {"formatType":"odi"}, ttl=1440)
def get_cricbuzz_scorecard(match_id): return cricbuzz(f"matches/get-scorecard-v2", {"matchId": match_id}, ttl=1440)

# ── ESPNCRICINFO (same RapidAPI key, subscribe free) ──────────────────────────
def espn(path, params=None, ttl=1440):
    key = f"espn_{path}_{json.dumps(params or {})}"
    cached = cache_get(key, ttl)
    if cached: return cached
    host = getattr(config, 'ESPN_HOST', getattr(config, 'RAPIDAPI_HOST', 'cricinfo15.p.rapidapi.com'))
    data = rapidapi_get(host, path, params)
    if "error" not in data: cache_set(key, data, ttl)
    return data

def get_player_details(player_id): return espn("api/v1/cricketinfo/player-details", {"player_id": player_id})
def get_series_stats(series_id):   return espn("api/v1/cricketinfo/seriesStats", {"seriesId": series_id})
def get_series_squads(series_id):  return espn("api/v1/cricketinfo/seriesSquads", {"seriesId": series_id})
def get_match_scorecard(match_id): return espn("api/v1/cricketinfo/matchDetailsFullScorecard", {"matchId": match_id})
def get_ground_details(ground_id): return espn("api/v1/cricketinfo/groundDetails", {"groundId": ground_id})
def search_players(name):          return espn("api/v1/cricketinfo/searchPlayers", {"query": name}, ttl=60)
