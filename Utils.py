# Utils.py holds various functions that are not necessarily tied
# to a particular class or file and must be accessible all around.

from Constants import *

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

