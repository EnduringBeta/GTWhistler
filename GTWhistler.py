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
    curDay               = None

    dailySchedule        = None
    scheduleWhistled     = False
    prevTweets           = None

    wtwbToday            = False
    wtwbTime             = None

    GAMEDAYInfo          = None
    GAMEDAYPhase         = GamedayPhase.notGameday

    # ---------------------
    # --- SETUP METHODS ---
    # ---------------------

    def __init__(self):
        # Run "daily check" with argument True to indicate this is on boot
        self.dailyCheck(True)

    def fullSetup(self):
        setupSuccess = self.configSetup()
        setupSuccess = self.twitterSetup()  and setupSuccess
        setupSuccess = self.scheduleSetup() and setupSuccess
        setupSuccess = self.logSetup()      and setupSuccess
        setupSuccess = self.footballSetup() and setupSuccess

        return setupSuccess

    def configSetup(self):
        try:
            with open(APIConfigFile, encoding='utf-8') as dataFile:
                self.APIConfig = json.loads(dataFile.read())
        except Exception as e:
            errorStr = "Error when loading configuration: " + str(e)
            self.whistlerError(errorStr)
            return False # If error during setup, stop running

        return True

    def twitterSetup(self):
        try:
            self.t = Twitter(auth=OAuth(
                consumer_key    =   self.APIConfig[config_consumerKey],
                consumer_secret =   self.APIConfig[config_consumerSecret],
                token           =   self.APIConfig[config_accessToken],
                token_secret    =   self.APIConfig[config_accessTokenSecret]))
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

    def footballSetup(self):
        Football.updateHeaders(self.APIConfig[config_fantasyDataKey])
        scheduleGT = Football.updateFootballSchedule(self.dt.year, APIdata_GTTeam)
        if scheduleGT is not None:
            return True
        return False

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
           self.APIConfig[config_ownerUsername] is not None:
            self.DM(errorText)

    # ----------------------
    # --- TIMING METHODS ---
    # ----------------------

    def dailyCheck(self, booting=False):

        # Update date and time before doing anything
        self.updateDateTime()

        # Run full setup each day and on boot
        if not self.fullSetup():
            # If any setup did not succeed
            if booting:
                self.whistlerError("Error during boot setup!")
            else:
                self.whistlerError("Error during daily check setup!")
            return False

        self.setWeekdayAndLoadSchedule()

        self.checkIfWTWBDay()

        self.updateIfFootballScheduleUpdateDay()

        self.getInfoIfGAMEDAY()

        logging.info("Ran daily check:")
        logging.info(" - Current Day: " + str(self.curDay))
        logging.info(" - WTWB Day: " + str(self.wtwbToday))
        logging.info(" - GAMEDAY: " + str(True if self.GAMEDAYPhase \
                                                  is not GamedayPhase.notGameday else False))

        return True

    def updateDateTime(self):
        self.dt = datetime.now(tz)

    def setWeekdayAndLoadSchedule(self):
        self.curDay = self.dt.weekday()
        self.dailySchedule = self.scheduleConfig[config_regularSchedule][self.curDay]

    # Check if day of WTWB (http://www.specialevents.gatech.edu/our-events/when-whistle-blows)
    def checkIfWTWBDay(self):
        self.wtwbTime = self.scheduleConfig[config_WTWB]
        # TODO: Check if "is" is a good idea when used in code. Could be wrong!
        # Note: I have never seen this work properly yet.
        if self.dt.year  is self.wtwbTime[config_year]  and \
           self.dt.month is self.wtwbTime[config_month] and \
           self.dt.day   is self.wtwbTime[config_day]:
            self.wtwbToday = True

    # TODO: Test this
    def updateIfFootballScheduleUpdateDay(self):
        # TODO: Test this
        if Month(self.dt.month) in footballSeasonMonths and \
           Weekday(self.curDay) is updateWeekday:
            Football.updateFootballSchedule(self.dt.year, APIdata_GTTeam)

    # TODO: Test this on gameday
    def getInfoIfGAMEDAY(self):
        for game in Football.readFootballSchedule():
            if game[APIfield_DateTime] is not None:
                gameDate = datetime.strptime(game[APIfield_DateTime], dtFormatFootballAPI)
                if self.dt.year  == gameDate.year  and \
                   self.dt.month == gameDate.month and \
                   self.dt.day   == gameDate.day:
                    self.GAMEDAYInfo = game
                    # If device turned on mid-day, this will be temporarily wrong
                    self.GAMEDAYPhase = GamedayPhase.earlyGameday
                    return

        # If no game today and did not already return
        self.GAMEDAYPhase = GamedayPhase.notGameday

    # Ignores special day considerations
    def getNextScheduledWhistle(self):
        nextTime = self.getMidnight()
        self.dt = datetime.now(tz)
        # For every time on the schedule today
        for time in self.dailySchedule:
            # If scheduled time is in the future
            if time[config_hour] > self.dt.hour or \
                   (time[config_hour]   is self.dt.hour and
                    time[config_minute] >  self.dt.minute):
                # If scheduled time is sooner than working time
                if time[config_hour] < nextTime[config_hour] or \
                       (time[config_hour]   is nextTime[config_hour] and
                        time[config_minute] <  nextTime[config_minute]):
                    nextTime = time

        return nextTime

    def sleepUntil(self, nextTime):
        self.dt = datetime.now(tz)
        secToNextTime = (nextTime[config_hour]    - self.dt.hour  ) * minPerHour * secPerMin + \
                        (nextTime[config_minute]  - self.dt.minute) * secPerMin  + \
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

    @staticmethod
    def getMidnight():
        return { config_hour: maxHour, config_minute: minMinute }

    # TODO: Add reminder dates that send out DM to owner to update WTWB
    # Note: entire day is spent in this method
    def wtwbProcessing(self):
        # Remain silent during day until ceremony
        self.sleepUntil({config_hour: self.wtwbTime[config_hour],
                         config_minute: self.wtwbTime[config_minute]})

        # At beginning of ceremony
        self.whistleTweet("(When The Whistle Blows is a memorial service"
                          "taking place today to honor those lost"
                          "from the Georgia Tech community this year.)")

        # Delay for approximate length of ceremony
        sleep(self.wtwbTime[config_delay] * secPerMin)

        # ...Before tweeting in memoriam
        self.whistleTweet("(In memoriam) " + self.createWhistleText())

        # Remain quiet after ceremony
        self.sleepUntil(self.getMidnight())

    # Regular whistle schedule check
    def scheduledProcessing(self):
        curTime = {config_hour: self.dt.hour, config_minute: self.dt.minute}
        # If scheduled whistle time and haven't just whistled
        if self.scheduleWhistled is False and curTime in self.dailySchedule:
            self.scheduledWhistle()
        # If not, sleep until next useful time
        else:
            self.scheduleWhistled = False
            self.sleepUntil(self.getNextScheduledWhistle())

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

    @staticmethod
    def generateFootballWhistleText(score, oppTeam):
        # Fill out text
        text = ""
        for index in range(SsDefault):
            text += "s"
        for index in range(HsDefault):
            text += "h"
        text += "vr"
        for index in range(LowEsDefault):
            text += "e"
        for index in range(score if score > HighEsDefault else HighEsDefault):
            text += "E"

        # Yes, I completely lack maturity
        if oppTeam == APIdata_ugaTeam:
            text += "O" + thwg + "O"
        else:
            for index in range(HighOsDefault):
                text += "O"

        for index in range(LowOsDefault):
            text += "o"
        text += "w"

        return text

    def isWhistleTextValid(self, text):
        # Ensure the text does not exceed 140 characters
        # Note: no support for interpreting links
        # as taking up fewer characters
        if len(text) > twitterCharLimit:
            # Truncate text to fit (better than quitting entirely!)
            text = text[0:twitterCharLimit]

        # Compare text against past tweets to avoid duplicates
        # (which will not be tweeted as per Twitter rules)
        for tweet in self.prevTweets:
            if tweet[APIfield_TweetText] == text:
                return False

        return True

    def createWhistleText(self):
        # Get previous tweets for later comparisons of time and text
        self.prevTweets = self.t.statuses.user_timeline(
                            screen_name=self.APIConfig[config_botUsername],
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
            self.t.direct_messages.new(user=self.APIConfig[config_ownerUsername], text=message)
        except Exception as e:
            logging.error("Failure when DMing: " + str(e))

    def whistleTweet(self, text, checkTimeDelta=True):
        # For football games, do not care about short times between tweets for scores
        if checkTimeDelta:
            # Confirm it has been at least a few minutes since the last tweet
            # Could be necessary if program started and stopped within 1 minute
            lastTweetTime = datetime.strptime(self.prevTweets[0][APIfield_TweetTimestamp],
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

    # ----------------------------
    # --- MAIN PROCESSING LOOP ---
    # ----------------------------

    def start(self):
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
                    self.wtwbProcessing()
                    continue # Skip remaining processing
                # If football game today
                elif self.GAMEDAYPhase is not GamedayPhase.notGameday:
                    # TODO
                    #Football.getLatestScores()
                    continue

                # If schedule whistle time, whistle
                # If not, sleep until next useful time
                self.scheduledProcessing()
                    
        except Exception as e:
            errorStr = "Error during loop: " + str(e)
            self.whistlerError(errorStr)

# -----------------
# --- EXECUTION ---
# -----------------

# Allow time for system to come up
# TODO: Add this back in
#sleep(startupDelay)

GTWhistle = Whistler()
GTWhistle.start()
