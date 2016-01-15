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




