#!/usr/local/python3

import requests
import json
import sys
from datetime import datetime
from UMNToolsLib import Logging, AutomationPreferences, SplunkHTTPHEC


def Authentication(url):
    logFile = "newpackage.log"
    titleEditorCreds = AutomationPreferences("TITLE_EDITOR_USER", "TITLE_EDITOR_PASS")
    username = titleEditorCreds["TITLE_EDITOR_USER"]
    password = titleEditorCreds["TITLE_EDITOR_PASS"]
    response = requests.post(
        "{}/auth/tokens".format(url),
        auth=(username, password),
        headers={"Accept": "application/json"},
    )
    if response.status_code not in (200, 201):
        Logging(
            logFile,
            "Failed to get authorization token from {}".format(
                "{}/auth/tokens".format(url)
            ),
        )
        exit()
    else:
        authResponse = response.json()
    authToken = authResponse["token"]
    return authToken


def GetSoftwareTitles(url, authToken):
    logFile = "newpackage.log"
    response = requests.get(
        "{}/softwaretitles".format(url),
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer {}".format(authToken),
        },
    )
    if response.status_code not in (200, 201):
        Logging(
            logFile,
            "[{}] Failed to get software titles from {}".format(
                datetime.today(), "{}/softwaretitles".format(url)
            ),
        )
        sys.exit()
    else:
        softwateResponse = response.json()
    return softwateResponse


def UpdatePatchTitle(softwareTitle, softwareID, url, authToken, currentVersion):
    logFile = "newpackage.log"
    userPrefs = AutomationPreferences("PATCH_REPO")
    jsonFilePath = userPrefs["PATCH_REPO"]
    if " " in softwareTitle:
        softwareTitle = softwareTitle.replace(" ", "")
    response = requests.get(
        "{}/softwaretitles/{}".format(url, softwareID),
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer {}".format(authToken),
        },
    )
    try:
        jsonFile = open("{}/{}_Patch.json".format(jsonFilePath, softwareTitle), "r")
        response = requests.post(
            "{}/softwaretitles/{}/patches".format(url, softwareID),
            data=jsonFile,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(authToken),
            },
        )
        if response.status_code not in (200, 201):
            Logging(
                logFile,
                "[{}] Error {}: {}".format(
                    datetime.today(), response.status_code, response.content
                ),
            )
            SplunkLogging(logFile, "Patch title update failed on the Jamf Title Editor. [{}] {}".format(
                response.status_code, 
                response.content),
                softwareTitle=softwareTitle,
                softwareID=softwareID,
                action="Patch Title Update",
                apiResult="Failed",
                softwareVersion=currentVersion)
            return "Failed"
        else:
            Logging(
                logFile,
                "[{}] {} updated to {}".format(
                    datetime.today(), softwareTitle, currentVersion
                ),
            )
            SplunkLogging(logFile, "Patch title updated on the Jamf Title Editor.".format(
                response.status_code, 
                response.content),
                softwareTitle=softwareTitle,
                softwareID=softwareID,
                action="Patch Title Update",
                apiResult="Success",
                softwareVersion=currentVersion)
            return "Success"
    except FileNotFoundError as err:
        Logging(logFile, "[{}] {}".format(datetime.today(), err))
        return "Failed"


def SetCurrentVersion(softwareID, currentVersion, url, authToken, softwareName):
    logFile = "newpackage.log"
    response = requests.put(
        "{}/softwaretitles/{}".format(url, softwareID),
        data=json.dumps({"currentVersion": currentVersion}),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(authToken),
        },
    )
    if response.status_code not in (200, 201):
        Logging(
            logFile,
            "[{}] Error setting current version for [{}] {}".format(
                datetime.today(), softwareID, softwareName
            ),
        )
        Logging(logFile, "[{}] {}".format(response.status_code, response.content))
        SplunkLogging(logFile, "Patch title update failed on the Jamf Title Editor. [{}] {}".format(
                response.status_code, 
                response.content),
                softwareTitle=softwareName,
                softwareID=softwareID,
                action="Patch Title Set Current Version",
                apiResult="Failed",
                softwareVersion=currentVersion)
        return "Failed"
    else:
        Logging(
            logFile,
            "[{}] Current version for [{}] {} updated to {}".format(
                datetime.today(),
                softwareID,
                softwareName,
                currentVersion,
            ),
        )
        SplunkLogging(logFile, "Patch title current version set to {} on the Jamf Title Editor.".format(currentVersion),
            softwareTitle=softwareName,
            softwareID=softwareID,
            action="Patch Title Set Current Version",
            apiResult="Success",
            softwareVersion=currentVersion)
        return "Success"

def SplunkLogging(logFile, message, softwareTitle=None, softwareVersion=None, action=None, softwareID=None, apiResult=None):
    splunkToken = AutomationPreferences("SPLUNK_TOKEN")
    eventData = {
        "Software title": softwareTitle,
        "Version": softwareVersion,
        "Message": message,
        "Action": action,
        "Jamf Title Editor ID": softwareID,
        "Command Result": apiResult
    }
    SplunkHTTPHEC(
        "jamf_automation", logFile, splunkToken["SPLUNK_TOKEN"], eventData, "cds_app"
    )


def Main(updateSoftwareDict):
    if len(updateSoftwareDict) == 0:
        print("No updates")
        sys.exit()
    titleEditorURL = AutomationPreferences("TITLE_EDITOR_URL")
    baseURL = titleEditorURL["TITLE_EDITOR_URL"]
    authToken = Authentication(baseURL)
    patchTitleDict = GetSoftwareTitles(baseURL, authToken)
    for softwareTitleDict in patchTitleDict:
        if softwareTitleDict["name"] in updateSoftwareDict:
            patchUpdateStatus = UpdatePatchTitle(
                softwareTitleDict["name"],
                softwareTitleDict["softwareTitleId"],
                baseURL,
                authToken,
                updateSoftwareDict[softwareTitleDict["name"]],
            )
            if patchUpdateStatus == "Success":
                currentVersionStatus = SetCurrentVersion(
                    softwareTitleDict["softwareTitleId"],
                    updateSoftwareDict[softwareTitleDict["name"]],
                    baseURL,
                    authToken,
                    softwareTitleDict["name"],
                )
    if currentVersionStatus == "Success":
        return "Success"
    else:
        return "Failed"


if __name__ == "__main__":
    Main()
