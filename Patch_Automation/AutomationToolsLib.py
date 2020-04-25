# /usr/local/bin/python3

# Generic tools that can be re-used with other scripts.
# Copyright (C) 2020  Dan Engh

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import getpass
import pathlib
from os import mkdir
import plistlib
import sys
import requests
import json

# Logging function that pulls a custom log location from an automation plist or uses the default
def Logging(filename, message="\n", printLogLocation=False):
    # Set the log file path
    currentUser = getpass.getuser()
    userFilePath = pathlib.Path(
        "/Users/" + currentUser + "/Library/Logs/Patch_Automation"
    )
    try:
        userPreferences = plistlib.load(
            open(
                "/Users/"
                + currentUser
                + "/Library/Preferences/com.github.patch.automation.plist",
                "rb",
            )
        )
        try:
            userFilePath = pathlib.Path(userPreferences["LOG_LOCATION"])
        except:
            pass
    except:
        pass
    logPath = userFilePath
    # Verify that the log location exists
    CreatePath(userFilePath, logPath)
    # Will print the log location out to console or write a message to the log.
    if printLogLocation:
        print("Log can be viewed at " + str(logPath))
    else:
        openLog = open(logPath / filename, "a+")
        openLog.write(str(message) + "\n")
        openLog.close()


# Checks to see if the file path alread exists. If it does not, it creates it.
def CreatePath(filepath, logpath):
    if not filepath.exists():
        mkdir(filepath)
    if not logpath.exists():
        print("Log location doesn't exist. Creating path...")
        mkdir(logpath)
        print(str(logpath) + " created.")


# Checks for plist of preferences and returns a dictionary of the required keys for the automation
def AutomationPreferences(*args):
    logFile = "automation_errors.log"
    currentUser = getpass.getuser()
    userPrefFile = (
        "/Users/"
        + currentUser
        + "/Library/Preferences/com.github.patch.automation.plist"
    )
    autopkgPrefFile = (
        "/Users/" + currentUser + "/Library/Preferences/com.github.autopkg.plist"
    )
    automationPrefs = {}
    # Checks the two locations for preferences needed for automation and creates dictionaries of all existing
    # values.
    try:
        userPrefs = plistlib.load(open(userPrefFile, "rb"))
    except:
        userPrefs = {}
    try:
        autopkgPrefs = plistlib.load(open(autopkgPrefFile, "rb"))
    except:
        autopkgPrefs = {}
    # If preferences are found, this will check to see if the key values passed as arguments exist in the preference files.
    # A single dictionary is built of only the keys needed.
    if len(userPrefs) > 0:
        for preference in userPrefs:
            if preference in args:
                automationPrefs[preference] = userPrefs[preference]
    if len(autopkgPrefs) > 0:
        for preference in autopkgPrefs:
            if preference not in userPrefs:
                if preference in args:
                    automationPrefs[preference] = autopkgPrefs[preference]
    # If no keys or new preferences were found, it will write out to the console and give the preference file locations that
    # the values can be added to.
    if len(automationPrefs) == 0:
        logFile = "Missing_Preferences.log"
        print(
            "No preferences found. Please add them to one of the following preferences files: "
        )
        Logging(
            logFile,
            "No preferences found. Please add them to one of the following preferences files: ",
        )
        print(userPrefFile)
        print(autopkgPrefFile)
        Logging(logFile, userPrefFile)
        Logging(logFile, autopkgPrefFile)
        print("Required Keys:")
        Logging(logFile, "Required Keys:")
        for requiredKey in args:
            Logging(logFile, requiredKey)
            print(requiredKey)
        print(Logging(logFile, printLogLocation=True))
        sys.exit()
    # If it finds the keys, it checks to make sure that all the needed keys were found and write back to the console which ones
    # need to be added to the preference file.
    else:
        missingKeys = []
        for key in args:
            try:
                automationPrefs[key]
            except:
                missingKeys.append(key)
        if len(missingKeys) > 0:
            logFile = "Missing_Preferences.log"
            print(
                "Required key(s) "
                + str(missingKeys)
                + " are missing. Please add them to one of the following preferences files: "
            )
            Logging(
                logFile,
                "Required key(s) "
                + str(missingKeys)
                + " are missing. Please add them to one of the following preferences files: ",
            )
            print(userPrefFile)
            print(autopkgPrefFile)
            Logging(logFile, userPrefFile)
            Logging(logFile, autopkgPrefFile)
            print(Logging(logFile, printLogLocation=True))
            sys.exit()
    # Finally returns the built dictionary with just the keys that are needed.
    return automationPrefs


# This will send a notification to the specified slack channel below. Since we only have one at this time set up, it is
# hard coded to the #autopkg_updates channel.
def SlackNotification(logfile, message):
    slackURL = AutomationPreferences("SLACK_URL")
    msg = {"text": message}
    slackPost = requests.post(
        slackURL, data=json.dumps(msg), headers={"content-type": "application/json"}
    )
    if slackPost.status_code != 200:
        Logging(
            logfile,
            "There was an error posting to Slack: " + str(slackPost.status_code),
        )
