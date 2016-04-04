# GT_Whistler is an automated Twitter account that tweets
# whistle noises at the times the Georgia Tech whistle does.

# It is built upon the Python Twitter API: https://github.com/sixohsix/twitter/
# With encouragement from seeing the simplicity of the following projects:
# - metaphor-a-minute: https://github.com/dariusk/metaphor-a-minute
# - TwitterFollowBot: https://github.com/rhiever/TwitterFollowBot

# For Twitter access
from twitter import *

# For configuration reading
# (Thanks: http://stackoverflow.com/questions/2835559/parsing-values-from-a-json-file-in-python)
import json

from datetime import datetime
from pytz import timezone
from time import sleep, strftime
from random import randint
from sys import stdout
import logging

class Whistler:
    """Class that holds functionality for processing conditions to tweet as @GT_Whistle twitter account"""

    # ---------------
    # --- Members ---
    # ---------------

    twitterConfigFile   = None
    scheduleConfigFile  = None
    logFile             = None
    twitterConfig       = None
    scheduleConfig      = None
    log                 = None
    logLevel            = logging.DEBUG
    t                   = None

    tz                  = timezone('US/Eastern')
    dt                  = None
    dtFormat            = "%a, %d %b %Y - %H:%M:%S"
    dtFormatTwitter     = "%a %b %d %H:%M:%S %z %Y"
    secPerMin           = 60
    minPerHour          = 60
    dailySchedule       = None
    scheduleWhistled    = False
    prevTweets          = None

    defaultWhistleText  = "shhvreeeEEEEEEEEEEOOOOOooow"
    SsDefault           =  2
    HsDefault           =  2
    LowEsDefault        =  3
    HighEsDefault       = 10
    HighOsDefault       =  5
    LowOsDefault        =  3
    SsDelta             =  1
    HsDelta             =  1
    LowEsDelta          =  2
    HighEsDelta         =  5
    HighOsDelta         =  2
    LowOsDelta          =  2

    wtwbToday           = False
    wtwbTime            = None
    GAMEDAY             = False

    curDay              = None
    Monday              = 0
    Tuesday             = 1
    Wednesday           = 2
    Thursday            = 3
    Friday              = 4
    Saturday            = 5
    Sunday              = 6

    errorDelay          = 15
    minTweetTimeDelta   = 5
    postTweetDelay      = 15
    loopDelay           = 0.5

    silenceBeforeWTWB   = 3 # Number of hours before When The Whistle Blows
                            # that the whistle will not do scheduled whistles
    numTweetsCompare    = 5 # Number of past tweets to compare against when
                            # generating new tweet text

    # ---------------------
    # --- SETUP METHODS ---
    # ---------------------

    def __init__(self, twitterFileInput, scheduleFileInput, logFileInput):
        self.twitterConfigFile  = twitterFileInput
        self.scheduleConfigFile = scheduleFileInput
        self.logFile            = logFileInput

        # Get current date and time (where the whistle is)
        self.dt = datetime.now(self.tz)

        if not self.fullSetup(): # If any setup did not succeed
            # TODO: Make this failure louder!
            return False

        # Load schedule
        self.curDay = self.dt.weekday()
        self.dailySchedule = self.scheduleConfig['regularSchedule'][self.curDay]

    def processException(self, text):
        logging.error(text)
        self.directMessageOnError(text)
        sleep(self.errorDelay * self.secPerMin) # Do nothing for a while to prevent spammy worst-case scenarios

    def directMessageOnError(self, errorText):
        if self.t is not None and \
           self.twitterConfig is not None and \
           self.twitterConfig['owner_username'] is not None:
            try:
                self.t.direct_messages.new(user=self.twitterConfig['owner_username'], text=errorText)
            except Exception as e:
                logging.error("Failure when error DMing: " + str(e))

    def twitterSetup(self):
        try:
            with open(self.twitterConfigFile, encoding='utf-8') as dataFile:
                self.twitterConfig = json.loads(dataFile.read())
        except Exception as e:
            errorStr = "Error when loading configuration: " + str(e)
            self.processException(errorStr)
            return False # If error during setup, stop running

        try:
            self.t = Twitter(auth=OAuth(
                consumer_key    =   self.twitterConfig["consumer_key"],
                consumer_secret =   self.twitterConfig["consumer_secret"],
                token           =   self.twitterConfig["access_token"],
                token_secret    =   self.twitterConfig["access_token_secret"]))
        except Exception as e:
            errorStr = "Error when authenticating with Twitter: " + str(e)
            self.processException(errorStr)
            return False # If error during setup, stop running

        return True

    def scheduleSetup(self):
        try:
            with open(self.scheduleConfigFile, encoding='utf-8') as dataFile:
                self.scheduleConfig = json.loads(dataFile.read())
        except Exception as e:
            errorStr = "Error when loading schedule: " + str(e)
            self.processException(errorStr)
            return False # If error during setup, stop running

        return True

    def logFileSetup(self):
        try:
            logging.basicConfig(
                filename=self.logFile,
                level=self.logLevel,
                format='%(asctime)s: %(message)s')
            logging.info("GT_Whistler Log File Started")
        except Exception as e:
            errorStr = "Error when setting up log file: " + str(e)
            self.processException(errorStr)
            return False # If error during setup, stop running

        return True

    def fullSetup(self):
        successful = self.twitterSetup()
        successful = self.scheduleSetup() and successful
        successful = self.logFileSetup() and successful

        return successful

    def dailyCheck(self):

        if not self.fullSetup(): # If any setup did not succeed
            return False

        self.curDay = self.dt.weekday()
        self.dailySchedule = self.scheduleConfig['regularSchedule'][self.curDay]

        # Check if day of WTWB (http://www.specialevents.gatech.edu/our-events/when-whistle-blows)
        self.wtwbTime = self.scheduleConfig['WTWB']
        if self.dt.year  is self.wtwbTime['year']  and \
           self.dt.month is self.wtwbTime['month'] and \
           self.dt.day   is self.wtwbTime['day']:
            self.wtwbToday = True

        # TODO: Check if day of a football game
        if False:
            self.GAMEDAY = True

        logging.info("Ran daily check:")
        logging.info(" - Current Day: " + str(self.curDay))
        logging.info(" - WTWB Day: " + str(self.wtwbToday))
        logging.info(" - GAMEDAY: " + str(self.GAMEDAY))

        return True

    def generateRandomWhistleText(self):
        # Calculate randomized numbers of letters
        numSs     = randint(    self.SsDefault - self.SsDelta,     self.SsDefault     + self.SsDelta)
        numHs     = randint(    self.HsDefault - self.HsDelta,     self.HsDefault     + self.HsDelta)
        numLowEs  = randint( self.LowEsDefault - self.LowEsDelta,  self.LowEsDefault  + self.LowEsDelta)
        numHighEs = randint(self.HighEsDefault - self.HighEsDelta, self.HighEsDefault + self.HighEsDelta)
        numHighOs = randint(self.HighOsDefault - self.HighOsDelta, self.HighOsDefault + self.HighOsDelta)
        numLowOs  = randint( self.LowOsDefault - self.LowOsDelta,  self.LowOsDefault  + self.LowOsDelta)

        # Fill out text
        text = ""
        for index in range(numSs):
            text += "s"
        for index in range(numHs):
            text += "h"
        text += "vr"
        for index in range(numLowEs):
            text += "e"
        for index in range(numHighEs):
            text += "E"
        for index in range(numHighOs):
            text += "O"
        for index in range(numLowOs):
            text += "o"
        text += "w"

        return text

    def isWhistleTextValid(self, text):
        # Compare text against past tweets to avoid duplicates
        # (which will not be tweeted as per Twitter rules)
        for tweet in self.prevTweets:
            if tweet['text'] is text:
                return False

        return True

    def createWhistleText(self):
        # Get previous tweets for later comparisons of time and text
        self.prevTweets = self.t.statuses.user_timeline(
                            screen_name=self.twitterConfig['bot_username'],
                            count=self.numTweetsCompare)

        validTextFound = False

        while (not validTextFound):
            # Generate tweet text
            potentialText = self.generateRandomWhistleText()
            # Check if text is new
            validTextFound = self.isWhistleTextValid(potentialText)

        return potentialText

    # ----------------------
    # --- OUTPUT METHODS ---
    # ----------------------

    def whistleTweet(self, text):
        # Confirm it has been at least a few minutes since the last tweet
        # Could be necessary if program started and stopped within 1 minute
        lastTweetTime = datetime.strptime(self.prevTweets[0]['created_at'], \
                                          self.dtFormatTwitter)             \
                                           .astimezone(self.tz)

        if 0 <= (self.dt - lastTweetTime).seconds <= self.minTweetTimeDelta * self.secPerMin:
            return

        try:
            self.t.statuses.update(status=text)
        except Exception as e:
            errorStr = "Error when tweeting: " + text + " (" + str(e) + ")"
            self.processException(errorStr)

        printStr = "Whistled: {0} @ {1}".format(text, self.dt.strftime(self.dtFormat))
        logging.info(printStr)

        self.scheduleWhistled = True

    # Method primarily for debugging
    # Note that this does not follow the restriction of only one message per 5 minutes
    def whistlePrint(self, text):
        printStr = "Whistled: {0} @ {1}".format(text, self.dt.strftime(self.dtFormat))
        print(printStr)
        stdout.flush()
        logging.info(printStr)

        self.scheduleWhistled = True

    def scheduledWhistle(self):
        # Create text to tweet
        text = self.createWhistleText()

        # Only tweet if not recently whistled
        if not self.scheduleWhistled:
            self.whistleTweet(text)
            #self.whistlePrint(text)
        else:
            return

        sleep(self.postTweetDelay * self.secPerMin) # Do nothing for a while

    # TODO: Add reminder dates that send out DM to owner to update WTWB and football dates
    def wtwbFirstWhistle(self):
        self.whistleTweet("(When The Whistle Blows is a memorial service taking place today to honor those lost from the Georgia Tech community this year.)")

    def wtwbSecondWhistle(self):
        self.whistleTweet("(In memoriam) " + self.createWhistleText())

    def footballWhistle(self):
        self.whistleTweet("Football!")

    # ----------------------------
    # --- MAIN PROCESSING LOOP ---
    # ----------------------------

    def start(self):
        try:
            while(1):
                # Get current date and time (where the whistle is)
                self.dt = datetime.now(self.tz)
                curTime = { "hour": self.dt.hour, "minute": self.dt.minute }

                # If first check of a new day, run daily check
                if self.curDay is not self.dt.weekday():
                    if not self.dailyCheck(): # Check return value to see if should exit
                        return

                # If When The Whistle Blows day
                if self.wtwbToday:
                    # If near WTWB time
                    if 0 <= self.dt.hour - self.wtwbTime['hour'] <= self.silenceBeforeWTWB:
                        # If exactly time
                        if self.dt.hour is self.wtwbTime['hour'] and \
                           self.dt.minute is self.wtwbTime['minute']:
                            self.wtwbFirstWhistle()

                            sleep(self.wtwbTime['delay'] * self.secPerMin) # Delay for approximate length of ceremony
                            self.wtwbSecondWhistle()

                            sleep(self.minPerHour * self.secPerMin) # Remain quiet after ceremony
                            self.wtwbToday = False
                            continue
                        # If not exactly time, start again
                        else:
                            continue

                # If football game today
                if self.GAMEDAY:
                    # TODO
                    continue

                # If scheduled whistle time and haven't just whistled
                if self.scheduleWhistled == False and curTime in self.dailySchedule:
                    self.scheduledWhistle()
                else:
                    self.scheduleWhistled = False
                    sleep(self.loopDelay * self.secPerMin) # If not, sleep a little bit to lower CPU load
        except Exception as e:
            errorStr = "Error during loop: " + str(e)
            self.processException(errorStr)

# -----------------
# --- EXECUTION ---
# -----------------

# Custom file for authentication data not to be shared publicly
twitterConfigFile   = "myConfig.json"
# Custom file for holding all of the scheduled times the whistle should sound
scheduleConfigFile  = "mySchedule.json"
# File for holding logs of program behavior and actions
logFile             = "GTW_log.txt"

GT_Whistle = Whistler(twitterConfigFile, scheduleConfigFile, logFile)
GT_Whistle.start()
