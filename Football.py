# Football.py holds the functions for accessing football scores during GAMEDAYS
# using an online API.

# Example API code taken from devloper.fantasydata.com
import http.client, urllib.request, urllib.parse, urllib.error, base64
import logging

import Constants

headers = None

def updateHeaders(subscriptionKey):
    global headers
    headers = {
        # Request headers
        'Ocp-Apim-Subscription-Key': subscriptionKey,
    }

def accessFootballAPI(basePath, dataPath, params=urllib.parse.urlencode({})):
    if headers is None:
        logging.error("Error when calling football API: must define headers")
        return
    try:
        conn = http.client.HTTPSConnection(Constants.APIserver)
        APIpath = basePath + dataPath + "?%s" % params
        conn.request(Constants.APIget, APIpath, params, headers)
        response = conn.getresponse()
        data = response.read()
        logging.info(data)
        conn.close()
    except Exception as e:
        logging.error("Failure when accessing footbal API: " + str(e))

#def checkForFootballSchedule():
#    accessFootballAPI()


#def checkIfGameStarted():
#    return

# -----------------
# --- EXECUTION ---
# -----------------

# Testing
updateHeaders("")
accessFootballAPI(Constants.APIstatspath, Constants.APIboxscore + "1149")
