#!/usr/local/bin/python3

from AutomationToolsLib import Logging, AutomationPreferences, SlackNotification
from datetime import date
from xml.etree import ElementTree
import requests
from os import devnull
from sys import exit


def GetUpdatedSoftwareVersion():
    logPrefs = AutomationPreferences("LOG_LOCATION")
    tDate = str(date.today())
    newPackageFile = open(logPrefs["LOG_LOCATION"] + "/newpackage.log", "r")
    softwareUpdates = {}
    for line in newPackageFile:
        if tDate in line:
            for software in newPackageFile:
                if "updated software:" in software:
                    software = software.strip("updated software: ")
                    software = software.rstrip("\n")
                    software = software.rsplit(sep=" ", maxsplit=1)
                    softwareUpdates[software[0]] = software[1]
    return softwareUpdates


def AddPackageToDefinition(updatedSoftware):
    logfile = "jamfPatchUpdate.log"
    jamfPrefs = AutomationPreferences("JSS_URL", "API_USERNAME", "API_PASSWORD")
    patchURL = jamfPrefs["JSS_URL"] + "/JSSResource/patchsoftwaretitles"
    pkgSuffix = ".pkg"
    pkgList = []
    for pkg in updatedSoftware:
        pkgList.append(pkg + "-" + updatedSoftware[pkg] + pkgSuffix)
    response = requests.get(
        patchURL,
        auth=(jamfPrefs["API_USERNAME"], jamfPrefs["API_PASSWORD"]),
        headers={"Accept": "application/xml"},
    )
    if response.status_code != 200:
        Logging(logfile, "Error connecting to Jamf: " + str(response.status_code))
        Logging(logfile, response.content)
        exit()
    responseTree = ElementTree.fromstring(response.content)
    for software in updatedSoftware:
        iterator = 1
        software_not_found = False
        while iterator <= int(responseTree[0].text):
            if software == responseTree[iterator][0].text:
                Logging(logfile, "Updating patch policy for " + software)
                patchTitleResponse = requests.get(
                    patchURL + "/id/" + responseTree[iterator][1].text,
                    auth=(jamfPrefs["API_USERNAME"], jamfPrefs["API_PASSWORD"]),
                    headers={"Accept": "application/xml"},
                )
                patchTitleTree = ElementTree.fromstring(patchTitleResponse.content)
                if patchTitleTree[6][0][0].text == updatedSoftware[software]:
                    for pkg in pkgList:
                        if updatedSoftware[software] in pkg:
                            xmlData = (
                                "<patch_software_title><versions><version><software_version>"
                                + updatedSoftware[software]
                                + "</software_version><package><name>"
                                + pkg
                                + "</name></package></version></versions></patch_software_title>"
                            )
                            newResponse = requests.put(
                                patchURL + "/id/" + responseTree[iterator][1].text,
                                auth=(
                                    jamfPrefs["API_USERNAME"],
                                    jamfPrefs["API_PASSWORD"],
                                ),
                                data=xmlData,
                                headers={"content-type": "application/xml"},
                            )
                            if newResponse.status_code != 201:
                                Logging(
                                    logfile,
                                    "Update of "
                                    + software
                                    + " failed with error code: "
                                    + str(newResponse.status_code),
                                )
                                Logging(logfile, newResponse.content)
                            else:
                                Logging(
                                    logfile,
                                    pkg
                                    + " added to definition version "
                                    + updatedSoftware[software],
                                )
                                UpdateTargetVersion(updatedSoftware[software])
                            iterator = int(responseTree[0].text) + 50
                else:
                    Logging(
                        logfile,
                        "Updated Version does not match the latest version in Jamf.",
                    )
                    Logging(
                        logfile,
                        "Jamf: "
                        + str(patchTitleTree[6][0][0].text)
                        + " != "
                        + "Updated: "
                        + updatedSoftware[software],
                    )
                    iterator = int(responseTree[0].text) + 50
            iterator = iterator + 1
            if iterator == int(responseTree[0].text):
                software_not_found = True
        if software_not_found:
            Logging(
                logfile,
                "No patch policy found for "
                + software
                + " "
                + str(updatedSoftware[software]),
            )
            print(
                "No patch policy found for "
                + software
                + " "
                + str(updatedSoftware[software])
            )


def UpdateTargetVersion(updatedSoftware):
    logfile = "jamfPatchUpdate.log"
    apiPrefs = AutomationPreferences("API_USERNAME", "API_PASSWORD", "JSS_URL")
    apiURL = apiPrefs["JSS_URL"] + "/JSSResource/patchpolicies"
    response = requests.get(
        apiURL,
        auth=(apiPrefs["API_USERNAME"], apiPrefs["API_PASSWORD"]),
        headers={"Accept": "application/xml"},
    )
    patchPolicyContent = ElementTree.fromstring(response.content)
    for software in updatedSoftware:
        counter = 1
        Logging(logfile, "Updating target version for " + software)
        for title in patchPolicyContent:
            while counter <= int(patchPolicyContent[0].text):
                softwareTestPolicy = software + " Update Test"
                if softwareTestPolicy == patchPolicyContent[counter][1].text:
                    patchPolicyID = patchPolicyContent[counter][0].text
                    xmlData = (
                        "<patch_policy><general><target_version>"
                        + updatedSoftware[software]
                        + "</target_version></general></patch_policy>"
                    )
                    patchTrgtResponse = requests.put(
                        apiURL + "/id/" + patchPolicyID,
                        auth=(apiPrefs["API_USERNAME"], apiPrefs["API_PASSWORD"]),
                        data=xmlData,
                        headers={"Content-type": "application/xml"},
                    )
                    if patchTrgtResponse.status_code != 201:
                        Logging(
                            logfile,
                            software
                            + " target version update failed with response code: "
                            + str(patchTrgtResponse.status_code),
                        )
                        Logging(
                            logfile,
                            software
                            + " target version "
                            + updatedSoftware[software]
                            + " was not updated to "
                            + patchPolicyContent[counter][1].text,
                        )
                        SlackNotification(
                            logfile,
                            ":failed: "
                            + patchPolicyContent[counter][1].text
                            + " was not updated. Please update "
                            + patchPolicyContent[counter][1].text
                            + " to `"
                            + updatedSoftware[software]
                            + "` manually.",
                        )
                    else:
                        Logging(
                            logfile,
                            patchPolicyContent[counter][1].text
                            + " has been updated to target version "
                            + updatedSoftware[software],
                        )
                        SlackNotification(
                            logfile,
                            ":white_check_mark: "
                            + patchPolicyContent[counter][1].text
                            + " has been updated to target version "
                            + updatedSoftware[software],
                        )
                    counter = int(patchPolicyContent[0].text) + 1
                else:
                    counter = counter + 1
            if counter == int(patchPolicyContent[0].text):
                Logging(logfile, softwareTestPolicy + " wasn't found.")


def Main():
    logfile = "jamfPatchUpdate.log"
    todayDate = str(date.today())
    Logging(logfile, "********************" + str(todayDate) + "********************")
    softwareUpdate = GetUpdatedSoftwareVersion()
    if len(softwareUpdate) != 0:
        AddPackageToDefinition(softwareUpdate)
        UpdateTargetVersion(softwareUpdate)
    else:
        Logging(logfile, "No new software updates.")


Main()
