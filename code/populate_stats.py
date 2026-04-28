import sqlite3
import random

db_path = "champions_trophy.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get all matches
cur.execute("SELECT match_id, team_1_name, team_2_name FROM MATCHES")
matches = cur.fetchall()

# Get team names to team_id mapping from TEAM table
cur.execute("SELECT team_name, team_id FROM TEAM")
team_map = dict(cur.fetchall())

# Get all players
cur.execute("SELECT player_id, team_id, player_role FROM PLAYER")
players = cur.fetchall()

# Clear existing stats just in case
cur.execute("DELETE FROM PLAYER_MATCH_STATS")

stats_to_insert = []

for match_id, t1_name, t2_name in matches:
    t1_id = team_map.get(t1_name)
    t2_id = team_map.get(t2_name)
    
    # Find players for these teams
    match_players = [p for p in players if p[1] in (t1_id, t2_id)]
    
    for p_id, p_team, role in match_players:
        runs = random.randint(0, 100) if role in ("Batsman", "Batter", "WK-Batsman") else random.randint(0, 30)
        balls = int(runs * random.uniform(0.7, 1.5))
        fours = runs // 6
        sixes = runs // 15
        wickets = random.randint(0, 3) if role in ("Bowler", "All-Rounder") else 0
        runs_given = wickets * 15 + random.randint(10, 40)
        overs = random.randint(2, 10) if role in ("Bowler", "All-Rounder") else 0
        
        stats_to_insert.append((
            match_id, p_id, p_team, runs, balls, fours, sixes, "", "caught", random.randint(1, 11),
            overs, runs_given, wickets, 0, 0
        ))

cur.executemany("""
    INSERT INTO PLAYER_MATCH_STATS 
    (match_id, player_id, team_id, runs_scored, balls_faced, fours, sixes, dismissed_by, dismissal, batting_pos, overs_bowled, runs_given, wickets, maidens, caught)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", stats_to_insert)

conn.commit()
conn.close()
print(f"Successfully populated {len(stats_to_insert)} rows into PLAYER_MATCH_STATS!")
