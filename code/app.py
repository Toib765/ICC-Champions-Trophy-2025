from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from flask_cors import CORS
from db import query, execute
from api_fetcher import (get_current_matches, get_cricbuzz_live,
                         get_cricbuzz_scorecard, get_icc_standings,
                         get_player_details, search_players, get_match_scorecard)
import config, os
import daa_algos

app = Flask(__name__)
CORS(app)
app.secret_key = config.SECRET_KEY

# Initialize Global Trie for Autocomplete
player_trie = daa_algos.PlayerTrie()
try:
    players_data = query("SELECT player_id, player_name, country_name FROM PLAYER JOIN TEAM ON TEAM.team_id=PLAYER.team_id")
    if players_data:
        for p in players_data:
            player_trie.insert({"type": "Player", "name": p['player_name'], "desc": p['country_name'], "id": p['player_id']})
except Exception as e:
    print("Warning: Could not initialize Trie. DB might not exist yet.")

# ── AUTH ───────────────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username']==config.ADMIN_USER and request.form['password']==config.ADMIN_PASS:
            session['logged_in'] = True
            return redirect(url_for('admin'))
        error = 'Wrong credentials'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/admin')
def admin():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('admin.html')

# ── PAGES ──────────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('index.html')

# ── CORE DB APIS ───────────────────────────────────────────────────────────────
@app.route('/api/summary')
def summary():
    total_matches = query("SELECT COUNT(*) AS c FROM MATCHES", one=True)
    total_runs    = query("SELECT COALESCE(SUM(no_of_totalruns),0) AS c FROM PLAYER", one=True)
    total_wickets = query("SELECT COALESCE(SUM(no_of_wickets),0) AS c FROM PLAYER", one=True)
    total_sixes   = query("SELECT COALESCE(SUM(sixes),0) AS c FROM PLAYER_MATCH_STATS", one=True)
    top_scorer    = query("SELECT player_name,no_of_totalruns FROM PLAYER ORDER BY no_of_totalruns DESC LIMIT 1", one=True)
    top_bowler    = query("SELECT player_name,no_of_wickets FROM PLAYER WHERE no_of_wickets>0 ORDER BY no_of_wickets DESC LIMIT 1", one=True)
    champion      = query("SELECT winner FROM MATCHES WHERE match_stage='Final' LIMIT 1", one=True)
    highest_part  = query("SELECT MAX(runs) AS c FROM PARTNERSHIP", one=True)
    return jsonify({
        "total_matches":  total_matches['c'] if total_matches else 0,
        "total_runs":     int(total_runs['c']) if total_runs else 0,
        "total_wickets":  int(total_wickets['c']) if total_wickets else 0,
        "total_sixes":    int(total_sixes['c']) if total_sixes else 0,
        "top_scorer":     top_scorer or {},
        "top_bowler":     top_bowler or {},
        "champion":       champion['winner'] if champion else "TBD",
        "highest_partnership": highest_part['c'] if highest_part else 0
    })

@app.route('/api/standings')
def standings():
    rows = query("""
        SELECT t.team_id, t.team_name, t.country_name, t.group_name, t.team_rank,
               t.no_of_wins, t.no_of_loses, t.no_of_no_results, t.total_matches,
               COALESCE(cap.captain_name,'') AS captain,
               COALESCE(c.coach_name,'') AS coach,
               COALESCE(wk.wk_name,'') AS wicket_keeper
        FROM TEAM t
        LEFT JOIN CAPTAIN cap ON cap.team_id=t.team_id
        LEFT JOIN COACH c     ON c.team_id=t.team_id
        LEFT JOIN WICKET_KEEPER wk ON wk.team_id=t.team_id
        ORDER BY t.group_name, t.no_of_wins DESC
    """)
    return jsonify(rows)

@app.route('/api/matches')
def matches():
    return jsonify(query("SELECT * FROM MATCHES ORDER BY match_date ASC") or [])

