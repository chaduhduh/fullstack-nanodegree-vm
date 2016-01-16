--DB definitions

-- Tournament
DROP DATABASE IF EXISTS tournament;
CREATE DATABASE tournament;

-- closes old connection if present and opens new one to tournament
\c tournament;

-- Players Schema
DROP TABLE IF EXISTS players CASCADE;
CREATE TABLE players(
   id SERIAL PRIMARY KEY,
   name VARCHAR(255)
);

-- Matches Schema
DROP TABLE IF EXISTS matches CASCADE;
CREATE TABLE matches(
   id SERIAL PRIMARY KEY,
   playeroneid BIGINT references players(id),
   playertwoid BIGINT references players(id),
   currentstatus VARCHAR(30),
   winningplayerid BIGINT,
   losingplayerid BIGINT
);

-- Player Stats
CREATE VIEW playerstats AS
SELECT id, name, (SELECT count(m.id) from matches m where m.winningplayerid = p.id) as wins,
	   (SELECT count(id) FROM matches WHERE winningplayerid = p.id OR losingplayerid = p.id) as matches
FROM players p





