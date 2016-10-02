# GTWhistler is an automated Twitter account that tweets
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
from time import sleep
from random import randint
from sys import stdout

from Constants import *
import Utils
import Football

class Whistler:
    """Class that holds functionality for processing
    conditions to tweet as @GTWhistle twitter account"""

    # ---------------
    # --- Members ---
    # ---------------

    APIConfig            = None
    scheduleConfig       = None
    log                  = None
    t                    = None

    dt                   = None

    dailySchedule        = None
    scheduleWhistled     = False
    prevTweets           = None

    wtwbToday            = False
    wtwbTime             = None
    GAMEDAY              = False

    curDay               = None

    gamedayPhase         = GamedayPhase.notGameday

    # ---------------------
    # --- SETUP METHODS ---
    # ---------------------

    def __init__(self):

        # Get current date and time (where the whistle is)
        self.dt = datetime.now(tz)

        if not self.fullSetup(): # If any setup did not succeed
            self.whistlerError("Error during initialization setup!")
            return

        # Load schedule
        self.curDay = self.dt.weekday()
        self.dailySchedule = self.scheduleConfig['regularSchedule'][self.curDay]

    def fullSetup(self):
        setupSuccess = self.twitterSetup()
        setupSuccess = self.scheduleSetup() and setupSuccess
        setupSuccess = self.logSetup() and setupSuccess
        setupSuccess = Football.updateFootballSchedule(self.dt.year, APIdata_GTTeam) and setupSuccess

        return setupSuccess

    def twitterSetup(self):
        try:
            with open(APIConfigFile, encoding='utf-8') as dataFile:
                self.APIConfig = json.loads(dataFile.read())
        except Exception as e:
            errorStr = "Error when loading configuration: " + str(e)
            self.whistlerError(errorStr)
            return False # If error during setup, stop running

        try:
            self.t = Twitter(auth=OAuth(
                consumer_key    =   self.APIConfig["consumer_key"],
                consumer_secret =   self.APIConfig["consumer_secret"],
                token           =   self.APIConfig["access_token"],
                token_secret    =   self.APIConfig["access_token_secret"]))
        except Exception as e:
            errorStr = "Error when authenticating with Twitter: " + str(e)
            self.whistlerError(errorStr)
            return False # If error during setup, stop running

        return True

    def scheduleSetup(self):
        try:
            with open(scheduleConfigFile, encoding='utf-8') as dataFile:
                self.scheduleConfig = json.loads(dataFile.read())
        except Exception as e:
            errorStr = "Error when loading schedule: " + str(e)
            self.whistlerError(errorStr)
            return False # If error during setup, stop running

        return True

    def logSetup(self):
        retStr = Utils.logFileSetup()
        if retStr == "":
            logging.info("GTWhistler Log File Started")
            return True
        else:
            self.whistlerError("Error when setting up log file: " + retStr)
            return False # If error during setup, stop running

    # ------------------------------
    # --- ERROR HANDLING METHODS ---
    # ------------------------------

    def whistlerError(self, text):
        logging.error(text)
        self.directMessageOnError(text)
        sleep(errorDelay * secPerMin) # Do nothing for a while to prevent spammy worst-case scenarios

    def directMessageOnError(self, errorText):
        if self.t is not None and \
           self.APIConfig is not None and \
           self.APIConfig['owner_username'] is not None:
            self.DM(errorText)

    # ----------------------
    # --- TIMING METHODS ---
    # ----------------------

    def dailyCheck(self):

        if not self.fullSetup(): # If any setup did not succeed
            self.whistlerError("Error during daily check setup!")
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

    # Ignores special day considerations
    def getNextScheduledWhistle(self):
        nextTime = { "hour": maxHour, "minute": minMinute }
        self.dt = datetime.now(tz)
        # For every time on the schedule today
        for time in self.dailySchedule:
            # If scheduled time is in the future
            if time['hour'] > self.dt.hour or \
                   (time['hour']   is self.dt.hour and
                    time['minute'] >  self.dt.minute):
                # If scheduled time is sooner than working time
                if time['hour'] < nextTime['hour'] or \
                       (time['hour']   is nextTime['hour'] and
                        time['minute'] <  nextTime['minute']):
                    nextTime = time

        return nextTime

    def sleepUntil(self, nextTime):
        self.dt = datetime.now(tz)
        secToNextTime = (nextTime['hour']    - self.dt.hour  ) * minPerHour * secPerMin + \
                        (nextTime['minute']  - self.dt.minute) * secPerMin  + \
                        (minSecond - self.dt.second)
                        # Find time difference to calculate total sleep time.
                        # If no more scheduled times, calculation based on 24h:00m for daily check.
                        # Next time should always be beginning of minute, so subtract off
                        # the seconds we are currently already into the current minute.
                        # Extra milliseconds mean wake occurs within the
                        # first second of the minute, which is acceptable noise.

        try:
            sleep(secToNextTime) # Sleep until next time
        except Exception as e:
            errorStr = "Error when trying to sleep: " + str(e)
            self.whistlerError(errorStr)

    # ----------------------
    # --- STRING METHODS ---
    # ----------------------

    @staticmethod
    def generateRandomWhistleText():
        # Calculate randomized numbers of letters
        numSs     = randint(SsDefault     - SsDelta,
                            SsDefault     + SsDelta)
        numHs     = randint(HsDefault     - HsDelta,
                            HsDefault     + HsDelta)
        numLowEs  = randint(LowEsDefault  - LowEsDelta,
                            LowEsDefault  + LowEsDelta)
        numHighEs = randint(HighEsDefault - HighEsDelta,
                            HighEsDefault + HighEsDelta)
        numHighOs = randint(HighOsDefault - HighOsDelta,
                            HighOsDefault + HighOsDelta)
        numLowOs  = randint(LowOsDefault  - LowOsDelta,
                            LowOsDefault  + LowOsDelta)

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
        # Ensure the text does not exceed 140 characters
        # Note: no support for interpreting links
        # as taking up fewer characters
        if len(text) > twitterCharLimit:
            return False

        # Compare text against past tweets to avoid duplicates
        # (which will not be tweeted as per Twitter rules)
        for tweet in self.prevTweets:
            if tweet['text'] == text:
                return False

        return True

    def createWhistleText(self):
        # Get previous tweets for later comparisons of time and text
        self.prevTweets = self.t.statuses.user_timeline(
                            screen_name=self.APIConfig['bot_username'],
                            count=numTweetsCompare)

        potentialText = ""
        validTextFound = False

        while not validTextFound:
            # Generate tweet text
            potentialText = self.generateRandomWhistleText()
            # Check if text is new
            validTextFound = self.isWhistleTextValid(potentialText)

        return potentialText

    # ----------------------
    # --- OUTPUT METHODS ---
    # ----------------------

    def DM(self, message):
        try:
            self.t.direct_messages.new(user=self.APIConfig['owner_username'], text=message)
        except Exception as e:
            logging.error("Failure when DMing: " + str(e))

    def whistleTweet(self, text):
        # Confirm it has been at least a few minutes since the last tweet
        # Could be necessary if program started and stopped within 1 minute
        lastTweetTime = datetime.strptime(self.prevTweets[0]['created_at'],
                                          dtFormatTwitter) \
                                           .astimezone(tz)

        secSinceLastTweet = (self.dt - lastTweetTime).seconds
        if 0 <= secSinceLastTweet <= minTweetTimeDelta * secPerMin:
            sleep((minTweetTimeDelta * secPerMin) - secSinceLastTweet)
            return

        # Otherwise, tweet!
        try:
            self.t.statuses.update(status=text)
        except Exception as e:
            errorStr = "Error when tweeting: " + text + " (" + str(e) + ")"
            self.whistlerError(errorStr)
        else:
            printStr = "Whistled: {0} @ {1}".format(text, self.dt.strftime(dtFormat))
            logging.info(printStr)

            self.scheduleWhistled = True

    # Method primarily for debugging
    # Note that this does not follow the restriction of only one message per 5 minutes
    def whistlePrint(self, text):
        printStr = "Whistled: {0} @ {1}".format(text, self.dt.strftime(dtFormat))
        print(printStr)
        stdout.flush()
        logging.info(printStr)

        self.scheduleWhistled = True

    def scheduledWhistle(self):
        # Create text to tweet
        text = self.createWhistleText()

        # Only tweet if not recently whistled
        if not self.scheduleWhistled:
            if debugDoNotTweet:
                self.whistlePrint(text)  # For testing
            else:
                self.whistleTweet(text)
        else:
            return

    # TODO: Add reminder dates that send out DM to owner to update WTWB and football dates
    def wtwbFirstWhistle(self):
        self.whistleTweet("(When The Whistle Blows is a memorial service taking place"
                          "today to honor those lost from the Georgia Tech community this year.)")

    def wtwbSecondWhistle(self):
        self.whistleTweet("(In memoriam) " + self.createWhistleText())

    def footballWhistle(self):
        self.whistleTweet("Football!")

    # ----------------------------
    # --- MAIN PROCESSING LOOP ---
    # ----------------------------

    def start(self):

        # Allow time for system to come up
        sleep(startupDelay)
        self.dt = datetime.now(tz)
        self.DM("[{0}] Wetting whistle... @ {1}".format(versionNumber, self.dt.strftime(dtFormat)))

        try:
            while 1:
                # Get current date and time (where the whistle is)
                self.dt = datetime.now(tz)
                
                # If first check of a new day, run daily check
                if self.curDay is not self.dt.weekday():
                    if not self.dailyCheck(): # Check return value to see if should exit
                        return

                # If When The Whistle Blows day
                if self.wtwbToday:
                    # If near WTWB time
                    if 0 <= self.dt.hour - self.wtwbTime['hour'] <= silenceBeforeWTWB:
                        # If exactly time
                        if self.dt.hour is self.wtwbTime['hour'] and \
                           self.dt.minute is self.wtwbTime['minute']:
                            self.wtwbFirstWhistle()

                            # Delay for approximate length of ceremony
                            sleep(self.wtwbTime['delay'] * secPerMin)
                            self.wtwbSecondWhistle()

                            sleep(minPerHour * secPerMin) # Remain quiet after ceremony
                            self.wtwbToday = False
                            continue
                        # If near but not exactly time, wait until then
                        else:
                            self.sleepUntil({ "hour":   self.wtwbTime['hour'],
                                              "minute": self.wtwbTime['minute']
                                            })
                            continue

                # If football game today
                if self.GAMEDAY:
                    # TODO
                    #Football.getLatestScores()
                    continue

                curTime = { "hour": self.dt.hour, "minute": self.dt.minute }
                # If scheduled whistle time and haven't just whistled
                if self.scheduleWhistled is False and curTime in self.dailySchedule:
                    self.scheduledWhistle()
                    continue
                else:
                    self.scheduleWhistled = False
                    self.sleepUntil(self.getNextScheduledWhistle())
                    continue
                    
        except Exception as e:
            errorStr = "Error during loop: " + str(e)
            self.whistlerError(errorStr)

# -----------------
# --- EXECUTION ---
# -----------------

GTWhistle = Whistler()
GTWhistle.start()
