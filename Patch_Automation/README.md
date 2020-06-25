# Patch Server Automation (BETA)
Written in and compatible with Python 3.8

* This automation is designed to work with a Slack channel set up to recieve incoming webhooks.
* This automation is designed to use preference files for jamf pro server, patch server, log location and slack room information.
* This has been adapted from a highly customized environment and should be thoroughly tested for compatibility.
* This requires the `requests` module
  * pip3 install requests
  * sudo pip3 install requests


### Automation tips
* Create a two separate LaunchDaemons and set them to run at whatever interval works best for your environment that runs a symlinked command located at /usr/local/bin
  * Put them either in /Library/LaunchAgents or /Users/<user>/LaunchAgents
* Create a folder in /usr/local/ to put the scripts into
  * ex. /usr/local/<ORG>
* Make the scripts executable
  * chmod +x /usr/local/<ORG>/<script>
* Make a symlink in /usr/local/bin so it is recognized in the normal PATH
  * ln -s /path/to/script.py /usr/local/bin/<command name>

### Preference file
Add preferences with __defaults write__ to a preference file in ~/Library/Preferences called com.github.patch.automation
* note that preferences will also be pulled from an autopkg preference file as well for Jamf servers

Required keys:
* "JSS_URL"
  * Can be pulled from com.github.autopkg preference file and does not need to be in both. If this is in both preference files, the value in com.github.patch.automation will take precedence.
* "API_USERNAME"
  * Can be pulled from com.github.autopkg preference file and does not need to be in both. If this is in both preference files, the value in com.github.patch.automation will take precedence.
* "API_PASSWORD"
  * Can be pulled from com.github.autopkg preference file and does not need to be in both. If this is in both preference files, the value in com.github.patch.automation will take precedence.
* "PATCH_REPO"
  * This is the github repo for your JSON files related to patch. If these do not live in github, this location is still needed but the github commands will likely show up as failures in the log
* "PATCH_URL"
  * Include the full patchserver address including port

Optional keys:
* "PATCH_TOKEN"
  * If you are using an API token on the patchserver, include this key
* "LOG_LOCATION"
  * This isn't required and will default to /Users/<currentUser>/Library/Logs/Patch_Automation
