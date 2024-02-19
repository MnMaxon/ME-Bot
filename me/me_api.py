import asyncio
import json
import os
from pprint import pprint
from typing import Union, List, Dict, Any

import requests
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from me.me_client import client

API_ENDPOINT = os.environ.get('DISCORD_API_ENDPOINT', 'https://discord.com/api/v10')
CLIENT_ID = os.environ['ME_BOT_ID']
CLIENT_SECRET = os.environ['OAUTH_SECRET']
REDIRECT_URI = os.environ['OAUTH_REDIRECT_URI']
print("REDIRECT URI!")
print(REDIRECT_URI)

app = FastAPI()

startup_wait = 4


@app.get("/")
async def hello_world():
    return {"hello": "world"}


@app.get("/hello/")
async def hello_world2():
    return {"hello": "world"}


@app.on_event("startup")
async def startup_event():  # this function will run before the main API starts
    print("Beginning startup_event")
    try:
        # await client.start(client.token)
        token = os.environ['ME_RUN_TOKEN']
        asyncio.create_task(client.start(token))
        print(f"Started client, waiting for {startup_wait} seconds for connectivity...")
        await asyncio.sleep(startup_wait)  # optional sleep for established connection with discord
    except KeyboardInterrupt:
        await client.logout()

    print(f"{client.user} has connected to Discord!")
    print(f"startup_event complete for ME Bot")


def get_user_info(session, token_dict):
    data = {
        # 'grant_type': 'authorization_code',
        # 'code': code,
        # 'redirect_uri': REDIRECT_URI
    }
    headers = {
        # 'Content-Type': 'application/x-www-form-urlencoded',
        # "Content-Type": "application/json",
        # "Authorization": f'{token_dict['token_type']} {token_dict['access_token']}'
        # "authorization": f'{token_dict['token_type']} ',

    }
    # r = session.get('%s/users/@me' % API_ENDPOINT, data=data, headers=headers)
    print(session.headers) # TODO DELETE THIS
    r = session.get('%s/oauth2/@me' % API_ENDPOINT, data=data, headers=session.headers) #TODO THIS FOR BOTS WRONG!
    # r = session.get('%s/oauth2/@me' % API_ENDPOINT, data=data, headers=session.headers)
    # r = session.get('%s/users/@me' % API_ENDPOINT, data=data, headers=session.headers)
    print(r)
    print(r.json())
    r.raise_for_status()
    return r.json()

def get_oauth_info(token_dict):
    headers = {
        # 'Content-Type': 'application/x-www-form-urlencoded',
        # "Content-Type": "application/json",
        "Authorization": f'{token_dict['token_type']} {token_dict['access_token']}'
        # "authorization": f'{token_dict['token_type']} ',
    }
    r = requests.get('%s/oauth2/@me' % API_ENDPOINT, headers=headers) #TODO THIS FOR BOTS WRONG!
    print(r.json())
    r.raise_for_status()
    return r.json()


def exchange_code(session, code):
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post('%s/oauth2/token' % API_ENDPOINT, data=data, headers=headers,  auth=(CLIENT_ID, CLIENT_SECRET))
    try:
        r.raise_for_status()
    except Exception as ex:
        print(f"Failed to process ouath response: {r.json()}")
        raise ex
    return r.json()


def exchange_code_disc(code):
    print("CODE",code)
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post('%s/oauth2/token' % API_ENDPOINT, data=data, headers=headers, auth=(CLIENT_ID, CLIENT_SECRET))
    print(r.json())
    r.raise_for_status()
    return r.json()


def refresh_token_disc(refresh_token):
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = requests.post('%s/oauth2/token' % API_ENDPOINT, data=data, headers=headers, auth=(CLIENT_ID, CLIENT_SECRET))
    print(r.json())
    r.raise_for_status()
    return r.json()


def get_bot_token_dict(session, scope='identify connections'):
    data = {
        'grant_type': 'client_credentials',  # client_credentials always gives the bot owner
        'redirect_uri': REDIRECT_URI,
        'scope': scope
    }
    # if code is not None:
    #     print("ADDING CODE!!!")
    #     data['code'] = code
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    r = session.post('%s/oauth2/token' % API_ENDPOINT, data=data, headers=headers)
    r.raise_for_status()
    return r.json()


@app.get('/oauth/callback')
def callback(code=None):
    # if True:
    #     return bot_oauth()

    session = requests.Session()
    session.auth = (CLIENT_ID, CLIENT_SECRET)
    # bot_token = get_bot_token_dict(session=session)
    token_dict = exchange_code(session, code=code)
    session.headers.update({'Authorization': f'Bearer {token_dict['access_token']}'})
    user_auth = get_oauth_info(token_dict)
    print('User Oauth',user_auth)  # TODO Why can't I do anything with token?

    # return RedirectResponse('/')
    return 'SUCCESS'

    # return uri, state
