#!/usr/local/bin/python3

# Creates a backup of the patchserver database, stores it locally and keeps 3 vesions.
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

from AutomationToolsLib import AutomationPreferences, Logging
import requests
from datetime import datetime
from getpass import getuser
import pathlib
import os


def GetPreferences(*args):
    userPrefs = {}
    for item in args:
        userPrefs.update(AutomationPreferences(item))
    return userPrefs


def FilepathCheck(filepath):
    if pathlib.Path(filepath).exists():
        return True
    else:
        return False


def CreateFilepath(filepath):
    pathlib.Path(filepath).mkdir()


def CreateBackup(filepath):
    currentDate = datetime.today().strftime("%Y-%m-%d")
    patchPrefs = GetPreferences("PATCH_URL", "PATCH_TOKEN")
    logFile = "patchserver_backup.log"
    backupAPI = patchPrefs["PATCH_URL"] + "/api/v1/backup"
    Logging(logFile, currentDate)
    Logging(logFile, "----------------------------------------")
    Logging(logFile, "Creating backup...")
    response = requests.get(
        backupAPI,
        headers={
            "Authorization": "Bearer " + patchPrefs["PATCH_TOKEN"],
            "Accept": "application/zip",
        },
    )
    if response.status_code != 200:
        Logging(logFile, "Error connecting to patchserver.")
        Logging(logFile, response.status_code)
        Logging(logFile, response.content)
        Logging(logFile, "Patchserver database not backed up.")
    else:
        zipFileName = str(currentDate) + "-patchserver-backup.zip"
        zipFile = open(filepath + zipFileName, "wb")
        zipFile.write(response.content)
        zipFile.close()
        Logging(logFile, "Backup successfully created.")
        Logging(logFile, zipFileName + " saved to " + filepath)


def ManageBackups(filepath):
    logFile = "patchserver_backup.log"
    fileList = os.listdir(filepath)
    try:
        fileList.remove(".DS_Store")
    except:
        print("No DS_Store file present")
    sortedFileList = sorted(fileList, reverse=True)
    print(sortedFileList)
    if len(sortedFileList) > 3:
        print("Deleting oldest backup")
        Logging(logFile, "Deleting oldest backup")
        fileToDelete = sortedFileList.pop()
        os.remove(filepath + "/" + fileToDelete)
        print(fileToDelete + " has been deleted")
        Logging(logFile, fileToDelete + " has been deleted")
        Logging(logFile)
    Logging(logFile, str(filepath))


def Main():
    currentUser = getuser()
    backupLocation = "/Users/" + currentUser + "/Documents/Patch_Backups/"
    if not FilepathCheck(backupLocation):
        CreateFilepath(backupLocation)
    CreateBackup(backupLocation)
    ManageBackups(backupLocation)


Main()
