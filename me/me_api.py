import asyncio
import os

from fastapi import FastAPI
from me.me_client import client

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
    print("ADDED HELLO ENDPOINT!")
    try:
        # await client.start(client.token)
        token = os.environ['ME_RUN_TOKEN']
        guilds = os.environ.get('ME_RUN_GUILDS')
        if guilds is not None:
            guilds = guilds.replace(";", ",").replace(" ", ",").split(",")
            guilds = [g.strip() for g in guilds]
            guilds = [int(g) for g in guilds if g != ""]
        client.sync_guilds = guilds
        asyncio.create_task(client.start(token))
        print(f"Started client, waiting for {startup_wait} seconds for connectivity...")
        await asyncio.sleep(startup_wait)  # optional sleep for established connection with discord
    except KeyboardInterrupt:
        await client.logout()

    print(f"{client.user} has connected to Discord!")
    print(f"startup_event complete for ME Bot")


@app.get('/oauth/callback')
def callback():
    return "Oauth url"