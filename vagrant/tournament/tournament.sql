--DB definitions

-- Tournament
DROP DATABASE IF EXISTS tournament;
CREATE DATABASE tournament;

\c tournament;

-- Players Schema
DROP TABLE IF EXISTS players CASCADE;
CREATE TABLE players(
   id SERIAL PRIMARY KEY NOT NULL,
   firstname VARCHAR(50),
   lastname VARCHAR(50)
);

-- Matches Schema
DROP TABLE IF EXISTS matches CASCADE;
CREATE TABLE matches(
   id SERIAL PRIMARY KEY NOT NULL,
   playeroneid BIGINT references players(id),
   playertwoid BIGINT references players(id),
   currentstatus VARCHAR(30),
   winningplayerid BIGINT,
   losingplayerid BIGINT
);



