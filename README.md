# ICC-Champions-Trophy-2025
This is a cricket database built to give information to people on live matches and past matches, particularly of the champions trophy 2025. It gives real time detailed analysis about every single player by analyzing thier strenght zones, thier past performances on the specific grounds, against different pitch conditions.


# 🏆 ICC Champions Trophy 2025 — Analytics Dashboard

A full-stack sports analytics web app for the **ICC Champions Trophy 2025** tournament,
built with **Flask**, **SQLite**, and **Chart.js**.

## Project Members

1. Toib Ujjawal — RA2411030030061
2. [Ujjawal Sharma] — RA2411030030054

## 📁 Project Documents

| Sr | Description                        | Link     |
|----|------------------------------------|----------|
| 1  | Project Code                       | [View](#) |
| 2  | Project Report                     | [View](#) |
| 3  | Final PPT                          | [View](#) |
| 4  | RA2411030030061_Certificate         | [View](#) |
| 5  | RA2411030030054_Certificate         | [View](#) |
| 6  | RA2411030030061_CourseReport        | [View](#) |
| 7  | RA2411030030054_CourseReport        | [View](#) |

## Features

| Tab | Description |
|-----|-------------|
| 📊 **Overview** | Tournament summary — runs, wickets, sixes, champion, top scorer & bowler |
| 🏅 **Standings** | Group A & B tables with captain, coach, and wicket-keeper |
| 🏟️ **Matches** | All 15 matches; click any for innings breakdown, partnerships & performers |
| 👤 **Players** | Phase splits, wicket types, handedness, and match-by-match form chart |
| 📈 **Analytics** | Toss impact chart, wicket type doughnut, handedness bar chart |
| ⚡ **Phase Analysis** | PP / middle / death overs batting & bowling leaderboards |
| 🌍 **Grounds** | Venue stats — avg score, bat/field win rates, pitch type |
| 🤝 **Partnerships** | Top 10 batting stands with match context |
| ⚔️ **Head-to-Head** | Choose any two teams and view their full head-to-head history |
| 📡 **Live** | Real-time scores via Cricbuzz API (RapidAPI) |
| 🔐 **Admin Panel** | Login-protected panel to add/update matches, players, and stats |

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3 + Flask |
| **Database** | SQLite 3 |
| **Frontend** | HTML5 + Vanilla JavaScript |
| **Charts** | Chart.js |
| **External APIs** | CricketData.org · Cricbuzz (RapidAPI) · ESPNcricinfo (RapidAPI) |

## Quick Setup

### 1. Prerequisites
- Python 3.8+
- pip

### 2. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/ct25-dashboard.git
cd ct25-dashboard
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys
```bash
cp config.example.py config.py
```

Edit `config.py` and fill in your keys:

| Key | Where to Get It |
|-----|-----------------|
| `CRICDATA_KEY` | [cricketdata.org/member.aspx](https://cricketdata.org/member.aspx) — free, 100 hits/day |
| `RAPIDAPI_KEY` | [rapidapi.com](https://rapidapi.com) — free account → API Key |

RapidAPI free tiers needed:
- **Cricbuzz Cricket** by Cricbuzz — 200 hits/month
- **espncricinfo API** by Matheus — free tier available

### 5. Initialize the Database
```bash
python init_db.py
```
Seeds 8 teams, ~30 players, 15 matches, 30 innings, partnerships, and standings.

### 6. Run the App
```bash
python app.py
```
Open **http://localhost:5000** in your browser.

> **Windows:** Double-click `run.bat` to auto-initialize and start the server.

## Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| **Admin** | `toib` | `toib123` |

> ⚠️ Change these in `config.py` before sharing or deploying.

## Project Structure

```
ct25-dashboard/
├── app.py                 # Flask server with all API routes
├── db.py                  # SQLite helpers (query + execute)
├── api_fetcher.py         # External API calls + TTL cache
├── init_db.py             # DB schema and seed data (run once)
├── config.py              # API keys & admin password (DO NOT COMMIT)
├── config.example.py      # Template — copy to config.py
├── requirements.txt       # Python dependencies
├── run.bat                # Windows one-click launcher
└── templates/
    ├── index.html         # Main dashboard (10 tabs)
    ├── admin.html         # Admin control panel
    └── login.html         # Admin login page
```

## Database Schema

**10 tables · 6 SQL views**

### Tables

| Table | Key Columns |
|-------|-------------|
| `STADIUM` | stadium_name PK, city, capacity, ends, pitch_type |
| `TEAM` | team_id PK, group_name, no_of_wins, no_of_loses |
| `PLAYER` | 35 columns — aggregates, phase splits, wicket breakdown, vs-handedness |
| `MATCHES` | match_id PK, toss_winner, winner, win_type, stadium_name FK |
| `INNINGS` | match_id FK, pp/mid/death runs & wickets per innings |
| `PLAYER_MATCH_STATS` | per-player per-match batting + bowling figures |
| `PARTNERSHIP` | player1_id FK, player2_id FK, runs, balls, wicket_no |
| `CAPTAIN` | team_id FK, captain_name |
| `COACH` | team_id FK, coach_name |
| `WICKET_KEEPER` | team_id FK, wk_name |
| `api_cache` | cache_key PK, data JSON, fetched_at timestamp |

### SQL Views

| View | Purpose |
|------|---------|
| `vw_TopRunScorers` | Ranked batters by total runs |
| `vw_TopWicketTakers` | Ranked bowlers with economy and best figures |
| `vw_TossImpact` | Win rates by toss decision |
| `vw_GroundStats` | Per-venue averages and win rates |
| `vw_PhaseStats` | Per-player phase-wise strike rates |
| `vw_PlayerMatchForm` | Match-by-match form per player |

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/summary` | Tournament overview |
| GET | `/api/standings` | Group standings |
| GET | `/api/matches` | All 15 matches |
| GET | `/api/match/<id>` | Innings, partnerships & performers |
| GET | `/api/player/<id>` | Player profile, form, partnerships |
| GET | `/api/top_batters` | Top 10 run scorers |
| GET | `/api/top_bowlers` | Top 10 wicket takers |
| GET | `/api/phase_stats` | Phase-wise leaderboard |
| GET | `/api/ground_stats` | Venue stats |
| GET | `/api/best_partnerships` | Top 10 batting stands |
| GET | `/api/head_to_head?t1=X&t2=Y` | Team vs. team history |
| GET | `/api/live` | Live scores (Cricbuzz → CricketData fallback) |
| GET | `/api/icc_standings` | ICC ODI rankings |
| POST | `/api/add_match` *(admin)* | Add or update a match |
| POST | `/api/add_player` *(admin)* | Add or update a player |
| POST | `/api/update_player` *(admin)* | Overwrite all player stats |
| POST | `/api/add_player_stats` *(admin)* | Add match-level stats |

## GitHub Safety

Ensure `.gitignore` contains:
```
champions_trophy.db
config.py
__pycache__/
*.pyc
```
> Never commit `config.py` — only `config.example.py`.

---

*Toib, Ujjawal · SRM Institute of Science and Technology, Delhi NCR · 4th Semester DBMS Project · 2025*
