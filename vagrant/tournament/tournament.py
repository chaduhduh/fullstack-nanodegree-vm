#!/usr/bin/env python
# 
# tournament.py -- implementation of a Swiss-system tournament
#

import psycopg2

def executeQuery(args):
    """ Excutes a given query on a given DB and returns result 

        This abstracts the actual execution of the queries. This way
        any other lib or database type could be used without needing to
        rewrite all of the functions below. One could simply rewrite how
        the connection is made and how query is ran. This could also be 
        modified slightly to be a wrapper excluding certain query types.

        Args:
        dbname : name of database to connect to
        query : query to run on database
        type : type of query to run. Insert, find, delete
        values : list of values to insert into query (prevent injection)
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
                if 'values' not in args:
                    cursor.execute(query)
                else:
                    cursor.execute(query,args['values'])
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
                    cursor.execute(query,args['values'])
                    result = cursor.rowcount

            connection.commit()
            cursor.close()
            connection.close()
            return result


def connect(args):
    """Connect to the PostgreSQL database.  Returns sa database connection.

        Args:
        dbame : name of database to connect
    """

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
    """Remove all the match records from the database."""

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


def registerPlayer(name):
    """Adds a player to the tournament database.
  
    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)
  
    Args:
        name : name of player to regiset
    """

    if len(name) < 1:
        print "Player not registered. Invalid name or no name given."
    else:
        query = "INSERT INTO players (name) VALUES (%s)"
        values = (name,)
        results = executeQuery({
            'dbname': 'tournament', 
            'query' : query, 
            'type' : 'insert', 
            'values' : values
            })


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

    getPlayers = "SELECT id, name, wins, matches FROM playerstats ORDER BY wins DESC"
    players = executeQuery({'dbname': 'tournament', 'query' : getPlayers, 'type' : 'find'})
    return players


def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    
    if not winner or not loser:
        print "one or no players specified for report match"
    else:
        query = "INSERT INTO matches \
                (playeroneid, losingplayerid) \
                VALUES (%s,%s)"
        values = (winner, loser)
        results = executeQuery({
            'dbname': 'tournament', 
            'query' : query, 
            'type' : 'insert', 
            'values' : values
            })
 
 
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

    match_tup = ()
    matches_list = []
    player_count = 0 # keeps track of how many players per match
    players = playerStandings();
    for player in players:
        if player_count == 0:
            playerone = player
            player_count += 1
        elif player_count == 1:
            playertwo = player
            player_count += 1
        if player_count == 2: # match full, add match to list then reset
            match_tup = (playerone[0],playerone[1],playertwo[0],playertwo[1])
            matches_list.append(match_tup)
            player_count = 0
    return matches_list

