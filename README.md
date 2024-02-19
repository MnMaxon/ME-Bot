# ME-Bot
Custom Discord Bot for Meme Elitists

# Setup
Installation
* Install Python (app written for Python 3.12)
* Run: pip install {path_to_code}/requirements.txt
* Set up MultiFactor Authentication On your Discord account
  * You may get this error if you don't - discord.errors.Forbidden: 403 Forbidden (error code: 50001): Missing Access


Run
* Run the main.py for command help
* To start app, run: python main.py run
* Required Env Variables:
  * ME_RUN_TOKEN: Discord Client Token
  * ME_BOT_ID: Discord Bot ID
  * OAUTH_URL
  * OAUTH_SECRET
  * OAUTH_REDIRECT_URI
* Optional Env Variables:
  * ME_RUN_GUILDS ={guild1},{guild2},{...}
    * For Dev - Updates the commands immediately for these guilds - Can take ~1 hour to sync to all servers normally

# Technical Information
Stores data in csv files in /data

Handles command line through click

app.yaml and .gcloudignore include for Google App Engine deployment

Using GCloud for API hosting