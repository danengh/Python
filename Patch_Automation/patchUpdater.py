#!/usr/local/bin/python3

# 1) Identify new software uploaded to Jamf
# 2) Push and pull from github repo to update software version in JSON
# 3) Push new version through API to patch server with JSON file
# 4) Notify a slack room.
# JSON patch-only file is identified by "-patch.json"
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
# Version 1.0

import pathlib
import subprocess
import requests
import json
import sys
from getpass import getuser
import os
from datetime import date
from datetime import datetime
from xml.etree import ElementTree
from AutomationToolsLib import Logging, AutomationPreferences, SlackNotification

# Function to look through the current list and compare it to the file already in place to see if there are new packages. If it finds them, posts them to the new package
# list. Retunrs the updated software in a dictionary.
def FindUpdatedSoftware(packageList, packageFile):
    logFile = "newpackage.log"
    updatedSoftwareDict = {}
    softwareListPath = GetFileLocation()
    if not softwareListPath.exists():
        os.mkdir(softwareListPath)
    softwareListLog = softwareListPath / packageFile
    if not softwareListLog.exists() or os.stat(softwareListLog).st_size <= 5:
        print("No file exists. Moving on...")
    else:
        softList = open(softwareListLog, "r").readlines()
        for software in packageList:
            try:
                if (
                    str(
                        packageList[software][0]
                        + ":"
                        + str(packageList[software][1])
                        + "\n"
                    )
                    in softList
                ):
                    pass
                else:
                    updatedSoftwareDict[packageList[software][0]] = packageList[
                        software
                    ][1]
                    Logging(
                        logFile,
                        "updated software: "
                        + packageList[software][0]
                        + " "
                        + str(packageList[software][1]),
                    )
            except:
                pass
    return updatedSoftwareDict


# Re-writes the software package list that is used for comparison to find new software packages.
def WriteToSoftwareList(packageDict, packageFile):
    logFile = "newpackage.log"
    softwareListPath = GetFileLocation()
    softwareListLog = softwareListPath / packageFile
    if not softwareListPath.exists():
        os.mkdir(softwareListPath)
    softwareListFile = open(softwareListLog, "w+")
    if len(packageDict) == 0:
        Logging(
            logFile,
            "Could not reach the Jamf server. The master list of packages will remain unchanged.",
        )
    else:
        for software in packageDict:
            try:
                softwareListFile.write(
                    packageDict[software][0]
                    + ":"
                    + str(packageDict[software][1])
                    + "\n"
                )
            except:
                pass
        Logging(logFile, "The master list of of packages has been updated.")


# Finds all of the ID's and then the package names in Jamf. It then returns the the list of packages.
def CreateSoftwareIDList(APIEndpoint, apiUser, apiPass):
    logFile = "newpackage.log"
    api = APIEndpoint + "/packages"
    softwareIDList = []
    jssSoftware = requests.get(
        api, auth=(apiUser, apiPass), headers={"Accept": "application/xml"}
    )
    if jssSoftware.status_code != 200:
        Logging(
            logFile,
            "There was an error connecting with the API with error code: "
            + str(jssSoftware.status_code),
        )
        Logging(logFile, str(jssSoftware.content))
        packageNameList = {}
        return packageNameList
    else:
        numPackagesTree = ElementTree.fromstring(jssSoftware.content)
        counter = 1
        done = "false"
        while done:
            try:
                softwareIDList.append(numPackagesTree[counter][0].text)
                counter = counter + 1
            except:
                done = "true"
                break
        packageNameList = GetPackageName(api, apiUser, apiPass, softwareIDList)
        return packageNameList


