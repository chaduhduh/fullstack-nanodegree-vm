#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2

def executeQuery(args):
    """ Excutes a given query on a given DB and returns result 

        This essentially allows for cleaner functions below and 
        eliminates redundant code. This could also be used as a
        wrapper to eliminate certain queries from running. For 
        example one could remove support for insert type statements.
    """

    if 'dbname' not in args and 'query' not in args and 'type' not in args:
        print "invalid executeQuery options"
    else:
        querytype = args['type']
        connection = connect({ 'dbname' : args['dbname'] })
        if connection:
            cursor = connection.cursor()
            query = args['query']

            # FIND QUERY
            if(querytype == 'find'):
                cursor.execute(query)
                if cursor.rowcount > 0:
                    result = cursor.fetchall()
                else:
                    result = 0

            # DELETE QUERY
            if(querytype == 'delete'):
                cursor.execute(query)
                result = cursor.rowcount

            # INSERT QUERY
            if(querytype == 'insert'):
                if 'values' not in args:
                    print "no values to insert"
                else:
                    cursor.execute("INSERT INTO players (firstname, lastname) VALUES (%s, %s)",args['values'])
                    result = cursor.rowcount

            connection.commit()
            cursor.close()
            connection.close()
            return result

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
    results = executeQuery({'dbname': 'tournament', 'query' : query, 'type' : 'delete'})


def deletePlayers():
    """Remove all the player records from the database."""
    query = ("DELETE FROM players;")
    results = executeQuery({'dbname': 'tournament', 'query' : query, 'type' : 'delete'})


def countPlayers():
    """Returns the number of players currently registered."""
    count = 0
    query = ("SELECT COUNT(id) FROM players;")
    results = executeQuery({'dbname': 'tournament', 'query' : query, 'type' : 'find'})
    for row in results:
        count = row[0]
    return count

def registerPlayer(args):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
      first name: the player's first name (need not be unique).
      last name: the player's first name (need not be unique).
    """
    
    if 'firstname' not in args and 'lastname' not in args:
        print "Player not registered. Invalid name format. Please use first name and last name"
    else:
        query = "INSERT INTO players (firstname, lastname) VALUES (%s, %s)"
        values = ('chadddd', 'this is new')
        results = executeQuery({'dbname': 'tournament', 'query' : query, 'type' : 'insert', 'values' : values})


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
registerPlayer({'firstname' : 'cassandra', 'lastname' : 'mmmhmmm' })