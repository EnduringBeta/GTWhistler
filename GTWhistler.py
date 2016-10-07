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
    tweetRegularSchedule = True

    wtwbToday            = False
    wtwbTime             = None

    GAMEDAYInfo          = None
    gameState            = None
    GAMEDAYPhase         = GamedayPhase.notGameday

    # ---------------------
    # --- SETUP METHODS ---
    # ---------------------

    def __init__(self):
        # Run "daily check" with argument True to indicate this is on boot
        self.dailyCheck(True)

    def fullSetup(self, booting):
        setupSuccess = self.configSetup()
        setupSuccess = self.twitterSetup()  and setupSuccess
        setupSuccess = self.scheduleSetup() and setupSuccess
        setupSuccess = self.logSetup()      and setupSuccess
        if booting:
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
        if Football.updateFootballSchedule(self.dt.year, APIdata_GTTeam) is not None:
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
        if not self.fullSetup(booting):
            # If any setup did not succeed
            if booting:
                self.whistlerError("Error during boot setup!")
            else:
                self.whistlerError("Error during daily check setup!")
            return False

        self.setWeekdayAndLoadSchedule()

        self.remindIfWTWBReminderDay()

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

    # Sent at midnight the night before because of when daily check occurs
    def remindIfWTWBReminderDay(self):
        if self.isDTThisDate(self.dt.year, # Same every year, so not stored. Cheating!
                             self.scheduleConfig[config_WTWB][config_WTWBreminder][config_month],
                             self.scheduleConfig[config_WTWB][config_WTWBreminder][config_day]):
            self.DM(wtwb_reminder)

    # Check if day of WTWB (http://www.specialevents.gatech.edu/our-events/when-whistle-blows)
    def checkIfWTWBDay(self):
        self.wtwbTime = self.scheduleConfig[config_WTWB][config_WTWBevent]
        if self.isDTThisDate(self.wtwbTime[config_year],
                             self.wtwbTime[config_month],
                             self.wtwbTime[config_day]):
            self.wtwbToday = True

    def updateIfFootballScheduleUpdateDay(self):
        if self.dt.month in self.scheduleConfig[config_football][config_updateMonths] and \
           self.curDay is self.scheduleConfig[config_football][config_updateWeekday]:
            Football.updateFootballSchedule(self.dt.year, APIdata_GTTeam)

    def getInfoIfGAMEDAY(self):
        for game in Football.readFootballSchedule():
            if game[APIfield_DateTime] is not None:
                gameDate = datetime.strptime(game[APIfield_DateTime], dtFormatFootballAPI)
                if self.dt.year  == gameDate.year  and \
                   self.dt.month == gameDate.month and \
                   self.dt.day   == gameDate.day:
                    self.GAMEDAYInfo = game
                    # If device turned on mid-day, this will be temporarily wrong
                    self.GAMEDAYPhase = GamedayPhase.midnightGameday
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
            if self.isDTBeforeThisTime(time[config_hour], time[config_minute]):
                # If scheduled time is sooner than working time
                if time[config_hour] < nextTime[config_hour] or \
                       (time[config_hour]  == nextTime[config_hour] and
                        time[config_minute] < nextTime[config_minute]):
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

    def isDTBeforeThisTime(self, hour, minute):
        return self.isFirstTimeBeforeSecond(self.dt.hour, self.dt.minute, hour, minute)

    @staticmethod
    def isFirstTimeBeforeSecond(firstHour, firstMinute, secondHour, secondMinute):
        return firstHour   < secondHour  or \
               firstHour  == secondHour and \
               firstMinute < secondMinute

    def isDTThisDate(self, year, month, day):
        return self.dt.year  == year  and \
               self.dt.month == month and \
               self.dt.day   == day

    # Note: entire day is spent in this method
    def wtwbProcessing(self):
        # Note: like most methods, this assumes "dt" is current
        if self.isDTBeforeThisTime(self.wtwbTime[config_hour], self.wtwbTime[config_minute]):
            # Remain silent during day until ceremony
            self.sleepUntil({
                config_hour: self.wtwbTime[config_hour],
                config_minute: self.wtwbTime[config_minute]
            })

            # At beginning of ceremony
            self.whistle(wtwb_explanation)

            # Delay for approximate length of ceremony
            sleep(self.wtwbTime[config_delay] * secPerMin)

            # ...Before tweeting in memoriam
            self.whistle(self.createValidRandomWhistleText(wtwb_inMemoriam))

        # Remain quiet after ceremony (or if booted during ceremony)
        self.sleepUntil(self.getMidnight())

    # "tweetRegularSchedule" is set at varous points during GAMEDAY
    # because games may occur during when scheduled whistles
    # should happen, but doing both is too convoluted and could
    # miss the game. So only before and after the game (with
    # assurances the device won't sleep through the game)
    # will regularly-scheduled whistles be enabled.
    # TODO: Test this on GAMEDAYS to ensure it updates scores appropriately
    def gamedayProcessing(self):
        # Not GAMEDAY, so leave this method and do normal day
        if   self.GAMEDAYPhase is GamedayPhase.notGameday:
            self.tweetRegularSchedule = True
            return
        # Marching band tradition to celebrate GAMEDAY the second it arrives
        elif self.GAMEDAYPhase is GamedayPhase.midnightGameday:
            # Should reach this during midnight daily check
            self.whistle(gameday_midnight)

            # Turn off scheduled tweets to make sure we reach next phase and don't sleep too long
            self.tweetRegularSchedule = False
            # Move to next phase
            self.GAMEDAYPhase = GamedayPhase.earlyGameday
            logging.info("Leaving " + str(GamedayPhase.midnightGameday))
            return
        # Long before game, so allow scheduled whistles as long
        # as the next whistle/event isn't during pregame
        elif self.GAMEDAYPhase is GamedayPhase.earlyGameday:
            # Get datetimes for next events
            gameDate = datetime.strptime(self.GAMEDAYInfo[APIfield_DateTime], dtFormatFootballAPI)
            nextWhistleTime = self.getNextScheduledWhistle()

            # If next scheduled event is after pregame begins, move to next phase
            if self.isFirstTimeBeforeSecond(gameDate.hour
                                                - self.scheduleConfig[config_football][config_pregameHours],
                                            gameDate.minute,
                                            nextWhistleTime[config_hour],
                                            nextWhistleTime[config_minute]):
                # Turn off scheduled tweets for rest of game-related events
                self.tweetRegularSchedule = False
                # Sleep until pregame time
                self.sleepUntil({
                    config_hour: gameDate.hour
                                    - self.scheduleConfig[config_football][config_pregameHours],
                    config_minute: gameDate.minute
                })
                self.GAMEDAYPhase = GamedayPhase.preGame
                logging.info("Leaving " + str(GamedayPhase.earlyGameday))
            else:
                # Leave on scheduled tweets since next one doesn't interfere with GAMEDAY
                self.tweetRegularSchedule = True
            return
        # Tweet before game for maximal school spirit, then sleep until game
        elif self.GAMEDAYPhase is GamedayPhase.preGame:
            self.whistle(gameday_pregame)
            gameDate = datetime.strptime(self.GAMEDAYInfo[APIfield_DateTime], dtFormatFootballAPI)
            self.sleepUntil({
                config_hour: gameDate.hour,
                config_minute: gameDate.minute
            })

            self.GAMEDAYPhase = GamedayPhase.toeHitLeather
            logging.info("Leaving " + str(GamedayPhase.preGame))
            return
        # Tweet as game starts
        elif self.GAMEDAYPhase is GamedayPhase.toeHitLeather:
            self.whistle(gameday_toeHitLeather)
            # Set initial game state (should be 0-0, of course)
            self.gameState = Football.getGameState(self.GAMEDAYInfo[APIfield_GameID])

            self.GAMEDAYPhase = GamedayPhase.gameOn
            logging.info("Leaving " + str(GamedayPhase.toeHitLeather))
            return
        # Check if score has changed, tweet if so, then sleep until next sampling
        elif self.GAMEDAYPhase is GamedayPhase.gameOn:
            # Get new score and progress through game
            # Note: scores are scrabled +/- 20%, but they should change during TD/FGs/Safeties
            newGameState = Football.getGameState(self.GAMEDAYInfo[APIfield_GameID])

            if Football.ourTeamScored(
                    APIdata_GTTeam,
                    self.gameState,
                    newGameState
            ):
                # Update current game state
                self.gameState = newGameState
                # Whistle using new score as input
                self.whistle(self.generateFootballWhistleText(
                    Football.ourTeamScore(APIdata_GTTeam, self.gameState),
                    Football.opposingTeam(APIdata_GTTeam, self.gameState)
                ))
                # In case of a score at the same time the game ends,
                # do one at a time. Don't want to whistle back-to-back
                sleep(scoreSamplingPeriod * secPerMin)
                return

            # If no detected score, check if game state has empty data
            # and replace with new state if it is filled.
            # This could occur at the beginning of a game before it has started.
            if Football.gameStateMissingData(self.gameState) and \
                    not Football.gameStateMissingData(newGameState):
                self.gameState = newGameState

            # If game is newly over
            if self.gameState[APIfield_Period] == APIdata_Final:
                # Tweet as game ends if victory
                if Football.ourTeamWinning(
                        APIdata_GTTeam,
                        self.GAMEDAYInfo[APIfield_HomeTeam],
                        self.gameState[APIfield_HomeTeamScore],
                        self.gameState[APIfield_AwayTeamScore]):
                    self.whistle(gameday_victory + self.generateFootballWhistleText(
                        Football.ourTeamScore(APIdata_GTTeam, self.gameState),
                        Football.opposingTeam(APIdata_GTTeam, self.gameState)
                    ))

                self.GAMEDAYPhase = GamedayPhase.postGame
                logging.info("Leaving " + str(GamedayPhase.gameOn))
            # Sleep until next time to sample
            else:
                sleep(scoreSamplingPeriod * secPerMin)
            return
        # Return to normal scheduled operation
        # (Unlikely to have more to whistle today, anyway)
        elif self.GAMEDAYPhase is GamedayPhase.postGame:
            self.GAMEDAYInfo = None
            self.gameState = None
            self.tweetRegularSchedule = True
            logging.info("Leaving " + str(GamedayPhase.postGame))
            return
        else:
            self.whistlerError("Unknown GAMEDAY phase error!")
        return

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

    def createValidRandomWhistleText(self, prefixString=""):
        # Get previous tweets for later comparisons of time and text
        self.prevTweets = self.t.statuses.user_timeline(
                            screen_name=self.APIConfig[config_botUsername],
                            count=numTweetsCompare)

        potentialText = ""
        validTextFound = False

        while not validTextFound:
            # Generate tweet text
            potentialText = prefixString + self.generateRandomWhistleText()
            # Check if text is new
            validTextFound = self.isWhistleTextValid(potentialText)

        return potentialText

    # ----------------------
    # --- OUTPUT METHODS ---
    # ----------------------

    def DM(self, message):
        try:
            self.t.direct_messages.new(user=self.APIConfig[config_ownerUsername], text=message)
            logging.info("DM: " + message)
        except Exception as e:
            logging.error("Failure when DMing: " + str(e))

    def whistleTweet(self, text):
        # Confirm it has been at least a small amount of time since the last tweet
        # Could be necessary if program started and stopped very quickly
        # Use to be optional, but now only set to 1 minute, which is within
        # GAMEDAY sampling rate for scores
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

    # Allows both methods of output for deployment and testing
    def whistle(self, text):
        if debugDoNotTweet:
            self.whistlePrint(text) # For testing
        else:
            self.whistleTweet(text)

    def scheduledWhistle(self):
        # Only tweet if not recently whistled
        if not self.scheduleWhistled:
            self.whistle(self.createValidRandomWhistleText())

    # ----------------------------
    # --- MAIN PROCESSING LOOP ---
    # ----------------------------

    def start(self):
        self.DM("[{0}] Wetting whistle... @ {1}"
                .format(versionNumber,
                        datetime.now(tz).strftime(dtFormat)))

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
                    self.gamedayProcessing()

                # Under some conditions (GAMEDAY), any regularly-scheduled tweets will be ignored
                if self.tweetRegularSchedule:
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
sleep(startupDelay)

GTWhistle = Whistler()
GTWhistle.start()
