# Patch Server Automation (BETA)
Written in and compatible with Python 3.8

* This automation is designed to work with a Slack channel set up to recieve incoming webhooks.
* This automation is designed to use preference files for jamf pro server, patch server, log location and slack room information.
* This has been adapted from a highly customized environment and should be thoroughly tested for compatibility.

Automation tips
* Create a two separate LaunchDaemons and set them to run at whatever interval works best for your environment that runs a symlinked command located at /usr/local/bin
  * Put them either in /Library/LaunchAgents or /Users/<user>/LaunchAgents
* Create a folder in /usr/local/ to put the scripts into
  * ex. /usr/local/<ORG>
* Make the scripts executable
  * chmod +x /usr/local/<ORG>/<script>
* Make a symlink in /usr/local/bin so it is recognized in the normal PATH
  * ln -s /path/to/script.py /usr/local/bin/<command name>
