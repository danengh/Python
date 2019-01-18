#!/usr/local/bin/python

import os
import shutil
import sys
from xml.etree import ElementTree
from xml.sax.saxutils import escape
from subprocess import call
from collections import OrderedDict

class patchUpdater():
    def __init__(self):
        self.application_path = None
        self.version = None
        self.os_requirements = None
        self.publisher = None
        self.extension_attribute = None
        self.file_output_location = None
        self.patch_profile = None

def patchcliProc():
    try:
        patchcli = os.path.exists("/usr/local/bin/patchcli")
        return patchcli
    except FileNotFoundError:
        print("patchlib has not been installed")

def userInput(arg):
    returnVar = input(str("Input value for {0}: ").format(arg))
    if returnVar == "":
        returnVar = None
    return returnVar

def xmlInput(xmlPath, xmlKey):
    if not os.path.exists(xmlPath):
        raise FileNotFoundError
        print(xmlPath, " does not exist")
    xmlElements = ElementTree.parse(xmlPath)
    return tree.get(xmlKey)
    pass

def patchcliOptions(key):
    if key == "file_output_location":
        return "-o"
    elif key == "publisher":
        return "-p"
    elif key == "extension_attribute":
        return "-e"
    elif key == "version":
        return "--app-version"
    elif key == "patch_profile":
        return "--profile"
    elif key == "os_requirements":
        return "--min-sys-version"
    else:
        pass

def runpatchcli(**kwargs):
    patchOptions = OrderedDict()
    for arg in kwargs:
        if kwargs[arg] != None:
            cliOption = patchcliOptions(arg)
            if arg == "application_path":
                pass
            else:
                patchOptions[cliOption] = kwargs[arg]
                # print(cliOption, patchOptions[cliOption])
        else:
            exit
    if len(patchOptions) != 0:
        if len(patchOptions) == 1:
            optionList=list(patchOptions.keys())
            call(["/usr/local/bin/patchcli", "patch", kwargs["application_path"], optionList[0], patchOptions[optionList[0]], "--patch-only"])
        elif len(patchOptions) == 2:
            optionList=list(patchOptions.keys())
            call(["/usr/local/bin/patchcli", "patch", kwargs["application_path"], optionList[0], patchOptions[optionList[0]], optionList[1], patchOptions[optionList[1]], "--patch-only"])
        elif len(patchOptions) == 3:
            optionList=list(patchOptions.keys())
            call(["/usr/local/bin/patchcli", "patch", kwargs["application_path"], optionList[0], patchOptions[optionList[0]], optionList[1], patchOptions[optionList[1]], optionList[2], patchOptions[optionList[2]], "--patch-only"])
        elif len(patchOptions) == 4:
            optionList=list(patchOptions.keys())
            call(["/usr/local/bin/patchcli", "patch", kwargs["application_path"], optionList[0], patchOptions[optionList[0]], optionList[1], patchOptions[optionList[1]], optionList[2], patchOptions[optionList[2]], optionList[3], patchOptions[optionList[3]], "--patch-only"])
        elif len(patchOptions) == 5:
            optionList=list(patchOptions.keys())
            call(["/usr/local/bin/patchcli", "patch", kwargs["application_path"], optionList[0], patchOptions[optionList[0]], optionList[1], patchOptions[optionList[1]], optionList[2], patchOptions[optionList[2]], optionList[3], patchOptions[optionList[3]], optionList[4], patchOptions[optionList[4]],"--patch-only"])
        else:
            optionList=list(patchOptions.keys())
            call(["/usr/local/bin/patchcli", "patch", kwargs["application_path"], optionList[0], patchOptions[optionList[0]], optionList[1], patchOptions[optionList[1]], optionList[2], patchOptions[optionList[2]], optionList[3], patchOptions[optionList[3]], optionList[4], patchOptions[optionList[4]], optionList[5], patchOptions[optionList[5]],"--patch-only"])
    else:
        call(["/usr/local/bin/patchcli", "patch", kwargs["application_path"], "--patch-only"])
    

def main():
    keyInputs = {
        "application_path": patch1.application_path,
        "version": patch1.version,
        "os_requirements": patch1.os_requirements,
        "publisher": patch1.publisher,
        "extension_attribute": patch1.extension_attribute,
        "file_output_location": patch1.file_output_location,
        "patch_profile": patch1.patch_profile
    }
    for patchVar in keyInputs:
        value = userInput(patchVar)
        keyInputs[patchVar] = value
    runpatchcli(**keyInputs)

if __name__ == "__main__":
    patch1 = patchUpdater()
    main()
