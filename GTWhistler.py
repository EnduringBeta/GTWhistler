# GTWhistler is an automated Twitter account that tweets
# whistle noises at the times the Georgia Tech whistle does.

# It is built upon the Python Twitter API: https://github.com/sixohsix/twitter/
# With encouragement from seeing the simplicity of the following projects:
# - metaphor-a-minute: https://github.com/dariusk/metaphor-a-minute
# - TwitterFollowBot: https://github.com/rhiever/TwitterFollowBot

# For Twitter access
from TwitterAPI import TwitterAPI
# No longer supports DMs because of Twitter API change
#from twitter import *

# For configuration reading
# (Thanks: http://stackoverflow.com/questions/2835559/parsing-values-from-a-json-file-in-python)
import json
from datetime import datetime
from time import sleep
from random import randint
from random import random
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
    reset                = False

    wtwbToday            = False
    wtwbTime             = None

    footballConnected    = False
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
        # Each day, set this Boolean true in case a previous day's special event goes awry
        # If current day is a special event, this variable will be overwritten in other functions
        self.tweetRegularSchedule = True
        
        setupSuccess = self.configSetup()
        setupSuccess = self.twitterSetup()  and setupSuccess
        setupSuccess = self.scheduleSetup() and setupSuccess
        setupSuccess = self.logSetup()      and setupSuccess

        # This part of setup should not break the program if it fails
        # Note: removed this because constantly failing; maybe API changed, maybe COVID-19 scheduling
        # if booting:
        #     self.footballConnected = self.footballSetup()
        self.footballConnected = False

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
            self.t = TwitterAPI(
                self.APIConfig[config_consumerKey],
                self.APIConfig[config_consumerSecret],
                self.APIConfig[config_accessToken],
                self.APIConfig[config_accessTokenSecret])
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
        else:
            self.whistlerError("Failed to setup football feature!")
            return False

    # ------------------------------
    # --- ERROR HANDLING METHODS ---
    # ------------------------------

    def whistlerError(self, text):
        logging.error(text)
        self.directMessageOnError(text)
        # Show logs from the error
        self.directMessageOnError(Utils.getLog(DM_defaultNumLines))
        self.directMessageOnError("Sleeping for a while before continuing...")
        sleep(errorDelay * secPerMin) # Do nothing for a while to prevent spammy worst-case scenarios

    def directMessageOnError(self, errorText):
        if self.t is not None and \
           self.APIConfig is not None and \
           self.APIConfig[config_ownerUsername] is not None:
            self.sendDM(errorText)

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

        if self.footballConnected:
            self.updateIfFootballScheduleUpdateDay()
            self.getInfoIfGAMEDAY()

        logging.info("Ran daily check:")
        logging.info(" - Current Day: " + str(self.curDay))
        logging.info(" - WTWB Day: " + str(self.wtwbToday))

        if self.footballConnected:
            logging.info(" - GAMEDAY: " + str(True if self.GAMEDAYPhase \
                                                      is not GamedayPhase.notGameday else False))
        else:
            logging.info(" - GAMEDAY: Disconnected")

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
            self.sendDM(wtwb_reminder)

    # Check if day of WTWB (http://www.specialevents.gatech.edu/our-events/when-whistle-blows)
    def checkIfWTWBDay(self):
        self.wtwbTime = self.scheduleConfig[config_WTWB][config_WTWBevent]
        if self.isDTThisDate(self.wtwbTime[config_year],
                             self.wtwbTime[config_month],
                             self.wtwbTime[config_day]):
            self.wtwbToday = True
        else:
            self.wtwbToday = False

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
                    # TODO: Needs testing
                    # For each of these states, also set variables
                    # that would be set if progressed through normally

                    # If midnight hour
                    if self.dt.hour is 0:
                        self.GAMEDAYPhase = GamedayPhase.midnightGameday
                    # If before pregame time
                    elif self.isFirstTimeBeforeSecond(self.dt.hour,
                                                      self.dt.minute,
                                                      gameDate.hour - self.scheduleConfig[config_football][config_pregameHours],
                                                      gameDate.minute):
                        self.tweetRegularSchedule = False
                        self.GAMEDAYPhase = GamedayPhase.earlyGameday
                    # If before game begins
                    elif self.isFirstTimeBeforeSecond(self.dt.hour,
                                                      self.dt.minute,
                                                      gameDate.hour,
                                                      gameDate.minute):
                        self.tweetRegularSchedule = False
                        self.GAMEDAYPhase = GamedayPhase.preGame
                    # If after game has begun (and if game over, will learn immediately)
                    else:
                        self.tweetRegularSchedule = False
                        self.gameState = Football.getGameState(self.GAMEDAYInfo[APIfield_GameID])
                        self.GAMEDAYPhase = GamedayPhase.gameOn

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

    # Checks down to the minute if at midnight
    def isMidnight(self):
        mn = self.getMidnight()

        return self.dt.hour == minHour and \
               self.dt.minute == mn[config_minute]

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
    def gamedayProcessing(self):
        # Not GAMEDAY, so leave this method and do normal day
        if   self.GAMEDAYPhase is GamedayPhase.notGameday:
            self.tweetRegularSchedule = True
            return
        # Marching band tradition to celebrate GAMEDAY the second it arrives
        elif self.GAMEDAYPhase is GamedayPhase.midnightGameday:
            # TODO: If prevTweets have "#GAMEDAY" in them, skip.
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
            # TODO: Needs testing
            # If offline, escape this loop after game is surely over
            gameDate = datetime.strptime(self.GAMEDAYInfo[APIfield_DateTime], dtFormatFootballAPI)
            if abs(self.dt.hour - gameDate.hour) > gamedayMaxHours:
                self.GAMEDAYPhase = GamedayPhase.postGame

            # Hang on to previous state for comparison
            oldGameState = self.gameState
            # Get new score and progress through game
            # Note: scores are scrabled +/- 20%, but they should change during TD/FGs/Safeties
            self.gameState = Football.getGameState(self.GAMEDAYInfo[APIfield_GameID])

            if Football.ourTeamScored(
                    APIdata_GTTeam,
                    oldGameState,
                    self.gameState,
            ):
                # Whistle using new score as input
                self.whistle(self.generateFootballWhistleText(
                    Football.ourTeamScore(APIdata_GTTeam, self.gameState),
                    Football.opposingTeam(APIdata_GTTeam, self.gameState)
                ))
                # In case of a score at the same time the game ends,
                # do one at a time. Don't want to whistle back-to-back
                sleep(scoreSamplingPeriod * secPerMin)
                return

            # If game is newly over
            if self.gameState[APIfield_Period] == APIdata_Final:
                # Tweet as game ends if victory
                if Football.ourTeamWinning(APIdata_GTTeam, self.gameState):
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
        
        # Stand up for what you believe in
        cause = random()
        if cause > 0.95:
            text += " (#BlackLivesMatter)"
        elif cause > 0.9:
            text += " (#StopAsianHate)"
        elif cause < 0.1:
            text += " (#WearAMask)"

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
            # Instead rely on code calling this to be smart if returns false
            # This code would not work anyway: "text" isn't returned
            # Truncate text to fit (better than quitting entirely!)
            #text = text[0:twitterCharLimit]

            logging.warning("Warning: attempted to tweet something too long: " + text)
            return False

        # Compare text against past tweets to avoid duplicates
        # (which will not be tweeted as per Twitter rules)
        for tweet in self.prevTweets:
            if tweet[APIfield_TweetText] == text:
                logging.warning("Warning: attempted to tweet duplicate: " + text)
                return False

        return True

    def isWhistleDMTextValid(self, text):
        if len(text) > twitterDMCharLimit:
            logging.warning("Warning: attempted to DM something too long: " + "...but obviously I wouldn't print that text to the log to make sure log future reads aren't also too long. Hah. That would be so silly.")
            return False
        else:
            return True

    def createValidRandomWhistleText(self, prefixString=""):
        self.setPrevTweets()

        potentialText = ""
        validTextFound = False

        while not validTextFound:
            # Generate tweet text
            potentialText = prefixString + self.generateRandomWhistleText()
            # Check if text is new
            validTextFound = self.isWhistleTextValid(potentialText)

        return potentialText

    # ---------------------
    # --- INPUT METHODS ---
    # ---------------------

    def processDMs(self):
        for DM in self.getNewDMs():
            self.interpretDM(DM)
            # Prevent sending tons of DMs in a burst
            sleep(DM_delay)

    def getNewDMs(self):
        directMessages = []

        try:
            # Gets last 30 days of DMs
            r = self.t.request(APIgetDMsPath)
            if r.status_code == 200:
                directMessages = json.loads(r.text)[DM_events]
                if len(directMessages) == 0:
                    return []
            else:
                self.whistlerError("Could not connect to read DMs!")
                return []
        except Exception as e:
            self.whistlerError("Failure when reading DMs: " + str(e))
            return []

        latestTimestamp = Utils.readLatestDMTimestamp()

        # Set latest read DM timestamp to first in list
        # (most recent) if not same as existing
        # Only do this for future use. Old "latest" must
        # still be used for this call to know when to stop
        if int(directMessages[0][DM_timestamp]) > latestTimestamp:
            Utils.storeLatestDMTimestamp(int(directMessages[0][DM_timestamp]))

        # Return only newer DMs than last read one that were sent to the bot
        # NOTE: Will miss DMs if more than 20 received since last check
        outputDMList = []
        for DM in directMessages:
            if int(DM[DM_timestamp]) <= latestTimestamp:
                return outputDMList
            elif int(DM[DM_messageCreate][DM_target][DM_recipientID]) == self.APIConfig[config_botUserID]:
                outputDMList.append(DM)

        return outputDMList

    # TODO: Logging fails on emoji
    def interpretDM(self, DM):
        msg = DM[DM_messageCreate][DM_messageData][DM_text]
        logging.info("Received DM: " + msg)

        # If owner sent "reset"
        if DM_reset in msg.lower() and int(DM[DM_messageCreate][DM_senderID]) == self.APIConfig[config_ownerUserID]:
            self.sendDM("Resetting...")
            self.reset = True
        # If owner sent "log [num lines]"
        elif DM_printLog in msg.lower() and int(DM[DM_messageCreate][DM_senderID]) == self.APIConfig[config_ownerUserID]:
            logging.info("Attempting to print log...")
            strArr = msg.lower().split()
            if strArr[0] == DM_printLog and len(strArr) == 2:
                try:
                    numLines = int(strArr[1])
                except Exception as e:
                    logging.warning("Failure to convert number of lines argument: " + str(e))
                    self.sendDM("Print log command format: 'log [num lines]'")
                    numLines = DM_defaultNumLines
                self.sendDM(Utils.getLog(numLines))
            elif len(strArr) is 1:
                self.sendDM(Utils.getLog())
            else:
                self.sendDM("Print log command format: 'log [num lines]'")
        # Otherwise toot response (if not midnight)
        else:
            if not self.isMidnight():
                # Reply with whistle sound of roughly same length
                msgDM = "T"
                if len(msg) < DM_maxTootLength:
                    for index in range(len(msg)):
                        msgDM += "o"
                else:
                    for index in range(DM_maxTootLength):
                        msgDM += "o"
                msgDM += "t!"
                self.sendDM(msgDM, int(DM[DM_messageCreate][DM_senderID]))
            else:
                logging.info("...Heart of a lion, and the wings of a bat...")
                logging.info("Ignoring tootable DM (Because It's Midnite!): " + msg)

    # ----------------------
    # --- OUTPUT METHODS ---
    # ----------------------

    def sendDM(self, message, userID=0):
        if not self.isWhistleDMTextValid(message):
            return

        # If no user ID provided, send to owner
        if userID == 0:
            userID = self.APIConfig[config_ownerUserID]

        try:
            if not debugDoNotDM:
                payload = {
                    DM_event: {
                        DM_type: DM_messageCreate,
                        DM_messageCreate: {
                            DM_target: {
                                DM_recipientID: str(userID)
                            },
                            DM_messageData: {
                                DM_text: message
                            }
                        }
                    }
                }
                # TODO: Why does this require json.dumps()?
                r = self.t.request(APIpostDMPath, json.dumps(payload))

                if r.status_code != 200:
                    # Don't try to send another DM when it just failed
                    logging.error("Could not connect to send DM: " + r.text)

            # If message isn't too long, log
            if len(message) < DM_maxLogChars:
                logging.info("DM: " + message)
            else:
                logging.info("DM long message")
        except Exception as e:
            # Don't try to send another DM when it just failed
            logging.error("Failure when DMing: " + str(e))

    def whistleTweet(self, text):
        # Done in createValidRandomWhistleText, but not every whistle calls
        # that method. Check if None and call if so.
        if self.prevTweets is None:
            self.setPrevTweets()

        if self.prevTweets is None:
            self.whistlerError("Not tweeting!")
            return

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
            payload = {Tweet_status: text}
            r = self.t.request(APIpostTweetPath, payload)

            if r.status_code != 200:
                self.whistlerError("Could not connect to send tweet!")
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

    def setPrevTweets(self):
        # Get previous tweets for later comparisons of time and text
        try:
            payload = {
                Tweet_userID: self.APIConfig[config_botUserID],
                Tweet_count: numTweetsCompare
            }
            r = self.t.request(APIgetTweetsPath, payload)

            if r.status_code == 200:
                pT = json.loads(r.text)
                if len(pT) > 0:
                    self.prevTweets = json.loads(r.text)
                else:
                    self.whistlerError("Did not retrieve previous tweets!")
                    return
            else:
                self.whistlerError("Could not connect to get previous tweets!")
                return

        except Exception as e:
            errorStr = "Error when getting previous tweets: (" + str(e) + ")"
            self.whistlerError(errorStr)

    # ----------------------------
    # --- MAIN PROCESSING LOOP ---
    # ----------------------------

    def start(self):
        self.sendDM("[{0}] Wetting whistle... @ {1}"
                    .format(versionNumber,
                        datetime.now(tz).strftime(dtFormat)))

        try:
            while not self.reset:
                # Get current date and time (where the whistle is)
                self.dt = datetime.now(tz)
                
                # If first check of a new day, run daily check
                # Also ensure that a football game isn't currently still going from earlier in the evening
                if not self.reset and self.curDay is not self.dt.weekday() and \
                    (self.GAMEDAYPhase is GamedayPhase.notGameday or
                     self.GAMEDAYPhase is GamedayPhase.postGame):
                    if not self.dailyCheck(): # Check return value to see if should exit
                        return

                # Check if any new DMs and respond to them appropriately
                if not self.reset:
                    self.processDMs()

                # If When The Whistle Blows day
                if not self.reset:
                    if self.wtwbToday:
                        self.wtwbProcessing()
                        continue # Skip remaining processing
                    # If football game today
                    elif self.GAMEDAYPhase is not GamedayPhase.notGameday and self.footballConnected:
                        self.gamedayProcessing()

                # Under some conditions (GAMEDAY), any regularly-scheduled tweets will be ignored
                if self.tweetRegularSchedule and not self.reset:
                    # If schedule whistle time, whistle
                    # If not, sleep until next useful time
                    self.scheduledProcessing()

        except Exception as e:
            errorStr = "Error during loop: " + str(e)
            self.whistlerError(errorStr)

# -----------------
# --- EXECUTION ---
# -----------------

GTWhistle = Whistler()
GTWhistle.start()