@app.route('/api/match/<match_id>')
def match_detail(match_id):
    match   = query("SELECT * FROM MATCHES WHERE match_id=?", (match_id,), one=True)
    innings = query("SELECT * FROM INNINGS WHERE match_id=? ORDER BY innings_no", (match_id,))
    parts   = query("""
        SELECT pt.*, p1.player_name AS p1_name, p2.player_name AS p2_name
        FROM PARTNERSHIP pt
        JOIN PLAYER p1 ON p1.player_id=pt.player1_id
        JOIN PLAYER p2 ON p2.player_id=pt.player2_id
        WHERE pt.match_id=? ORDER BY wicket_no
    """, (match_id,))
    performers = query("""
        SELECT pms.*, p.player_name, t.country_name, t.team_name
        FROM PLAYER_MATCH_STATS pms
        JOIN PLAYER p ON p.player_id=pms.player_id
        JOIN TEAM t ON t.team_id=p.team_id
        WHERE pms.match_id=?
        ORDER BY pms.runs_scored DESC
    """, (match_id,))
    return jsonify({"match": match, "innings": innings, "partnerships": parts, "performers": performers})

@app.route('/api/teams')
def teams():
    return jsonify(query("SELECT * FROM TEAM ORDER BY group_name, no_of_wins DESC"))

@app.route('/api/team_players/<team_id>')
def team_players(team_id):
    return jsonify(query("""
        SELECT p.*, t.country_name FROM PLAYER p
        JOIN TEAM t ON t.team_id=p.team_id
        WHERE p.team_id=? ORDER BY p.no_of_totalruns DESC
    """, (team_id,)))

@app.route('/api/team_journey/<country>')
def team_journey(country):
    return jsonify(query(
        "SELECT * FROM MATCHES WHERE team_1_name=? OR team_2_name=? ORDER BY match_date",
        (country, country)
    ) or [])

@app.route('/api/top_batters')
def top_batters():
    return jsonify(query("SELECT * FROM vw_TopRunScorers LIMIT 10"))

@app.route('/api/top_bowlers')
def top_bowlers():
    return jsonify(query("SELECT * FROM vw_TopWicketTakers LIMIT 10"))

@app.route('/api/toss_impact')
def toss_impact():
    return jsonify(query("SELECT * FROM vw_TossImpact") or [])

@app.route('/api/ground_stats')
def ground_stats():
    return jsonify(query("SELECT * FROM vw_GroundStats") or [])

@app.route('/api/phase_stats')
def phase_stats():
    return jsonify(query("SELECT * FROM vw_PhaseStats LIMIT 15") or [])

@app.route('/api/head_to_head')
def head_to_head():
    t1 = request.args.get('t1','')
    t2 = request.args.get('t2','')
    rows = query("""
        SELECT * FROM MATCHES
        WHERE (team_1_name=? AND team_2_name=?) OR (team_1_name=? AND team_2_name=?)
        ORDER BY match_date
    """, (t1,t2,t2,t1))
    return jsonify(rows or [])

@app.route('/api/opponents/<team_name>')
def get_opponents(team_name):
    # Fetch all distinct teams that team_name has played against
    rows = query("""
        SELECT DISTINCT team_2_name AS opponent FROM MATCHES WHERE team_1_name = ?
        UNION
        SELECT DISTINCT team_1_name AS opponent FROM MATCHES WHERE team_2_name = ?
    """, (team_name, team_name))
    return jsonify([r['opponent'] for r in rows] if rows else [])

@app.route('/api/player/<player_id>')
def player_profile(player_id):
    player = query("""
        SELECT p.*, t.country_name, t.team_name,
               COALESCE(cap.captain_name,'') AS is_captain
        FROM PLAYER p JOIN TEAM t ON t.team_id=p.team_id
        LEFT JOIN CAPTAIN cap ON cap.team_id=p.team_id AND cap.captain_name=p.player_name
        WHERE p.player_id=?
    """, (player_id,), one=True)
    form = query("SELECT * FROM vw_PlayerMatchForm WHERE player_id=?", (player_id,))
    parts = query("""
        SELECT pt.*, m.match_date, m.match_stage,
               CASE WHEN pt.player1_id=? THEN p2.player_name ELSE p1.player_name END AS partner
        FROM PARTNERSHIP pt
        JOIN PLAYER p1 ON p1.player_id=pt.player1_id
        JOIN PLAYER p2 ON p2.player_id=pt.player2_id
        JOIN MATCHES m ON m.match_id=pt.match_id
        WHERE pt.player1_id=? OR pt.player2_id=?
        ORDER BY pt.runs DESC LIMIT 5
    """, (player_id, player_id, player_id))
    return jsonify({"player": player, "form": form, "partnerships": parts})

