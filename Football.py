# Football.py holds the functions for accessing football scores during GAMEDAYS
# using an online API.

# Example API code taken from devloper.fantasydata.com
import http.client, urllib.parse, urllib.error
import json

from Constants import *

headers = None

def updateHeaders(subscriptionKey):
    global headers
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': subscriptionKey,
    }

def readFootballAPI(basePath, dataPath, params=urllib.parse.urlencode({})):
    if headers is None:
        logging.error("Error when calling football API: must define headers")
        return
    try:
        conn = http.client.HTTPSConnection(APIserver)
        APIpath = basePath + dataPath + "?%s" % params
        conn.request(APIget, APIpath, params, headers)
        response = conn.getresponse()
        dataStr = response.read().decode()
        dataObj = json.loads(dataStr)

        #logging.info(dataStr)
        conn.close()
    except Exception as e:
        logging.error("Failure when accessing football API: " + str(e))
        return None

    return dataObj

def updateFootballSchedule(year, team):
    # Convert gameID if not string
    if isinstance(year, int):
        year = str(year)

    fullSchedule = readFootballAPI(APIscorespath, APIschedule + year)
    scheduleGT = []

    for game in fullSchedule:
        if  game[APIfield_AwayTeam] == team or \
            game[APIfield_HomeTeam] == team:
            newGame = {
                APIfield_GameID:       game[APIfield_GameID],
                APIfield_DateTime:     game[APIfield_DateTime],
                APIfield_AwayTeam:     game[APIfield_AwayTeam],
                APIfield_HomeTeam:     game[APIfield_HomeTeam],
                APIfield_AwayTeamName: game[APIfield_AwayTeamName],
                APIfield_HomeTeamName: game[APIfield_HomeTeamName]
            }
            scheduleGT.append(newGame)

    # Write schedule to log and to file for later use
    logging.info("Got football schedule")
    #logging.info(json.dumps(scheduleGT, indent=4))
    try:
        with open(scheduleFootballFile, 'w') as outFile:
            json.dump(scheduleGT, outFile, indent=4)
    except Exception as e:
        logging.error("Failure to write football schedule to file: " + str(e))
        return None

    return scheduleGT

def readFootballSchedule():
    try:
        with open(scheduleFootballFile, 'r') as inFile:
            return json.load(inFile)
    except Exception as e:
        logging.error("Failure to read football schedule from file: " + str(e))
        return None

def getGameState(gameID):
    # Convert gameID if not string
    if isinstance(gameID, int):
        gameID = str(gameID)

    gameData = readFootballAPI(APIstatspath, APIboxscore + gameID)
    # Retrieved one game entry, so first and only in array
    gameState = {
        APIfield_HomeTeam:      gameData[0][APIfield_Game][APIfield_HomeTeam],
        APIfield_AwayTeam:      gameData[0][APIfield_Game][APIfield_AwayTeam],
        APIfield_HomeTeamScore: gameData[0][APIfield_Game][APIfield_HomeTeamScore],
        APIfield_AwayTeamScore: gameData[0][APIfield_Game][APIfield_AwayTeamScore],
        APIfield_Period:        gameData[0][APIfield_Game][APIfield_Period]
    }
    logging.info(gameState)

    return gameState

# Mostly concerned with scores being null
def gameStateMissingData(gameState):
    return gameState is None or \
           gameState[APIfield_HomeTeam]      is None or \
           gameState[APIfield_AwayTeam]      is None or \
           gameState[APIfield_HomeTeamScore] is None or \
           gameState[APIfield_AwayTeamScore] is None or \
           gameState[APIfield_Period]        is None

def opposingTeam(myTeam, gameState):
    if gameState[APIfield_HomeTeam] == myTeam:
        return gameState[APIfield_AwayTeam]
    else:
        return gameState[APIfield_HomeTeam]

def ourTeamScore(myTeam, gameState):
    if gameState[APIfield_HomeTeam] == myTeam:
        return gameState[APIfield_HomeTeamScore]
    else:
        return gameState[APIfield_AwayTeamScore]

def ourTeamScored(myTeam, prevGameState, curGameState):
    # Check if any values (or game states themselves) are empty
    # This can occur at the beginning of a game
    if gameStateMissingData(prevGameState) or gameStateMissingData(curGameState):
        return False

    # If my team is home
    if curGameState[APIfield_HomeTeam] == myTeam:
        # Return whether my team score increased
        return curGameState[APIfield_HomeTeamScore] > prevGameState[APIfield_HomeTeamScore]
    # If my team is away
    else:
        # Return whether my team score increased
        return curGameState[APIfield_AwayTeamScore] > prevGameState[APIfield_AwayTeamScore]

def ourTeamWinning(myTeam, gameState):
    # Check who is home/away to properly compare scores
    if gameState[APIfield_HomeTeam] == myTeam:
        # My team is home
        return gameState[APIfield_HomeTeamScore] > gameState[APIfield_AwayTeamScore]
    else:
        # My team is away
        return gameState[APIfield_HomeTeamScore] < gameState[APIfield_AwayTeamScore]