# Gets the package name based on the ID from Jamf.
def GetPackageName(APIEndpoint, apiUser, apiPass, softwareIDList):
    softwarePackages = {}
    for packageID in softwareIDList:
        api = APIEndpoint + "/id/" + str(packageID)
        packageXML = requests.get(
            api, auth=(apiUser, apiPass), headers={"Accept": "application/xml"}
        )
        if packageXML.status_code == 200:
            packageTree = ElementTree.fromstring(packageXML.content)
            package = packageTree[1].text.split("-", maxsplit=2)
            while len(package) > 2:
                package.pop()
            try:
                if "pkg" in str(package[1]):
                    package[1] = package[1].strip(".pkg")
            except:
                exit
            try:
                softwarePackages[packageID] = package
            except:
                print("WTF")
        elif packageXML.status_code == 404:
            pass
        else:
            print(
                "There is no package associated with "
                + str(softwarePackages[packageID])
                + " error code: "
                + str(packageXML.status_code)
            )
            pass
    return softwarePackages


# Function to get and create, if needed, the log file path and location.
def GetFileLocation():
    currentUser = getuser()
    libraryPath = pathlib.Path("/Users/" + currentUser + "/Library")
    logPath = libraryPath / "Logs/Patch_Automation"
    if not logPath.exists():
        os.mkdir(logPath)
    return logPath


# Pushes and pulls the github repo and any changes in the JSON files.
def GithubActions(patchRepo, commit=None):
    patchRepo = pathlib.Path(patchRepo)
    logFile = "newpackage.log"
    currentDir = os.getcwd()
    if patchRepo.exists():
        if commit is None:
            Logging(logFile, "Getting updated JSON files")
            os.chdir(patchRepo)
            subprocess.call(["git", "pull"])
            os.chdir(currentDir)
        else:
            Logging(logFile, "Pushing updated JSON back to Github")
            os.chdir(patchRepo)
            subprocess.call(["git", "commit", "-a", "-m", "'daily update'"])
            subprocess.call(["git", "push"])
            os.chdir(currentDir)
    else:
        Logging(
            logFile,
            "Github folder for Jamf Patch files does not exist. Github update failed",
        )


# Updates the patch server with the updated JSON definition.
def UpdatePatchserver(updSftwreDict, log):
    userPrefs = AutomationPreferences("PATCH_REPO", "PATCH_URL", "PATCH_TOKEN")
    gitRepo = userPrefs["PATCH_REPO"]
    patchURL = userPrefs["PATCH_URL"]
    apiToken = userPrefs["PATCH_TOKEN"]
    # Make sure the endpoint is pointing to the correct URL for updating
    if "/api/v1/title" not in patchURL:
        patchURL = patchURL + "/api/v1/title"
    GithubActions(gitRepo)
    for software in updSftwreDict:
        jsonFilepath = UpdateJSON(software, updSftwreDict[software])
        patchServer = patchURL + "/" + software + "/version"
        if pathlib.Path.exists(jsonFilepath):
            jsonFile = open(jsonFilepath, "r")
            patchResponse = requests.post(
                patchServer,
                data=jsonFile,
                headers={
                    "Content-type": "application/json",
                    "Authorization": "Bearer " + apiToken,
                },
            )
            if patchResponse.status_code != 201:
                Logging(
                    log,
                    software
                    + ": Patch update failed with error code "
                    + str(patchResponse.status_code),
                )
                Logging(log, str(patchResponse.content))
        else:
            Logging(log, str(jsonFilepath) + " doesn't exist.")
    GithubActions(gitRepo, "commit")