@app.route('/api/stadiums')
def stadiums():
    return jsonify(query("SELECT * FROM STADIUM"))

@app.route('/api/innings_summary')
def innings_summary():
    """Tournament-wide phase analysis across all innings"""
    rows = query("""
        SELECT batting_team,
               SUM(pp_runs) AS total_pp_runs, SUM(pp_wickets) AS total_pp_wkts,
               SUM(mid_runs) AS total_mid_runs, SUM(mid_wickets) AS total_mid_wkts,
               SUM(death_runs) AS total_death_runs, SUM(death_wickets) AS total_death_wkts,
               AVG(total_runs) AS avg_score, MAX(total_runs) AS highest, MIN(total_runs) AS lowest,
               COUNT(*) AS innings_count
        FROM INNINGS
        GROUP BY batting_team ORDER BY avg_score DESC
    """)
    return jsonify(rows or [])

@app.route('/api/best_partnerships')
def best_partnerships():
    rows = query("""
        SELECT pt.*, m.match_date, m.match_stage,
               p1.player_name AS p1_name, p2.player_name AS p2_name,
               t.country_name AS team
        FROM PARTNERSHIP pt
        JOIN PLAYER p1 ON p1.player_id=pt.player1_id
        JOIN PLAYER p2 ON p2.player_id=pt.player2_id
        JOIN MATCHES m ON m.match_id=pt.match_id
        JOIN TEAM t ON t.country_name=pt.batting_team
        ORDER BY pt.runs DESC LIMIT 10
    """)
    return jsonify(rows or [])

# ── DAA LAB APIS ───────────────────────────────────────────────────────────────
def get_fantasy_players():
    players_db = query("""
        SELECT p.player_id, p.player_name, p.player_role, t.country_name, 
               p.no_of_totalruns, p.no_of_wickets, p.batting_average
        FROM PLAYER p JOIN TEAM t ON t.team_id=p.team_id
        WHERE p.no_of_totalruns > 0 OR p.no_of_wickets > 0
    """)
    res = []
    if not players_db: return res
    for p in players_db:
        val = p['no_of_totalruns'] + (p['no_of_wickets'] * 25)
        avg = p['batting_average'] or 0
        cost = 7.0 + (min(avg, 50) / 50.0) * 3.0
        if p['no_of_wickets'] > 10: cost += 1.0
        cost = round(min(cost, 11.0), 1)
        r = p['player_role'] or ''
        role = 'Bowler' if 'Bowler' in r else 'WKAR' if 'All-Rounder' in r or 'WK' in r else 'Batter'
        
        res.append({
            "id": p['player_id'],
            "name": p['player_name'],
            "team": p['country_name'],
            "role": role,
            "cost": cost,
            "value": val
        })
    return res

@app.route('/api/daa/fantasy_pool')
def fantasy_pool():
    return jsonify(get_fantasy_players())

@app.route('/api/daa/fantasy_suggest', methods=['POST'])
def fantasy_suggest():
    d = request.json or {}
    locked_ids = d.get('locked_ids', [])
    total_budget = float(d.get('budget', 100.0))
    
    all_p = get_fantasy_players()
    locked_players = [p for p in all_p if p['id'] in locked_ids]
    
    locked_bat = sum(1 for p in locked_players if p['role'] == 'Batter')
    locked_bowl = sum(1 for p in locked_players if p['role'] == 'Bowler')
    locked_wkar = sum(1 for p in locked_players if p['role'] == 'WKAR')
    
    rem_budget = round(total_budget - sum(p['cost'] for p in locked_players), 1)
    
    req_bat = max(0, 5 - locked_bat)
    req_bowl = max(0, 5 - locked_bowl)
    req_wkar = max(0, 1 - locked_wkar)
    
    if req_bat == 0 and req_bowl == 0 and req_wkar == 0:
        return jsonify({"suggested": [], "locked": locked_players, "max_value": sum(p['value'] for p in locked_players)})
        
    available_bat = [p for p in all_p if p['id'] not in locked_ids and p['role'] == 'Batter']
    available_bowl = [p for p in all_p if p['id'] not in locked_ids and p['role'] == 'Bowler']
    available_wkar = [p for p in all_p if p['id'] not in locked_ids and p['role'] == 'WKAR']
    
    res = daa_algos.constrained_knapsack_fantasy(available_bat, available_bowl, available_wkar, req_bat, req_bowl, req_wkar, rem_budget)
    
    if "error" in res:
        return jsonify(res), 400
        
    return jsonify({
        "suggested": res["team"],
        "locked": locked_players,
        "max_value": res["max_value"] + sum(p['value'] for p in locked_players),
        "rem_budget": rem_budget - sum(p['cost'] for p in res["team"])
    })

