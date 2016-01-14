#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2

def executeQuery(args):
    """ Excutes a given query on a given DB and returns result """

    if 'dbname' in args and 'query' in args:
        connection = connect({ 'dbname' : args['dbname'] })
        if connection:
            cursor = connection.cursor()
            query = args['query']
            cursor.execute(query)
            if cursor.rowcount > 0:
                result = cursor.fetchall()
            else:
                result = 0
            connection.commit()
            connection.close()
            return result
    else:
        print "invalid query options, no database or query specified"

def connect(args):
    """Connect to the PostgreSQL database.  Returns sa database connection."""

    if 'dbname' in args:
        try:
            connection = psycopg2.connect("dbname=" + args['dbname'])
            cursor = connection.cursor()
            return connection
        except: 
            print "Connection failed. Make sure the database [" + args['dbname'] + "] exists"
            return False
    else:
        return False    


def deleteMatches():
    """Remove all the mastch records from the database."""

    query = ("DELETE FROM matches;")
    results = executeQuery({'dbname': 'tournament', 'query' : query})


def deletePlayers():
    """Remove all the player records from the database."""

    query = ("DELETE FROM players;")
    results = executeQuery({'dbname': 'tournament', 'query' : query})

def countPlayers():
    """Returns the number of players currently registered."""

    query = ("SELECT * FROM players;")
    results = executeQuery({'dbname': 'tournament', 'query' : query})
    return results

def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      name: the player's full name (need not be unique).
    """


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a player
    tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """


def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
 
 
def swissPairings():
    """Returns a list of pairs of players for the next round of a match.
  
    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.
  
    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """