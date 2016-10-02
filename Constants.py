# Constants.py holds various constants that don't belong in other files

import logging
from pytz import timezone
from enum import Enum

# Project constants
versionNumber        = "v1.0.2"

# Custom file for authentication data not to be shared publicly
APIConfigFile        = "myConfig.json"
# Custom file for holding all of the scheduled times the whistle should sound
scheduleConfigFile   = "schedule.json"
# Custom file for holding football schedule as access from API
scheduleFootballFile = "football.json"
# File for holding logs of program behavior and actions
logFile              = "GTW_log.txt"

# Logging constants
logLevel             = logging.DEBUG

# Timezone/Formatting constants
tz                   = timezone('US/Eastern')
dtFormat             = "%a, %d %b %Y - %H:%M:%S"
dtFormatTwitter      = "%a %b %d %H:%M:%S %z %Y"
dtFormatFootballAPI  = "%Y-%m-%dT%H:%M:%S"

# Time constants
secPerMin            = 60
minPerHour           = 60
maxHour              = 24
lastHour             = 23
minHour              =  0
maxMinute            = 60
lastMinute           = 59
minMinute            =  0
maxSecond            = 60
lastSecond           = 59
minSecond            =  0

# Whistle string constants
defaultWhistleText   = "shhvreeeEEEEEEEEEEOOOOOooow"
SsDefault            =  2
HsDefault            =  2
LowEsDefault         =  3
HighEsDefault        = 10
HighOsDefault        =  5
LowOsDefault         =  3
SsDelta              =  1
HsDelta              =  1
LowEsDelta           =  2
HighEsDelta          =  5
HighOsDelta          =  2
LowOsDelta           =  2

# Weekday constants
# (Only used for football scheduling)
class Weekday(Enum):
    Monday           = 0
    Tuesday          = 1
    Wednesday        = 2
    Thursday         = 3
    Friday           = 4
    Saturday         = 5
    Sunday           = 6

# Month constants
# (Only used for football scheduling)
class Month(Enum):
    January          =  1
    February         =  2
    March            =  3
    April            =  4
    May              =  5
    June             =  6
    July             =  7
    August           =  8
    September        =  9
    October          = 10
    November         = 11
    December         = 12

# Delay constants
startupDelay         = 10 # seconds
errorDelay           = 15 # minutes
minTweetTimeDelta    = 5  # minutes

# Other Whistler constants
numTweetsCompare     = 5    # Number of past tweets to compare against when
                            # generating new tweet text
twitterCharLimit     = 140  # Twitter 101 - all tweets must be <= 140 characters

debugDoNotTweet      = True # While in development, this Boolean prevents the
                            # account from tweeting, instead printing on the
                            # machine to confirm proper output.

# Config JSON field constants
config_ownerUsername     = "owner_username"
config_botUsername       = "bot_username"
config_consumerKey       = "consumer_key"
config_consumerSecret    = "consumer_secret"
config_accessToken       = "access_token"
config_accessTokenSecret = "access_token_secret"
config_fantasyDataKey    = "fantasy_data_key"

# Schedule JSON field constants
config_regularSchedule   = "regularSchedule"
config_WTWB              = "WTWB"

# Generic JSON field constants
config_year              = "year"
config_month             = "month"
config_day               = "day"
config_hour              = "hour"
config_minute            = "minute"
config_delay             = "delay"

# Twitter API field constants
APIfield_TweetText      = "text"
APIfield_TweetTimestamp = "created_at"

# Football API constants
APIget        = "GET"

APIprotocol   = "https://"
APIserver     = "api.fantasydata.net"
APIscorespath = "/v3/cfb/scores/JSON/"
APIstatspath  = "/v3/cfb/stats/JSON/"

APIboxscore        = "BoxScore/"
APIschedule        = "Games/"
APIgamesinprogress = "AreAnyGamesInProgress"

APIfield_Game          = "Game"
APIfield_GameID        = "GameID"
APIfield_DateTime      = "DateTime"
APIfield_AwayTeam      = "AwayTeam"
APIfield_HomeTeam      = "HomeTeam"
APIfield_AwayTeamName  = "AwayTeamName"
APIfield_HomeTeamName  = "HomeTeamName"
APIfield_AwayTeamScore = "AwayTeamScore"
APIfield_HomeTeamScore = "HomeTeamScore"
APIfield_Period        = "Period"

APIdata_GTTeam         = "GTECH"
#APIdata_GTTeamName     = "Georgia Tech Yellow Jackets"

# Football season constants
footballSeasonMonths = [Month.August,
                        Month.September,
                        Month.October,
                        Month.November,
                        Month.December]

updateWeekday        = Weekday.Sunday

# Gameday constants
class GamedayPhase(Enum):
    notGameday    = 0
    earlyGameday  = 1
    preGame       = 2
    toeHitLeather = 3
    gameOn        = 4
    gameEnds      = 5
    postGame      = 6

APIdata_ugaTeam        = "GA"
#APIdata_ugaTeamName    = "Georgia Bulldogs" # (sic)
thwg                   = "(THWg)"
