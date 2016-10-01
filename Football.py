# Football.py holds the functions for accessing football scores during GAMEDAYS
# using an online API.

# Example API code taken from devloper.fantasydata.com
import http.client, urllib.request, urllib.parse, urllib.error, base64
import json
import logging

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

        logging.info(dataStr)
        conn.close()
    except Exception as e:
        logging.error("Failure when accessing football API: " + str(e))
        return None

    return dataObj

def updateFootballSchedule(year, team):
    fullSchedule = readFootballAPI(APIscorespath, APIschedule + year)
    scheduleGT = []

    for game in fullSchedule:
        if  game[APIfield_AwayTeam] == team or \
            game[APIfield_HomeTeam] == team:
            newGame = {}
            newGame[APIfield_GameID]       = game[APIfield_GameID]
            newGame[APIfield_DateTime]     = game[APIfield_DateTime]
            newGame[APIfield_AwayTeam]     = game[APIfield_AwayTeam]
            newGame[APIfield_HomeTeam]     = game[APIfield_HomeTeam]
            newGame[APIfield_AwayTeamName] = game[APIfield_AwayTeamName]
            newGame[APIfield_HomeTeamName] = game[APIfield_HomeTeamName]
            scheduleGT.append(newGame)

    # Write schedule to log and to file for later use
    logging.info("Got football schedule:")
    logging.info(json.dumps(scheduleGT, indent=4))
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

# -----------------
# --- EXECUTION ---
# -----------------

# Testing
updateHeaders("")
updateFootballSchedule("2016", APIdata_GTTeam)
readFootballSchedule()
