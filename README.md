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
* To start app, run: python main.py run --token {bot_token}
* Arguments can be replaced with environment variables
  * Format: ME_{COMMAND_NAME}_{ARGUMENT_NAME}
  * Example: ME_RUN_TOKEN
* Optional --guilds argument - Use like --guilds {guild1},{guild2},{...}
  * This will update the commands immediately for those guilds - According to the internet, it can take an hour to sync normally
  * Env Variable: ME_RUN_GUILDS

# Technical Information
Stores data in csv files in /data

Handles command line through click

app.yaml and .gcloudignore include for Google App Engine deployment

Using GCloud for API hosting