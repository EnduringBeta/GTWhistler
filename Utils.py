# Utils.py holds various functions that are not necessarily tied
# to a particular class or file and must be accessible all around.

from Constants import *
import json
from datetime import datetime

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

# This method truncates log lines for DMing
def getLog(numLines=DM_defaultNumLines):
    if numLines > DM_maxNumLines:
        numLines = DM_maxNumLines
    try:
        with open(logFile, 'r') as inFile:
            logText = inFile.readlines()
            # If log file is too short, only return what it has
            if len(logText) < numLines:
                numLines = len(logText)

            # Limit length of any particular line to 100 characters
            # to ensure it can be DMed
            for line in logText:
                if len(line) > DM_maxLineLength:
                    logText[logText.index(line)] = line[:DM_maxLineLength - 6] + "[...]\n"

            # Read latest lines by reverse indexing,
            # then form into single string
            # (Each log line has new line character already.)
            return ''.join(logText[-numLines:])
    except Exception as e:
        logging.error("Failure to read from log file: " + str(e))
        return ""

def convertTimestampToDateTime(timestampStr):
    # Find if timestamp has timezone substring and
    # remove if so, since "strptime" can't handle it.
    # Examples: "+0000", "-0430" (always 5 characters plus a space)
    indexPlus = timestampStr.find('+')
    indexMinus = timestampStr.find('-')
    if indexPlus >= 0:
        timestampStr = timestampStr[:indexPlus] + timestampStr[indexPlus + 6:]
    elif indexMinus >= 0:
        timestampStr = timestampStr[:indexMinus] + timestampStr[indexMinus + 6:]
    
    return datetime.strptime(timestampStr, "%a %b %d %H:%M:%S %Y")

def storeLatestDMTimestamp(timestamp):
    timestamp = { Storage_LatestDMTimestamp: timestamp }

    try:
        with open(storageFile, 'w') as outFile:
            json.dump(timestamp, outFile, indent=4)
    except Exception as e:
        logging.error("Failure to write storage file: " + str(e))
        return

def readLatestDMTimestamp():
    try:
        with open(storageFile, 'r') as inFile:
            return convertTimestampToDateTime(json.load(inFile)[Storage_LatestDMTimestamp])
    except Exception as e:
        logging.error("Failure to read from storage file: " + str(e))
        return 0
