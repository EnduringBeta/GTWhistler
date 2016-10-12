# Utils.py holds various functions that are not necessarily tied
# to a particular class or file and must be accessible all around.

from Constants import *
import json

def logFileSetup():
    try:
        logging.basicConfig(
            filename=logFile,
            level=logLevel,
            format='%(asctime)s: %(message)s')
    except Exception as e:
        errorStr = "Error when setting up log file: " + str(e)
        return errorStr
    return ""

# TODO: Improve how lines are formatted in DM
def getLog(numLines=DM_defaultNumLines):
    if numLines > DM_maxNumLines:
        numLines = DM_maxNumLines
    try:
        with open(logFile, 'r') as inFile:
            logText = inFile.readlines()
            # Read latest lines by reverse indexing
            return logText[-numLines:]
    except Exception as e:
        logging.error("Failure to read from storage file: " + str(e))
        return ""

def storeLatestDMID(ID):
    # Adjust input arg if not in proper form
    if isinstance(ID, int):
        ID = { Storage_LatestDMID: ID }
    elif isinstance(ID, str):
        ID = { Storage_LatestDMID: int(ID) }

    try:
        with open(storageFile, 'w') as outFile:
            json.dump(ID, outFile, indent=4)
    except Exception as e:
        logging.error("Failure to write storage file: " + str(e))
        return

def readLatestDMID():
    try:
        with open(storageFile, 'r') as inFile:
            return json.load(inFile)[Storage_LatestDMID]
    except Exception as e:
        logging.error("Failure to read from storage file: " + str(e))
        return 0