# Identifies the json file that needs to be updated, sends request to update the file, sends request to update the patch server
# and finally sends notifications to slack.
def UpdateJSON(title, version):
    logFile = "JSONUpdate.log"
    currUser = getuser()
    userPrefs = AutomationPreferences("PATCH_REPO")
    try:
        gitRepo = pathlib.Path(userPrefs["PATCH_REPO"])
    except:
        gitRepo = pathlib.Path("/Users/" + currUser + "/Documents/GitHub")
        print("No patch repo set. Using default path: " + str(gitRepo))
    JSONFile = title + "-patch.json"
    if pathlib.Path.exists(gitRepo / JSONFile):
        ModifyJSON(gitRepo / JSONFile, title, version, logFile)
        SlackNotification(
            logFile,
            str(date.today())
            + " : "
            + title
            + " has been updated to "
            + version
            + ". "
            + title
            + " has been updated on the patch server",
        )
        Logging(logFile, str(datetime.today()) + ": " + JSONFile + " was updated.")
    else:
        JSONFile = JSONFile.replace(" ", "%20")
        if pathlib.Path.exists(gitRepo / JSONFile):
            ModifyJSON(gitRepo / JSONFile, title, version, logFile)
            SlackNotification(
                logFile,
                str(date.today())
                + " : "
                + title
                + " has been updated to "
                + version
                + ". "
                + title
                + " has been updated on the patch server",
            )
            Logging(logFile, str(datetime.today()) + ": " + JSONFile + " was updated.")
        else:
            JSONFile = JSONFile.replace("%20", "")
            if pathlib.Path.exists(gitRepo / JSONFile):
                ModifyJSON(gitRepo / JSONFile, title, version, logFile)
                SlackNotification(
                    logFile,
                    str(date.today())
                    + " : "
                    + title
                    + " has been updated to "
                    + version
                    + ". "
                    + title
                    + " has been updated on the patch server",
                )
                Logging(
                    logFile, str(datetime.today()) + ": " + JSONFile + " was updated."
                )
            else:
                Logging(logFile, JSONFile + " does not exist.")
                SlackNotification(
                    logFile,
                    str(date.today())
                    + " : "
                    + title
                    + " has been updated to "
                    + version
                    + ". Please update patch definitions manually",
                )
    return gitRepo / JSONFile


# Modifies the json file with the updated version and date
def ModifyJSON(file, title, newVersion, logFile):
    todayDate = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    JSONFile = open(file, "r")
    JSONDict = json.load(JSONFile)
    JSONFile.close()
    oldVersion = JSONDict.get("version")
    for item in JSONDict:
        if item == "version":
            JSONDict[item] = newVersion
        if item == "releaseDate":
            JSONDict[item] = todayDate
    for item in JSONDict.get("components")[0]:
        if item == "version":
            try:
                JSONDict.get("components")[0][item] = newVersion
            except:
                Logging(
                    logFile,
                    "Unable to get object " + str(JSONDict.get("components")[0][item]),
                )
    try:
        for appCritera in JSONDict.get("components")[0].get("criteria"):
            if appCritera["value"] == oldVersion:
                appCritera["value"] = newVersion
    except:
        Logging(
            logFile,
            "Unable to get object "
            + str(appCritera in JSONDict.get("components")[0].get("criteria")),
        )
    JSONFile = open(file, "w")
    json.dump(JSONDict, JSONFile)
    JSONFile.close()


# Main function
def Main():
    userPrefs = AutomationPreferences("JSS_URL", "API_USERNAME", "API_PASSWORD")
    if "https://" not in userPrefs["JSS_URL"]:
        userPrefs["JSS_URL"] = "https://" + userPrefs["JSS_URL"]
    jssApi = userPrefs["JSS_URL"] + "/JSSResource"
    apiUser = userPrefs["API_USERNAME"]
    apiPass = userPrefs["API_PASSWORD"]
    todayDate = date.today()
    packagesList = "JPSPackages.txt"
    logFile = "newpackage.log"
    Logging(logFile, "********************" + str(todayDate) + "********************")
    packageNames = CreateSoftwareIDList(jssApi, apiUser, apiPass)
    if len(packageNames) == 0:
        updatedSoftware = {}
    else:
        updatedSoftware = FindUpdatedSoftware(packageNames, packagesList)
    if len(updatedSoftware) == 0:
        Logging(logFile, "No Updates")
        SlackNotification(logFile, "No New Software")
        WriteToSoftwareList(packageNames, packagesList)
    else:
        WriteToSoftwareList(packageNames, packagesList)
        UpdatePatchserver(updatedSoftware, logFile)
    Logging(logFile, printLogLocation=True)


Main()