@app.route('/api/daa/peak_phase/<player_id>')
def daa_peak_phase(player_id):
    # Fetch chronological runs scored by player in all their matches
    stats = query("""
        SELECT m.match_date, pms.runs_scored, pms.balls_faced
        FROM PLAYER_MATCH_STATS pms
        JOIN MATCHES m ON m.match_id = pms.match_id
        WHERE pms.player_id = ?
        ORDER BY m.match_date ASC
    """, (player_id,))
    
    if not stats:
        return jsonify({"max_sum": 0, "start": -1, "end": -1, "details": []})
        
    runs_array = [s['runs_scored'] for s in stats]
    peak = daa_algos.max_subarray_peak(runs_array)
    
    # Extract the specific phase
    phase_details = []
    if peak['start'] != -1 and peak['end'] != -1:
        phase_details = stats[peak['start']:peak['end']+1]
        
    return jsonify({
        "max_runs": peak['max_sum'],
        "start_idx": peak['start'],
        "end_idx": peak['end'],
        "phase_matches": phase_details,
        "all_runs": runs_array
    })

@app.route('/api/dbms/moving_average/<player_id>')
def dbms_moving_average(player_id):
    # Fetch 5-match moving average using Window Functions
    ma_data = query("""
        SELECT match_date, runs_scored, moving_avg_5
        FROM vw_MovingAverage
        WHERE player_id = ?
        ORDER BY match_date ASC
    """, (player_id,))
    return jsonify(ma_data or [])

@app.route('/api/daa/search')
def daa_search():
    q = request.args.get('q', '').strip()
    if not q: return jsonify([])
    
    # Fetch all players and teams to search in-memory using Rabin-Karp
    players = query("SELECT player_id, player_name, country_name FROM PLAYER JOIN TEAM ON TEAM.team_id=PLAYER.team_id")
    results = []
    
    for p in players:
        # Search in player name
        if daa_algos.rabin_karp_search(p['player_name'], q):
            results.append({"type": "Player", "name": p['player_name'], "desc": p['country_name'], "id": p['player_id']})
        # Search in team name
        elif daa_algos.rabin_karp_search(p['country_name'], q):
            results.append({"type": "Player", "name": p['player_name'], "desc": p['country_name'], "id": p['player_id']})
            
    return jsonify(results[:15]) # Return top 15 matches

@app.route('/api/daa/autocomplete')
def daa_autocomplete():
    q = request.args.get('q', '').strip()
    if not q: return jsonify([])
    # O(M) time complexity Trie lookup
    results = player_trie.search_prefix(q)
    return jsonify(results)

@app.route('/api/daa/shortest_path')
def daa_shortest_path():
    p1 = request.args.get('p1')
    p2 = request.args.get('p2')
    if not p1 or not p2: return jsonify({"error": "Missing players"})
    
    partnerships = query("SELECT player1_id, player2_id FROM PARTNERSHIP")
    players = query("SELECT player_id, player_name FROM PLAYER")
    p_dict = {p['player_id']: p['player_name'] for p in players}
    
    graph = daa_algos.build_player_graph(partnerships, p_dict)
    path = daa_algos.shortest_path_bfs(graph, p1, p2)
    
    if not path:
        return jsonify({"path": [], "names": [], "found": False})
        
    names = [p_dict.get(pid, pid) for pid in path]
    return jsonify({"path": path, "names": names, "found": True})

