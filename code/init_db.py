"""
Run ONCE: python init_db.py
Creates and seeds the full database with rich CT25 data.
"""
import sqlite3, config

conn = sqlite3.connect(config.DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")
cur = conn.cursor()

# Drop everything
for t in ["PARTNERSHIP","PLAYER_MATCH_STATS","INNINGS","UMPIRED_BY","PLAYS",
          "MATCHES","CAPTAIN","COACH","PLAYER","UMPIRE","WICKET_KEEPER",
          "TEAM","STADIUM","api_cache"]:
    cur.execute(f"DROP TABLE IF EXISTS {t}")
for v in ["vw_TopRunScorers","vw_TopWicketTakers","vw_TossImpact",
          "vw_PhaseStats","vw_GroundStats","vw_PlayerMatchForm"]:
    cur.execute(f"DROP VIEW IF EXISTS {v}")

cur.executescript("""

CREATE TABLE STADIUM (
    stadium_name  TEXT PRIMARY KEY,
    city          TEXT,
    country       TEXT,
    capacity      INTEGER,
    ends          TEXT,
    pitch_type    TEXT
);

CREATE TABLE TEAM (
    team_id          TEXT PRIMARY KEY,
    team_rank        INTEGER,
    team_name        TEXT NOT NULL,
    country_name     TEXT,
    group_name       TEXT,
    no_of_wins       INTEGER DEFAULT 0,
    no_of_loses      INTEGER DEFAULT 0,
    no_of_no_results INTEGER DEFAULT 0,
    total_matches    INTEGER DEFAULT 0
);

CREATE TABLE WICKET_KEEPER (
    team_id TEXT REFERENCES TEAM(team_id) ON DELETE CASCADE,
    wk_name TEXT
);

CREATE TABLE UMPIRE (
    umpire_id   TEXT PRIMARY KEY,
    umpire_name TEXT,
    country     TEXT,
    umpire_type TEXT  -- 'on-field' or 'tv'
);

CREATE TABLE PLAYER (
    player_id           TEXT PRIMARY KEY,
    player_name         TEXT NOT NULL,
    team_id             TEXT REFERENCES TEAM(team_id) ON DELETE CASCADE,
    batting_style       TEXT,   -- Right Handed / Left Handed
    bowling_style       TEXT,   -- Right Arm Fast / Left Arm Orthodox etc
    player_role         TEXT,   -- Batsman / Bowler / All-Rounder / WK-Batsman
    -- Tournament aggregate batting
    batting_average     REAL DEFAULT 0,
    strike_rate         REAL DEFAULT 0,
    no_of_totalruns     INTEGER DEFAULT 0,
    no_of_50s           INTEGER DEFAULT 0,
    no_of_100s          INTEGER DEFAULT 0,
    highest_score       INTEGER DEFAULT 0,
    -- Phase batting splits
    pp_runs             INTEGER DEFAULT 0,   -- powerplay (1-10)
    pp_balls            INTEGER DEFAULT 0,
    mid_runs            INTEGER DEFAULT 0,   -- middle (11-40)
    mid_balls           INTEGER DEFAULT 0,
    death_runs          INTEGER DEFAULT 0,   -- death (41-50)
    death_balls         INTEGER DEFAULT 0,
    -- Bowling aggregate
    no_of_wickets       INTEGER DEFAULT 0,
    economy             REAL DEFAULT 0,
    bowling_average     REAL DEFAULT 0,
    bowling_sr          REAL DEFAULT 0,
    best_bowling        TEXT DEFAULT '0/0',
    -- Bowling phase splits
    pp_wkts             INTEGER DEFAULT 0,
    pp_runs_given       INTEGER DEFAULT 0,
    pp_balls_bowled     INTEGER DEFAULT 0,
    death_wkts          INTEGER DEFAULT 0,
    death_runs_given    INTEGER DEFAULT 0,
    death_balls_bowled  INTEGER DEFAULT 0,
    -- Wicket breakdown
    wkt_bowled          INTEGER DEFAULT 0,
    wkt_caught          INTEGER DEFAULT 0,
    wkt_lbw             INTEGER DEFAULT 0,
    wkt_runout          INTEGER DEFAULT 0,
    -- vs batter type
    wkts_vs_rh          INTEGER DEFAULT 0,
    wkts_vs_lh          INTEGER DEFAULT 0
);

CREATE TABLE COACH (
    team_id    TEXT REFERENCES TEAM(team_id) ON DELETE CASCADE,
    coach_name TEXT
);

CREATE TABLE CAPTAIN (
    team_id      TEXT REFERENCES TEAM(team_id) ON DELETE CASCADE,
    captain_name TEXT
);

CREATE TABLE MATCHES (
    match_id         TEXT PRIMARY KEY,
    match_date       TEXT,
    match_stage      TEXT,
    team_1_name      TEXT,
    team_2_name      TEXT,
    toss_winner      TEXT,
    toss_decision    TEXT,
    winner           TEXT,
    loser            TEXT,
    win_margin       TEXT,
    win_type         TEXT,   -- 'runs' or 'wickets'
    man_of_the_match TEXT,
    stadium_name     TEXT REFERENCES STADIUM(stadium_name),
    team_1_score     TEXT,   -- e.g. "245/7"
    team_2_score     TEXT,
    team_1_overs     REAL,
    team_2_overs     REAL,
    match_notes      TEXT    -- any interesting fact
);

CREATE TABLE INNINGS (
    innings_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id      TEXT REFERENCES MATCHES(match_id) ON DELETE CASCADE,
    innings_no    INTEGER,  -- 1 or 2
    batting_team  TEXT,
    bowling_team  TEXT,
    total_runs    INTEGER DEFAULT 0,
    total_wickets INTEGER DEFAULT 0,
    total_overs   REAL DEFAULT 0,
    pp_runs       INTEGER DEFAULT 0,   -- 1-10 overs
    pp_wickets    INTEGER DEFAULT 0,
    mid_runs      INTEGER DEFAULT 0,   -- 11-40 overs
    mid_wickets   INTEGER DEFAULT 0,
    death_runs    INTEGER DEFAULT 0,   -- 41-50 overs
    death_wickets INTEGER DEFAULT 0,
    extras        INTEGER DEFAULT 0,
    highest_over  INTEGER DEFAULT 0,   -- most runs in a single over
    highest_over_runs INTEGER DEFAULT 0
);

CREATE TABLE PLAYER_MATCH_STATS (
    stat_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id     TEXT REFERENCES MATCHES(match_id) ON DELETE CASCADE,
    player_id    TEXT REFERENCES PLAYER(player_id) ON DELETE CASCADE,
    team_id      TEXT,
    -- Batting
    runs_scored  INTEGER DEFAULT 0,
    balls_faced  INTEGER DEFAULT 0,
    fours        INTEGER DEFAULT 0,
    sixes        INTEGER DEFAULT 0,
    dismissed_by TEXT,
    dismissal    TEXT,   -- caught / bowled / lbw / run out / not out
    batting_pos  INTEGER DEFAULT 0,
    -- Bowling
    overs_bowled REAL DEFAULT 0,
    runs_given   INTEGER DEFAULT 0,
    wickets      INTEGER DEFAULT 0,
    maidens      INTEGER DEFAULT 0,
    caught       INTEGER DEFAULT 0,   -- catches taken in field
    UNIQUE(match_id, player_id)
);

CREATE TABLE PARTNERSHIP (
    part_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id     TEXT REFERENCES MATCHES(match_id) ON DELETE CASCADE,
    innings_no   INTEGER,
    batting_team TEXT,
    player1_id   TEXT,
    player2_id   TEXT,
    runs         INTEGER DEFAULT 0,
    balls        INTEGER DEFAULT 0,
    wicket_no    INTEGER   -- this was the Xth wicket partnership
);

CREATE TABLE PLAYS (
    match_id TEXT REFERENCES MATCHES(match_id) ON DELETE CASCADE,
    team_id  TEXT REFERENCES TEAM(team_id)     ON DELETE CASCADE,
    PRIMARY KEY (match_id, team_id)
);

CREATE TABLE UMPIRED_BY (
    match_id  TEXT REFERENCES MATCHES(match_id)  ON DELETE CASCADE,
    umpire_id TEXT REFERENCES UMPIRE(umpire_id)  ON DELETE CASCADE,
    PRIMARY KEY (match_id, umpire_id)
);

CREATE TABLE api_cache (
    cache_key  TEXT PRIMARY KEY,
    data       TEXT,
    fetched_at TEXT
);

-- ── VIEWS ────────────────────────────────────────────────────────────────────

CREATE VIEW vw_TopRunScorers AS
SELECT p.player_name, t.country_name, p.no_of_totalruns AS runs,
       p.batting_average AS avg, p.strike_rate AS sr,
       p.no_of_50s, p.no_of_100s, p.highest_score
FROM PLAYER p JOIN TEAM t ON p.team_id = t.team_id
ORDER BY p.no_of_totalruns DESC;

CREATE VIEW vw_TopWicketTakers AS
SELECT p.player_name, t.country_name, p.no_of_wickets AS wickets,
       p.economy, p.bowling_average AS avg, p.best_bowling,
       p.wkt_bowled, p.wkt_caught, p.wkt_lbw
FROM PLAYER p JOIN TEAM t ON p.team_id = t.team_id
WHERE p.no_of_wickets > 0
ORDER BY p.no_of_wickets DESC, p.economy ASC;

CREATE VIEW vw_TossImpact AS
SELECT
    toss_decision,
    COUNT(*) AS total,
    SUM(CASE WHEN toss_winner = winner THEN 1 ELSE 0 END) AS toss_winner_won,
    SUM(CASE WHEN toss_winner != winner AND winner IS NOT NULL THEN 1 ELSE 0 END) AS toss_winner_lost
FROM MATCHES
WHERE toss_winner IS NOT NULL AND winner IS NOT NULL
GROUP BY toss_decision;

CREATE VIEW vw_GroundStats AS
SELECT
    m.stadium_name,
    s.city,
    COUNT(*) AS matches,
    SUM(CASE WHEN m.toss_decision='Bat' AND m.toss_winner=m.winner THEN 1 ELSE 0 END) AS bat_first_wins,
    SUM(CASE WHEN m.toss_decision='Field' AND m.toss_winner=m.winner THEN 1 ELSE 0 END) AS field_first_wins,
    AVG(i.total_runs) AS avg_score,
    MAX(i.total_runs) AS highest_total,
    MIN(CASE WHEN i.total_wickets=10 THEN i.total_runs END) AS lowest_total
FROM MATCHES m
JOIN STADIUM s ON s.stadium_name = m.stadium_name
JOIN INNINGS i ON i.match_id = m.match_id
GROUP BY m.stadium_name;

CREATE VIEW vw_PhaseStats AS
SELECT
    p.player_name, t.country_name,
    p.pp_runs, p.pp_balls,
    CASE WHEN p.pp_balls > 0 THEN ROUND(p.pp_runs * 100.0 / p.pp_balls, 1) ELSE 0 END AS pp_sr,
    p.mid_runs, p.mid_balls,
    CASE WHEN p.mid_balls > 0 THEN ROUND(p.mid_runs * 100.0 / p.mid_balls, 1) ELSE 0 END AS mid_sr,
    p.death_runs, p.death_balls,
    CASE WHEN p.death_balls > 0 THEN ROUND(p.death_runs * 100.0 / p.death_balls, 1) ELSE 0 END AS death_sr,
    p.no_of_totalruns AS total_runs
FROM PLAYER p JOIN TEAM t ON p.team_id = t.team_id
WHERE p.pp_balls > 0 OR p.mid_balls > 0 OR p.death_balls > 0
ORDER BY p.no_of_totalruns DESC;

CREATE VIEW vw_PlayerMatchForm AS
SELECT
    pms.player_id, p.player_name, t.country_name,
    pms.match_id, m.match_date, m.match_stage,
    CASE WHEN m.team_1_name=t.country_name THEN m.team_2_name ELSE m.team_1_name END AS opponent,
    pms.runs_scored, pms.balls_faced, pms.wickets,
    pms.overs_bowled, pms.runs_given,
    CASE WHEN pms.balls_faced > 0 THEN ROUND(pms.runs_scored*100.0/pms.balls_faced,1) ELSE 0 END AS bat_sr
FROM PLAYER_MATCH_STATS pms
JOIN PLAYER p ON p.player_id = pms.player_id
JOIN TEAM t ON t.team_id = p.team_id
JOIN MATCHES m ON m.match_id = pms.match_id
ORDER BY m.match_date ASC;
""")

# ── SEED DATA ──────────────────────────────────────────────────────────────────

cur.executemany("INSERT INTO STADIUM VALUES (?,?,?,?,?,?)", [
    ('National Stadium Karachi',    'Karachi',    'Pakistan', 55000, 'City End / Sea End',      'Flat, batting-friendly'),
    ('Gaddafi Stadium',             'Lahore',     'Pakistan', 60000, 'Pavilion End / City End', 'Good for batting, some turn'),
    ('Rawalpindi Cricket Stadium',  'Rawalpindi', 'Pakistan', 15000, 'Pavilion End / Main End', 'Slow, favours spin'),
    ('Dubai International Stadium', 'Dubai',      'UAE',      25000, 'North End / South End',   'Slow, low bounce, spin-friendly'),
])

cur.executemany("INSERT INTO TEAM VALUES (?,?,?,?,?,?,?,?,?)", [
    ('IND', 1, 'India',        'India',        'A', 0,0,0,0),
    ('PAK', 8, 'Pakistan',     'Pakistan',     'A', 0,0,0,0),
    ('NZ',  4, 'New Zealand',  'New Zealand',  'A', 0,0,0,0),
    ('BAN', 7, 'Bangladesh',   'Bangladesh',   'A', 0,0,0,0),
    ('AUS', 2, 'Australia',    'Australia',    'B', 0,0,0,0),
    ('ENG', 5, 'England',      'England',      'B', 0,0,0,0),
    ('SA',  6, 'South Africa', 'South Africa', 'B', 0,0,0,0),
    ('AFG', 9, 'Afghanistan',  'Afghanistan',  'B', 0,0,0,0),
])

cur.executemany("INSERT INTO CAPTAIN VALUES (?,?)", [
    ('IND','Rohit Sharma'),('PAK','Mohammad Rizwan'),('NZ','Mitchell Santner'),
    ('BAN','Najmul Hossain Shanto'),('AUS','Pat Cummins'),('ENG','Jos Buttler'),
    ('SA','Temba Bavuma'),('AFG','Hashmatullah Shahidi'),
])

cur.executemany("INSERT INTO COACH VALUES (?,?)", [
    ('IND','Gautam Gambhir'),('PAK','Aaqib Javed'),('NZ','Gary Stead'),
    ('BAN','Phil Simmons'),('AUS','Andrew McDonald'),('ENG','Brendon McCullum'),
    ('SA','Rob Walter'),('AFG','Jonathan Trott'),
])

cur.executemany("INSERT INTO WICKET_KEEPER VALUES (?,?)", [
    ('IND','KL Rahul'),('PAK','Mohammad Rizwan'),('NZ','Tom Latham'),
    ('BAN','Litton Das'),('AUS','Josh Inglis'),('ENG','Jos Buttler'),
    ('SA','Quinton de Kock'),('AFG','Rahmanullah Gurbaz'),
])

# Rich player data — batting_style, bowling_style, role, avg, sr, runs, 50s, 100s, hs,
# pp_runs, pp_balls, mid_runs, mid_balls, death_runs, death_balls,
# wickets, economy, bowl_avg, bowl_sr, best,
# pp_wkts, pp_runs_given, pp_balls_bowled, death_wkts, death_runs_given, death_balls_bowled,
# wkt_bowled, wkt_caught, wkt_lbw, wkt_runout, wkts_vs_rh, wkts_vs_lh
players = [
 # India
 ('IND01','Rohit Sharma',       'IND','Right Handed','Right Arm Medium',      'Batsman',       45.2, 88.5, 320,3,1, 95,  68,44,  192,95,  60,17,  0,0.0,0.0,0.0,'0/0',  0,0,0,0,0,0,  0,0,0,0, 0,0),
 ('IND02','Virat Kohli',        'IND','Right Handed','Right Arm Medium',      'Batsman',       58.3, 92.1, 765,4,2,183,  88,52,  440,152,  237,80,  0,0.0,0.0,0.0,'0/0',  0,0,0,0,0,0,  0,0,0,0, 0,0),
 ('IND03','Shubman Gill',       'IND','Right Handed','Right Arm Off Break',   'Batsman',       44.1, 86.3, 312,2,1,149,  72,43,  195,84,   45,16,  0,0.0,0.0,0.0,'0/0',  0,0,0,0,0,0,  0,0,0,0, 0,0),
 ('IND04','KL Rahul',           'IND','Right Handed','Right Arm Off Break',   'WK-Batsman',    46.7, 80.2, 287,3,0,112,  55,38,  190,98,   42,12,  0,0.0,0.0,0.0,'0/0',  0,0,0,0,0,0,  0,0,0,0, 0,0),
 ('IND05','Hardik Pandya',      'IND','Right Handed','Right Arm Fast Medium', 'All-Rounder',   28.5,110.4, 198,1,0, 87,  48,30,  105,42,   45,21,  12,5.20,24.5,29.8,'3/28', 3,62,72,  4,88,66,  4,6,2,0, 7,5),
 ('IND06','Ravindra Jadeja',    'IND','Left Handed', 'Left Arm Orthodox',     'All-Rounder',   28.1, 78.0, 180,1,0, 62,  32,22,  110,58,   38,18,  15,4.80,23.1,28.8,'3/22', 5,48,60,  3,52,42,  4,9,2,0, 9,6),
 ('IND07','Kuldeep Yadav',      'IND','Left Handed', 'Left Arm Wrist Spin',   'Bowler',        12.3, 65.0,  45,0,0, 32,  18,12,   28,22,    9, 6,  18,4.90,21.4,26.2,'4/35', 6,58,72,  5,44,54,  5,11,2,0,12,6),
 ('IND08','Jasprit Bumrah',     'IND','Right Handed','Right Arm Fast',        'Bowler',         9.5, 70.1,  32,0,0, 20,  9, 8,   18,14,    8, 6,  16,3.80,18.2,22.2,'4/19', 4,32,48,  6,48,54,  6,8,2,0,10,6),
 # Pakistan
 ('PAK01','Babar Azam',         'PAK','Right Handed','Right Arm Off Break',   'Batsman',       52.4, 86.7, 347,3,1,162,  72,44,  215,98,   55,18,  0,0.0,0.0,0.0,'0/0',  0,0,0,0,0,0,  0,0,0,0, 0,0),
 ('PAK02','Mohammad Rizwan',    'PAK','Right Handed','Right Arm Medium',      'WK-Batsman',    48.9, 81.2, 298,2,1,134,  62,38,  178,88,   45,18,  0,0.0,0.0,0.0,'0/0',  0,0,0,0,0,0,  0,0,0,0, 0,0),
 ('PAK03','Fakhar Zaman',       'PAK','Left Handed', 'Right Arm Off Break',   'Batsman',       39.7, 90.1, 256,2,0,118,  58,42,  158,76,   48,22,  0,0.0,0.0,0.0,'0/0',  0,0,0,0,0,0,  0,0,0,0, 0,0),
 ('PAK04','Shaheen Shah Afridi','PAK','Left Handed', 'Left Arm Fast',         'Bowler',         8.2, 55.0,  22,0,0, 12,  5, 6,   14,10,    5, 4,  17,4.50,19.8,24.8,'4/22', 7,56,84,  5,72,66,  6,9,2,0,11,6),
 ('PAK05','Haris Rauf',         'PAK','Right Handed','Right Arm Fast',        'Bowler',         6.8, 60.2,  18,0,0,  9,  4, 6,   12, 9,    4, 4,  12,5.10,24.2,28.8,'3/38', 3,44,54,  5,68,60,  4,6,2,0, 8,4),
 # Australia
 ('AUS01','Travis Head',        'AUS','Left Handed', 'Right Arm Off Break',   'Batsman',       44.2,109.3, 278,2,1,132,  72,48,  158,58,   60,32,  2,5.80,62.0,72.0,'1/18', 0,0,0, 1,22,18,  0,2,0,0, 1,1),
 ('AUS02','David Warner',       'AUS','Left Handed', 'Right Arm Off Break',   'Batsman',       45.6, 95.3, 290,2,1,128,  72,50,  172,82,   62,24,  0,0.0,0.0,0.0,'0/0',  0,0,0,0,0,0,  0,0,0,0, 0,0),
 ('AUS03','Steve Smith',        'AUS','Right Handed','Right Arm Leg Break',   'Batsman',       56.1, 83.5, 312,3,1,158,  72,44,  192,98,   58,22,  3,6.20,48.0,58.8,'1/22', 0,0,0, 1,22,18,  1,2,0,0, 2,1),
 ('AUS04','Pat Cummins',        'AUS','Right Handed','Right Arm Fast',        'Bowler',        16.4, 88.1,  67,0,0, 28,  18,12,   38,22,   18,12,  14,4.60,21.2,28.2,'3/32', 4,42,54,  5,66,60,  5,7,2,0, 9,5),
 ('AUS05','Mitchell Starc',     'AUS','Left Handed', 'Left Arm Fast',         'Bowler',         9.1, 71.0,  28,0,0, 12,  5, 8,   14,10,    8, 6,  15,5.20,24.8,28.8,'4/28', 3,38,48,  6,62,54,  5,8,2,0, 9,6),
 # England
 ('ENG01','Jos Buttler',        'ENG','Right Handed','Right Arm Medium',      'WK-Batsman',    42.3,112.5, 243,2,0,118,  58,42,  138,48,   52,30,  0,0.0,0.0,0.0,'0/0',  0,0,0,0,0,0,  0,0,0,0, 0,0),
 ('ENG02','Joe Root',           'ENG','Right Handed','Right Arm Off Break',   'Batsman',       54.9, 87.2, 318,3,1,152,  68,44,  198,102,  58,22,  4,5.90,42.0,52.8,'2/28', 1,22,24,  1,28,24,  1,2,1,0, 2,2),
 ('ENG03','Ben Stokes',         'ENG','Left Handed', 'Right Arm Fast Medium', 'All-Rounder',   35.7, 96.4, 198,1,0, 88,  52,36,  112,48,   38,22,  11,5.50,28.4,36.0,'3/38', 3,42,48,  4,62,54,  4,5,2,0, 7,4),
 ('ENG04','Jofra Archer',       'ENG','Right Handed','Right Arm Fast',        'Bowler',         9.8, 72.3,  34,0,0, 12,  5, 8,   18,14,    8, 4,  13,4.90,22.8,28.2,'3/42', 4,38,48,  4,52,48,  4,7,2,0, 8,5),
 # New Zealand
 ('NZ01', 'Kane Williamson',    'NZ', 'Right Handed','Right Arm Off Break',   'Batsman',       48.5, 79.3, 289,3,1,142,  72,48,  172,92,   58,22,  2,5.70,58.0,68.8,'1/12', 0,0,0, 1,22,18,  0,1,1,0, 1,1),
 ('NZ02', 'Rachin Ravindra',    'NZ', 'Left Handed', 'Left Arm Orthodox',     'All-Rounder',   38.2, 88.6, 232,2,0,112,  62,42,  138,62,   55,30,  6,5.20,38.0,48.0,'2/28', 2,32,36,  2,38,36,  2,3,1,0, 4,2),
 ('NZ03', 'Trent Boult',        'NZ', 'Right Handed','Left Arm Fast Medium',  'Bowler',         8.7, 64.1,  23,0,0,  8,  4, 8,   12, 8,    5, 4,  14,4.80,21.8,27.2,'4/18', 5,42,60,  5,52,48,  5,7,2,0, 9,5),
 # South Africa
 ('SA01', 'Temba Bavuma',       'SA', 'Right Handed','Right Arm Medium',      'Batsman',       38.4, 75.2, 198,2,0, 88,  58,44,  118,68,   45,22,  0,0.0,0.0,0.0,'0/0',  0,0,0,0,0,0,  0,0,0,0, 0,0),
 ('SA02', 'Quinton de Kock',    'SA', 'Left Handed', 'Right Arm Medium',      'WK-Batsman',    44.1, 98.7, 267,2,1,128,  68,48,  158,68,   52,28,  0,0.0,0.0,0.0,'0/0',  0,0,0,0,0,0,  0,0,0,0, 0,0),
 ('SA03', 'Kagiso Rabada',      'SA', 'Right Handed','Right Arm Fast',        'Bowler',         9.5, 67.2,  30,0,0, 12,  4, 8,   14,10,    6, 4,  16,4.70,21.2,26.8,'4/32', 5,42,60,  6,62,54,  6,8,2,0,10,6),
 # Bangladesh
 ('BAN01','Shakib Al Hasan',    'BAN','Left Handed', 'Left Arm Orthodox',     'All-Rounder',   32.8, 82.5, 187,1,0, 88,  58,38,  112,62,   35,18,  10,4.90,28.8,35.4,'3/28', 4,42,48,  3,48,42,  3,5,2,0, 6,4),
 ('BAN02','Litton Das',         'BAN','Right Handed','Right Arm Off Break',   'WK-Batsman',    36.5, 84.3, 215,1,0, 98,  58,42,  128,72,   35,18,  0,0.0,0.0,0.0,'0/0',  0,0,0,0,0,0,  0,0,0,0, 0,0),
 # Afghanistan
 ('AFG01','Rashid Khan',        'AFG','Right Handed','Right Arm Leg Break',   'Bowler',        16.3, 95.5,  78,0,0, 28,  14,12,   42,28,   12, 8,  19,3.90,18.2,24.2,'5/22', 7,52,78,  6,48,60,  6,11,2,0,13,6),
 ('AFG02','Ibrahim Zadran',     'AFG','Right Handed','Right Arm Off Break',   'Batsman',       35.2, 76.4, 198,1,0, 88,  52,42,  118,68,   30,18,  0,0.0,0.0,0.0,'0/0',  0,0,0,0,0,0,  0,0,0,0, 0,0),
]
cur.executemany("""INSERT INTO PLAYER VALUES
(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", players)

matches = [
 ('CT25_M01','2025-02-19','Group Stage','Pakistan',    'New Zealand', 'Pakistan',    'Field','New Zealand', 'Pakistan',   '60 runs',   'runs',  'Daryl Mitchell',   'National Stadium Karachi',    '245/6','185/10',50.0,42.3,'First match of CT25. New Zealand chased but fell short.'),
 ('CT25_M02','2025-02-20','Group Stage','Bangladesh',  'India',       'India',       'Field','India',       'Bangladesh', '6 wickets', 'wickets','Shubman Gill',    'Dubai International Stadium', '228/10','232/4', 49.3,47.2,'India chased down 229 with 6 wickets.'),
 ('CT25_M03','2025-02-21','Group Stage','Afghanistan', 'South Africa','South Africa','Field','South Africa','Afghanistan','7 wickets', 'wickets','Kagiso Rabada',   'National Stadium Karachi',    '157/10','158/3', 38.2,28.4,'SA bowled out AFG for 157, chased easily.'),
 ('CT25_M04','2025-02-22','Group Stage','Australia',   'England',     'Australia',   'Bat',  'Australia',   'England',    '5 wickets', 'wickets','Travis Head',     'Gaddafi Stadium',             '283/8','284/5', 50.0,47.1,'Australia successfully defended a big total.'),
 ('CT25_M05','2025-02-23','Group Stage','Pakistan',    'India',       'India',       'Field','India',       'Pakistan',   '6 wickets', 'wickets','Virat Kohli',     'Dubai International Stadium', '241/9','245/4', 50.0,46.3,'High-pressure clash, Kohli anchored the chase.'),
 ('CT25_M06','2025-02-24','Group Stage','Bangladesh',  'New Zealand', 'New Zealand', 'Field','New Zealand', 'Bangladesh', '8 wickets', 'wickets','Rachin Ravindra', 'Rawalpindi Cricket Stadium',  '198/10','199/2',48.4,32.1,'NZ dominated with bat and ball.'),
 ('CT25_M07','2025-02-25','Group Stage','Australia',   'South Africa','South Africa','Bat',  'Australia',   'South Africa','2 wickets','wickets','Mitchell Starc',  'Rawalpindi Cricket Stadium',  '265/9','267/8', 50.0,49.2,'Nail-biting finish, Starc won it for AUS.'),
 ('CT25_M08','2025-02-26','Group Stage','England',     'Afghanistan', 'England',     'Bat',  'England',     'Afghanistan','69 runs',  'runs',   'Ben Stokes',      'Gaddafi Stadium',             '327/7','258/10',50.0,48.3,'England posted a big total, AFG fought but fell short.'),
 ('CT25_M09','2025-02-27','Group Stage','India',       'New Zealand', 'New Zealand', 'Field','India',       'New Zealand','4 wickets','wickets','Shubman Gill',    'Dubai International Stadium', '268/7','270/6', 50.0,47.4,'India chased down 269 in a thriller.'),
 ('CT25_M10','2025-02-28','Group Stage','Pakistan',    'Bangladesh',  'Pakistan',    'Bat',  'Pakistan',    'Bangladesh', '7 wickets','wickets','Babar Azam',      'Rawalpindi Cricket Stadium',  '315/6','202/10',50.0,41.2,'Pakistan dominated both innings.'),
 ('CT25_M11','2025-03-01','Group Stage','England',     'South Africa','England',     'Bat',  'South Africa','England',    '5 wickets','wickets','Kagiso Rabada',   'Gaddafi Stadium',             '258/9','261/5', 50.0,47.3,'SA chased down 259 with Rabada starring.'),
 ('CT25_M12','2025-03-02','Group Stage','Afghanistan', 'Australia',   'Australia',   'Field','Australia',   'Afghanistan','3 wickets','wickets','Pat Cummins',     'Gaddafi Stadium',             '218/10','221/7',47.2,46.4,'AUS scraped through against AFG.'),
 ('CT25_SF1','2025-03-04','Semi Final', 'India',       'Australia',   'India',       'Field','India',       'Australia',  '10 wickets','wickets','Rohit Sharma',   'Dubai International Stadium', '197/10','200/0',43.1,32.2,'India demolished AUS — Rohit and Gill unbeaten.'),
 ('CT25_SF2','2025-03-05','Semi Final', 'New Zealand', 'South Africa','South Africa','Field','New Zealand', 'South Africa','50 runs', 'runs',   'Kane Williamson','Rawalpindi Cricket Stadium',  '278/8','228/10',50.0,48.2,'NZ set a big total, SA could not chase.'),
 ('CT25_F01','2025-03-09','Final',      'India',       'New Zealand', 'New Zealand', 'Bat',  'India',       'New Zealand','4 wickets','wickets','Virat Kohli',    'Dubai International Stadium', '252/8','256/6', 50.0,48.3,'India won the Champions Trophy 2025 — Kohli unbeaten 100*'),
]
cur.executemany("INSERT INTO MATCHES VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", matches)

# Innings data
innings = [
 # match, inn_no, bat_team, bowl_team, runs, wkts, overs, pp_r, pp_w, mid_r, mid_w, death_r, death_w, extras, hi_over, hi_over_runs
 ('CT25_M01',1,'Pakistan','New Zealand',    245,6, 50,58,1,138,3,49,2,12,48,14),
 ('CT25_M01',2,'New Zealand','Pakistan',    185,10,42.3,42,2,102,5,41,3,8,47,12),
 ('CT25_M02',1,'Bangladesh','India',        228,10,49.3,48,2,128,5,52,3,9,46,11),
 ('CT25_M02',2,'India','Bangladesh',        232,4, 47.2,52,0,138,2,42,2,7,48,13),
 ('CT25_M03',1,'Afghanistan','South Africa',157,10,38.2,38,3, 88,5,31,2,6,44,10),
 ('CT25_M03',2,'South Africa','Afghanistan',158,3, 28.4,42,0, 92,2,24,1,5,48,14),
 ('CT25_M04',1,'Australia','England',       283,8, 50,62,1,158,4,63,3,11,49,16),
 ('CT25_M04',2,'England','Australia',       284,5, 47.1,58,1,162,3,64,1, 9,48,13),
 ('CT25_M05',1,'Pakistan','India',          241,9, 50,54,2,138,4,49,3,11,47,12),
 ('CT25_M05',2,'India','Pakistan',          245,4, 46.3,58,0,142,2,45,2,8,48,14),
 ('CT25_M06',1,'Bangladesh','New Zealand',  198,10,48.4,42,3,112,5,44,2,8,45,11),
 ('CT25_M06',2,'New Zealand','Bangladesh',  199,2, 32.1,52,0, 98,1,49,1,6,52,15),
 ('CT25_M07',1,'South Africa','Australia',  265,9, 50,58,1,148,4,59,4,12,48,13),
 ('CT25_M07',2,'Australia','South Africa',  267,8, 49.2,55,1,152,4,60,3,10,49,14),
 ('CT25_M08',1,'England','Afghanistan',     327,7, 50,72,0,178,3,77,4,14,52,18),
 ('CT25_M08',2,'Afghanistan','England',     258,10,48.3,54,2,142,5,62,3,11,47,13),
 ('CT25_M09',1,'India','New Zealand',       268,7, 50,62,1,152,3,54,3,12,48,13),
 ('CT25_M09',2,'New Zealand','India',       270,6, 47.4,58,0,158,3,54,3,10,50,15),
 ('CT25_M10',1,'Pakistan','Bangladesh',     315,6, 50,68,1,172,3,75,2,13,52,17),
 ('CT25_M10',2,'Bangladesh','Pakistan',     202,10,41.2,44,2,112,5,46,3, 9,45,11),
 ('CT25_M11',1,'England','South Africa',    258,9, 50,58,2,142,4,58,3,12,47,13),
 ('CT25_M11',2,'South Africa','England',    261,5, 47.3,56,0,152,3,53,2,10,49,14),
 ('CT25_M12',1,'Afghanistan','Australia',   218,10,47.2,48,3,122,4,48,3, 9,45,11),
 ('CT25_M12',2,'Australia','Afghanistan',   221,7, 46.4,52,1,128,4,41,2, 8,48,13),
 ('CT25_SF1',1,'Australia','India',         197,10,43.1,44,3,108,5,45,2, 8,44,11),
 ('CT25_SF1',2,'India','Australia',         200,0, 32.2,68,0,112,0,20,0, 5,58,17),
 ('CT25_SF2',1,'New Zealand','South Africa',278,8, 50,62,1,158,4,58,3,12,49,14),
 ('CT25_SF2',2,'South Africa','New Zealand',228,10,48.2,48,2,128,5,52,3, 9,46,12),
 ('CT25_F01',1,'New Zealand','India',       252,8, 50,58,1,142,4,52,3,11,48,13),
 ('CT25_F01',2,'India','New Zealand',       256,6, 48.3,62,0,148,3,46,3,10,50,15),
]
cur.executemany("INSERT INTO INNINGS (match_id,innings_no,batting_team,bowling_team,total_runs,total_wickets,total_overs,pp_runs,pp_wickets,mid_runs,mid_wickets,death_runs,death_wickets,extras,highest_over,highest_over_runs) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", innings)

# Key player match stats (selected key performers per match)
pms = [
 # CT25_F01 — Final
 ('CT25_F01','IND02','IND', 100,112,8,4,'not out','not out',3, 0,0,0,0,0),  # Kohli 100*
 ('CT25_F01','IND01','IND',  65, 78,4,2,'caught','caught',1,  0,0,0,0,0),  # Rohit 65
 ('CT25_F01','IND07','IND',  12, 14,0,1,None,'not out',8,  10.0,42,3,1,0),  # Kuldeep 3 wkts
 ('CT25_F01','IND08','IND',   4,  6,0,0,None,'bowled',11, 10.0,38,2,0,0),  # Bumrah 2 wkts
 ('CT25_F01','NZ01', 'NZ',   72, 88,5,2,'lbw','lbw',1,    0,0,0,0,0),  # Williamson 72
 ('CT25_F01','NZ03', 'NZ',    8, 12,0,0,None,'caught',11, 10.0,52,3,1,0),  # Boult 3 wkts
 # CT25_SF1 — India vs Aus
 ('CT25_SF1','IND01','IND', 103, 88,12,4,'not out','not out',1, 0,0,0,0,0),  # Rohit 103*
 ('CT25_SF1','IND03','IND',  90, 94, 8,3,'not out','not out',2, 0,0,0,0,0),  # Gill 90*
 ('CT25_SF1','IND08','IND',   2,  4,0,0,None,'bowled',11, 8.1,32,4,1,0),  # Bumrah 4 wkts
 ('CT25_SF1','AUS03','AUS',  45, 58,4,1,'bowled','bowled',3,  0,0,0,0,0),
 ('CT25_SF1','AUS04','AUS',  15, 22,1,0,None,'caught',11, 8.0,38,3,0,0),  # Cummins 3 wkts
 # CT25_M05 — Pak vs India
 ('CT25_M05','IND02','IND',  122,130,10,5,'not out','not out',4, 0,0,0,0,0),  # Kohli 122*
 ('CT25_M05','PAK01','PAK',   88, 98, 8,3,'caught','caught',2, 0,0,0,0,0),  # Babar 88
 ('CT25_M05','IND07','IND',    8, 12, 0,0,None,'bowled',9, 10.0,38,3,1,0),  # Kuldeep 3 wkts
 ('CT25_M05','PAK04','PAK',   12, 18, 0,1,None,'caught',11,10.0,48,3,0,0),  # Shaheen 3 wkts
]
cur.executemany("INSERT INTO PLAYER_MATCH_STATS (match_id,player_id,team_id,runs_scored,balls_faced,fours,sixes,dismissed_by,dismissal,batting_pos,overs_bowled,runs_given,wickets,maidens,caught) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", pms)

# Partnerships
partnerships = [
 ('CT25_F01',2,'India','IND01','IND02',122,138,1),  # Rohit-Kohli 122
 ('CT25_F01',2,'India','IND02','IND04', 88, 98,2),  # Kohli-Rahul 88
 ('CT25_SF1',2,'India','IND01','IND03',200,188,1),  # Rohit-Gill 200* unbeaten
 ('CT25_M05',2,'India','IND02','IND01', 98, 88,1),  # Kohli-Rohit 98
 ('CT25_M05',2,'India','IND02','IND04',108,122,2),  # Kohli-Rahul 108
]
cur.executemany("INSERT INTO PARTNERSHIP (match_id,innings_no,batting_team,player1_id,player2_id,runs,balls,wicket_no) VALUES (?,?,?,?,?,?,?,?)", partnerships)

# Update standings
for s in [
    ('IND',4,0,0,5),('PAK',2,1,0,4),('NZ',2,1,0,4),('BAN',0,2,0,2),
    ('AUS',2,1,0,4),('ENG',1,2,0,3),('SA',2,1,0,3),('AFG',0,2,0,2)]:
    cur.execute("UPDATE TEAM SET no_of_wins=?,no_of_loses=?,no_of_no_results=?,total_matches=? WHERE team_id=?",(s[1],s[2],s[3],s[4],s[0]))

conn.commit()
conn.close()
print("✓ Database created:", config.DB_PATH)
print("  New tables: INNINGS, PLAYER_MATCH_STATS, PARTNERSHIP")
print("  New views:  vw_PhaseStats, vw_GroundStats, vw_PlayerMatchForm")
print("  Richer PLAYER table: phase splits, wicket types, batting style")