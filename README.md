# GTWhistler #
This bot automates tweets at the times the Georgia Tech whistle sounds, including:
* The regular daily schedule
* Football game scores
* When The Whistle Blows

(It also responds to DMs at next whistle time, like a personal reminder.)

### Let me know if the schedule is wrong at any point! ###

## Notes: ##

* "Images" holds the original images and modified ones for use in the account as well as a document linking to their sources.
* "Automation" holds the script that is run as a service on the Raspberry Pi as well as instructions explaining how it works.
* "ExampleData" holds JSON files that contain useful information required for the bot to run. Sensitive data is removed. (Normally these are to be in the same directory as the Python code.)
 * "exampleConfig.json" is largely empty but is filled out on the Raspberry Pi for security reasons.
 * "exampleFootball.json" shows how data is saved for a mid-season 2016 football schedule
 * "exampleSchedule.json" shows an example schedule used by the bot to know when to tweet. (At time of writing it is identical to what is currently used.)
 * "exampleStorage.json" shows how data is stored for use between instances of running the bot.

## Task List: ##

### Confirmation Needed ###
* Commencement

### Features ###
* Bowl game
* Auto-like mentions
* Better handle and remember old DMs