@app.route('/api/daa/impact_sort')
def daa_impact_sort():
    # Calculate a complex metric on the fly and use Custom Merge Sort
    players_db = query("""
        SELECT p.*, t.country_name 
        FROM PLAYER p JOIN TEAM t ON t.team_id=p.team_id
    """)
    if not players_db: return jsonify([])
    
    players_list = []
    for p in players_db:
        p_dict = dict(p)
        # Complex formula: (Runs * SR / 100) + (Wickets * 25 * (120/max(Economy,1)))
        bat_impact = (p_dict['no_of_totalruns'] * p_dict['strike_rate']) / 100.0
        econ = p_dict['economy'] if p_dict['economy'] > 0 else 120 # penalty for no bowl
        bowl_impact = (p_dict['no_of_wickets'] * 25) * (120 / econ) if p_dict['no_of_wickets'] > 0 else 0
        
        p_dict['impact_score'] = round(bat_impact + bowl_impact, 2)
        players_list.append(p_dict)
        
    # Use DAA Merge Sort
    sorted_players = daa_algos.merge_sort_impact(players_list, key='impact_score', reverse=True)
    return jsonify(sorted_players[:20]) # Top 20 most impactful

# ── LIVE / EXTERNAL APIs ───────────────────────────────────────────────────────
@app.route('/api/live')
def live():
    # Try Cricbuzz first, fall back to CricketData.org
    cb = get_cricbuzz_live()
    if isinstance(cb, dict) and "typeMatches" in cb:
        return jsonify({"source": "cricbuzz", "data": cb})
    cd = get_current_matches()
    if isinstance(cd, dict) and "data" in cd and cd.get("status") != "failure":
        return jsonify({"source": "cricketdata", "data": cd})
        
    # Mock fallback data if both APIs fail
    mock_data = [
        {"matchStarted": True, "matchEnded": False, "t1": "India", "t2": "Pakistan", "t1s": "245/4 (42 ov)", "t2s": "", "status": "India elected to bat", "venue": "Lahore"},
        {"matchStarted": True, "matchEnded": False, "t1": "Australia", "t2": "England", "t1s": "310/8 (50 ov)", "t2s": "120/3 (20 ov)", "status": "England need 191 runs", "venue": "Rawalpindi"},
        {"matchStarted": False, "matchEnded": False, "t1": "New Zealand", "t2": "South Africa", "t1s": "", "t2s": "", "status": "Match starts in 2 hours", "venue": "Karachi"}
    ]
    return jsonify({"source": "mock fallback (API error)", "data": mock_data})

@app.route('/api/icc_standings')
def icc_rankings():
    return jsonify(get_icc_standings())

@app.route('/api/espn_player/<player_id>')
def espn_player(player_id):
    return jsonify(get_player_details(player_id))

@app.route('/api/search_player')
def search_player():
    name = request.args.get('q','')
    return jsonify(search_players(name))

@app.route('/api/external_scorecard/<match_id>')
def external_scorecard(match_id):
    return jsonify(get_match_scorecard(match_id))

# ── ADMIN ──────────────────────────────────────────────────────────────────────
def auth():
    if not session.get('logged_in'):
        return jsonify({"error":"Unauthorized"}), 403
    return None

