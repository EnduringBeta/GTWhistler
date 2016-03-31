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
from time import sleep

class Whistler:
    """Class that holds functionality for processing conditions to tweet as @GT_Whistle twitter account"""

    tz = timezone('US/Eastern')
    dt = datetime
    whistled = False;

    Monday = 0
    Friday = 5
    morningHour = 7
    eveningHour = 12 + 5
    classStartMinute = 5
    classEndMinute = 55

    def setup(self):
        # Custom file for authentication data not to be shared publicly.
        configFile = "myConfig.json"

        try:
            with open(configFile, encoding='utf-8') as dataFile:
                config = json.loads(dataFile.read())
        except Exception as e:
            print("Error when loading configuration:", e)

        try:
            t = Twitter(auth=OAuth(
                consumer_key    =   config["consumer_key"],
                consumer_secret =   config["consumer_secret"],
                token           =   config["access_token"],
                token_secret    =   config["access_token_secret"]))
        except Exception as e:
            print("Error when authenticating with Twitter:", e)

    def whistle(self):
        print("Tweet\r\n")
        self.whistled = True

    def start(self):
        # TODO: Make this loop more advanced
        try:
            while(1):
                # Get current date and time (where the whistle is)
                dt = datetime.now(self.tz)
                # Check if a weekday
                if self.Monday <= dt.weekday() <= self.Friday:
                    # Check if during hours of 7AM to 5PM
                    if self.morningHour <= dt.hour <= self.eveningHour:
                        # Check if 5-after on any hour but 7AM
                        if self.whistled == False and \
                            dt.hour != self.morningHour and \
                            dt.minute == self.classStartMinute:
                            self.whistle()
                        # Check if 5-till on any hour
                        elif self.whistled == False and \
                            dt.minute == self.classEndMinute:
                            self.whistle()
                        else:
                            self.whistled = False
        except Exception as e:
            print("Error during loop:", e)

# ---

GT_Whistle = Whistler()
GT_Whistle.setup()
GT_Whistle.start()

