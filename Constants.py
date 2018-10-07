# Constants.py holds various constants that don't belong in other files

import logging
from pytz import timezone
from enum import Enum

# Project constants
versionNumber        = "v2.3.0"

# Note: Use this Boolean for testing
debugDoNotTweet      = False # While in development, this Boolean prevents the
                             # account from tweeting, instead printing on the
                             # machine to confirm proper output.
debugDoNotDM         = False # Similar for direct messaging

# Custom file for authentication data not to be shared publicly
APIConfigFile        = "config.json"
# Custom file for holding all of the scheduled times the whistle should sound
scheduleConfigFile   = "schedule.json"
# Custom file for holding football schedule as access from API
scheduleFootballFile = "football.json"
# File for holding data between instances of the program running
storageFile          = "storage.json"
# File for holding logs of program behavior and actions
logFile              = "GTW_log.txt"

# Logging constants
logLevel             = logging.INFO

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
# class Weekday(Enum):
#     Monday           = 0
#     Tuesday          = 1
#     Wednesday        = 2
#     Thursday         = 3
#     Friday           = 4
#     Saturday         = 5
#     Sunday           = 6

# Month constants
# class Month(Enum):
#     January          =  1
#     February         =  2
#     March            =  3
#     April            =  4
#     May              =  5
#     June             =  6
#     July             =  7
#     August           =  8
#     September        =  9
#     October          = 10
#     November         = 11
#     December         = 12

# Delay constants
startupDelay         = 10 # seconds
errorDelay           = 15 # minutes
minTweetTimeDelta    = 1  # minutes

# This number is very important/delicate!
# Setting this rate lower will likely cause this program to
# exceed its maximum allotted number of API calls per month
scoreSamplingPeriod  = 2 # minutes

# Escape hatch value for if offline and will never receive data
# indicating the game is over
gamedayMaxHours      = 6 # hours

# Other Whistler constants
numTweetsCompare     = 12    # Number of past tweets to compare against when
                             # generating new tweet text
twitterCharLimit     = 140   # Twitter 101 - all tweets must be <= 140 characters
twitterDMCharLimit   = 10000 # Twitter 201 - all DMs as of mid-2015 can be up to 10,000 characters long

# WTWB string constants
wtwb_reminder    = "(This is your one reminder to update the When The Whistle Blows data for this year!)"
wtwb_explanation = "(When The Whistle Blows is a memorial service taking place today to honor those lost from the Georgia Tech community this year.)"
wtwb_inMemoriam  = "(In memoriam) "

# Config JSON field constants
config_ownerUsername     = "owner_username"
config_ownerUserID       = "owner_user_id"
config_botUsername       = "bot_username"
config_botUserID         = "bot_user_id"
config_consumerKey       = "consumer_key"
config_consumerSecret    = "consumer_secret"
config_accessToken       = "access_token"
config_accessTokenSecret = "access_token_secret"
config_fantasyDataKey    = "fantasy_data_key"

# Schedule JSON field constants
config_regularSchedule   = "regularSchedule"
config_WTWB              = "WTWB"
config_WTWBevent         = "event"
config_WTWBreminder      = "reminder"
config_football          = "football"
config_updateMonths      = "updateMonths"
config_updateWeekday     = "updateWeekday"
config_pregameHours      = "pregameHours"

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
# Thanks to Fantasy Data for providing a free
# trial and discussing my project with me.
# (https://fantasydata.com/products/real-time-sports-data-api.aspx)
APIget        = "GET"

APIprotocol   = "https://"
APIserver     = "api.fantasydata.net"
APIscorespath = "/v3/cfb/scores/JSON/"
APIstatspath  = "/v3/cfb/stats/JSON/"

APIboxscore        = "BoxScore/"
APIschedule        = "Games/"

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
APIdata_Final          = "F"

APIdata_GTTeam         = "GTECH"
#APIdata_GTTeamName     = "Georgia Tech Yellow Jackets"

# Gameday constants
class GamedayPhase(Enum):
    notGameday      = 0
    midnightGameday = 1
    earlyGameday    = 2
    preGame         = 3
    toeHitLeather   = 4
    gameOn          = 5
    postGame        = 6

APIdata_ugaTeam        = "GA"
#APIdata_ugaTeamName    = "Georgia Bulldogs" # (sic)
thwg                   = "(#THWg)"
gameday_midnight       = "(#GAMEDAY!)"
gameday_pregame        = "(Go Jackets!)"
gameday_toeHitLeather  = "(Sting 'em!) " + defaultWhistleText
# Used with score-calibrated whistle, so extra space needed
gameday_victory        = "(Victory!) "

# Storage File constants
Storage_LatestDMTimestamp  = "LatestDMTimestamp"

# Twitter API constants
APIpostTweetPath = "statuses/update"
APIgetTweetsPath = "statuses/user_timeline"
APIgetDMsPath = "direct_messages/events/list"
APIpostDMPath = "direct_messages/events/new"

# Tweeting constants
Tweet_status        = "status"
Tweet_userID        = "user_id"
Tweet_count         = "count"

# Direct Messaging (DM) constants
DM_delay            = 1
DM_event            = "event"
DM_events           = "events"
#DM_ID               = "id"
DM_type             = "type"
DM_timestamp        = "created_timestamp"
DM_messageCreate    = "message_create"
DM_target           = "target"
DM_recipientID      = "recipient_id"
DM_senderID         = "sender_id"
DM_messageData      = "message_data"
DM_text             = "text"
#DM_entities         = "entities"

# Direct Messaging (DM) commands
DM_reset           = "reset"
DM_printLog        = "log"
DM_defaultNumLines = 10
DM_maxNumLines     = 100
# Possible that a DM will fail if too many requested lines are this long, but unlikely
DM_maxLineLength   = 200
DM_maxLogChars     = 200
DM_maxTootLength   = 100