@app.route('/api/add_match', methods=['POST'])
def add_match():
    e = auth()
    if e: return e
    d = request.json
    try:
        execute("""
            INSERT OR REPLACE INTO MATCHES
            (match_id,match_date,match_stage,team_1_name,team_2_name,
             toss_winner,toss_decision,winner,loser,win_margin,win_type,
             man_of_the_match,stadium_name,team_1_score,team_2_score,match_notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (d['match_id'],d['match_date'],d['match_stage'],d['team_1'],d['team_2'],
              d.get('toss_winner'),d.get('toss_decision'),d.get('winner'),
              d.get('loser'),d.get('margin'),d.get('win_type'),d.get('mom'),
              d.get('stadium'),d.get('t1_score'),d.get('t2_score'),d.get('notes')))
        w=d.get('winner'); l=d.get('loser')
        if w and l and w!='No Result':
            execute("UPDATE TEAM SET no_of_wins=no_of_wins+1,total_matches=total_matches+1 WHERE team_name=?",(w,))
            execute("UPDATE TEAM SET no_of_loses=no_of_loses+1,total_matches=total_matches+1 WHERE team_name=?",(l,))
        return jsonify({"status":"ok"})
    except Exception as ex:
        return jsonify({"error":str(ex)}), 400

@app.route('/api/add_team', methods=['POST'])
def add_team():
    e = auth()
    if e: return e
    d = request.json
    try:
        execute("""
            INSERT OR REPLACE INTO TEAM
            (team_id, team_name, country_name, team_rank, group_name)
            VALUES (?, ?, ?, ?, ?)
        """, (d['team_id'], d['team_name'], d['country_name'], d.get('team_rank'), d.get('group_name')))
        return jsonify({"status":"ok"})
    except Exception as ex:
        return jsonify({"error":str(ex)}), 400

@app.route('/api/sync', methods=['POST'])
def sync():
    e = auth()
    if e: return e
    # Placeholder for actual sync logic
    return jsonify({"status": "ok", "synced_matches": 0})

@app.route('/api/add_player', methods=['POST'])
def add_player():
    e = auth()
    if e: return e
    d = request.json
    try:
        execute("""
            INSERT OR REPLACE INTO PLAYER
            (player_id,player_name,team_id,batting_style,bowling_style,player_role,
             batting_average,strike_rate,no_of_totalruns,no_of_50s,no_of_100s,highest_score,
             no_of_wickets,economy,bowling_average,best_bowling)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (d['player_id'],d['player_name'],d['team_id'],d.get('batting_style',''),
              d.get('bowling_style',''),d.get('role',''),
              d.get('bat_avg',0),d.get('sr',0),d.get('runs',0),
              d.get('fifties',0),d.get('hundreds',0),d.get('hs',0),
              d.get('wickets',0),d.get('economy',0),d.get('bowl_avg',0),d.get('best','0/0')))
        return jsonify({"status":"ok"})
    except Exception as ex:
        return jsonify({"error":str(ex)}), 400

@app.route('/api/add_player_stats', methods=['POST'])
def add_player_stats():
    """Add per-match stats for a player"""
    e = auth()
    if e: return e
    d = request.json
    try:
        execute("""
            INSERT OR REPLACE INTO PLAYER_MATCH_STATS
            (match_id,player_id,team_id,runs_scored,balls_faced,fours,sixes,
             dismissal,batting_pos,overs_bowled,runs_given,wickets,maidens)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (d['match_id'],d['player_id'],d['team_id'],
              d.get('runs',0),d.get('balls',0),d.get('fours',0),d.get('sixes',0),
              d.get('dismissal',''),d.get('pos',0),
              d.get('overs',0),d.get('runs_given',0),d.get('wickets',0),d.get('maidens',0)))
        return jsonify({"status":"ok"})
    except Exception as ex:
        return jsonify({"error":str(ex)}), 400

@app.route('/api/update_player', methods=['POST'])
def update_player():
    e = auth()
    if e: return e
    d = request.json
    try:
        execute("""
            UPDATE PLAYER SET
            no_of_totalruns=?,no_of_wickets=?,batting_average=?,strike_rate=?,
            economy=?,bowling_average=?,no_of_50s=?,no_of_100s=?,highest_score=?,
            pp_runs=?,pp_balls=?,mid_runs=?,mid_balls=?,death_runs=?,death_balls=?,
            pp_wkts=?,death_wkts=?,wkt_bowled=?,wkt_caught=?,wkt_lbw=?,
            wkts_vs_rh=?,wkts_vs_lh=?
            WHERE player_id=?
        """, (d.get('runs',0),d.get('wickets',0),d.get('bat_avg',0),d.get('sr',0),
              d.get('economy',0),d.get('bowl_avg',0),d.get('fifties',0),
              d.get('hundreds',0),d.get('hs',0),
              d.get('pp_runs',0),d.get('pp_balls',0),d.get('mid_runs',0),d.get('mid_balls',0),
              d.get('death_runs',0),d.get('death_balls',0),
              d.get('pp_wkts',0),d.get('death_wkts',0),
              d.get('wkt_bowled',0),d.get('wkt_caught',0),d.get('wkt_lbw',0),
              d.get('wkts_vs_rh',0),d.get('wkts_vs_lh',0),d['player_id']))
        return jsonify({"status":"ok"})
    except Exception as ex:
        return jsonify({"error":str(ex)}), 400

if __name__=='__main__':
    if not os.path.exists(config.DB_PATH):
        print("DB not found. Run: python init_db.py")
    app.run(debug=True, port=5000)
