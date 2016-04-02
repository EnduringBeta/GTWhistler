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

class Whistler:
    """Class that holds functionality for processing conditions to tweet as @GT_Whistle twitter account"""

    tz          = timezone('US/Eastern')
    dt          = datetime
    dtFormat    = "%a, %d %b %Y - %H:%M:%S"
    whistled    = False

    Monday      = 0
    Tuesday     = 1
    Wednesday   = 2
    Thursday    = 3
    Friday      = 4
    Saturday    = 5
    Sunday      = 6

    def twitterSetup(self, twitterConfigFile):
        try:
            with open(twitterConfigFile, encoding='utf-8') as dataFile:
                self.twitterConfig = json.loads(dataFile.read())
        except Exception as e:
            print("Error when loading configuration:", e)

        try:
            t = Twitter(auth=OAuth(
                consumer_key    =   twitterConfig["consumer_key"],
                consumer_secret =   twitterConfig["consumer_secret"],
                token           =   twitterConfig["access_token"],
                token_secret    =   twitterConfig["access_token_secret"]))
        except Exception as e:
            print("Error when authenticating with Twitter:", e)

    def scheduleSetup(self, scheduleConfigFile):
        try:
            with open(scheduleConfigFile, encoding='utf-8') as dataFile:
                self.scheduleConfig = json.loads(dataFile.read())
        except Exception as e:
            print("Error when loading schedule:", e)

    def specialSoundSetup(self):
        # Set up "When The Whistle Blows" time and football information
        # (http://www.specialevents.gatech.edu/our-events/when-whistle-blows)
        return

    def whistleTweet(self):
        t.statuses.update(status="Woo")

    def whistlePrint(self):
        print("WOOOO @ {0}\r\n".format(dt.strftime(dtFormat)))

    def scheduleWhistle(self):
        #self.whistleTweet()
        self.whistlePrint()

        self.whistled = True
        sleep(15 * 60) # Do nothing for X seconds/minutes

    def wtwbWhistle(self):
        return

    def footballWhistle(self):
        return

    def start(self):

        schedule = self.scheduleConfig['schedule']

        # TODO: Make this loop more advanced
        try:
            while(1):
                # Get current date and time (where the whistle is)
                dt = datetime.now(self.tz)
                curTime = { "hour": dt.hour, "minute": dt.minute }
                soundTimes = schedule[dt.weekday()]

                if self.whistled == False and curTime in soundTimes
                    self.scheduleWhistle()
                else:
                    self.whistled = False
        except Exception as e:
            print("Error during loop:", e)

# ---

# Custom file for authentication data not to be shared publicly
twitterConfigFile   = "myConfig.json"
# Custom file for holding all of the scheduled times the whistle should sound
scheduleConfigFile  = "schedule.json"

GT_Whistle = Whistler()
GT_Whistle.twitterSetup(GT_Whistle, twitterConfigFile)
GT_Whistle.scheduleSetup(GT_Whistle, scheduleConfigFile)
#GT_Whistle.start()

