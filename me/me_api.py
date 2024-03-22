import asyncio
import dataclasses
import logging

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

from me import session_info
from me.io import config
from me.io.db_util import SQLiteDB
from me.discord_bot.me_client import client
from me.io.requestor import DiscordRequestor

startup_wait = 4

_logger = logging.getLogger(__name__)


class MEFastAPI(FastAPI):
    user_sessions = {}

    def __init__(
            self: FastAPI, cfg=None, discord_requestor: DiscordRequestor = None, **kwargs
    ):
        if cfg is None:
            cfg = config.get_config()
        self.config: config.Config = cfg

        _logger.info("Setting up database...")
        db = SQLiteDB()
        self.db = db
        db.setup()

        if discord_requestor is None:
            discord_requestor = DiscordRequestor(
                cfg.me_bot_id,
                cfg.oauth_secret,
                cfg.oauth_redirect_uri,
                api_endpoint=cfg.discord_api_endpoint,
            )
        self.discord_requestor = discord_requestor
        super().__init__(**kwargs)


app = MEFastAPI()
REDIRECT_URI = app.config.oauth_redirect_uri
API_ENDPOINT = app.config.discord_api_endpoint

origins = [
    "http://localhost:3000*",
    "http://localhost:8000*",
    "http://127.0.0.1:*",
    "*",
]

try:
    website_base = app.config.website_url.lstrip("https").lstrip("http").lstrip(":").lstrip("/").split("/")[0]
    website_base = app.config.website_url.split(website_base, 1)[0] + website_base + "*"
    origins.append(website_base)
except Exception as e:
    print("WARNING: FAILED TO PARSE WEBSITE URL FOR ORIGIN - CODE BAD? ", e)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def hello_world():
    return {"hello": "world"}


@app.get("/hello/")
async def hello_world2():
    return {"hello": "world"}


@app.on_event("startup")
async def startup_event():  # this function will run before the main API starts
    _logger.info("Beginning startup_event")
    try:
        # await client.start(client.token)
        token = app.config.me_run_token
        # _logger.info(f"Started client, waiting for {startup_wait} seconds for connectivity...")
        _logger.info("Starting client...")
        client.me_setup(app.db, app.config)
        asyncio.create_task(client.start(token))
        _logger.info("Client started!")
        await asyncio.sleep(
            startup_wait
        )  # optional sleep for established connection with discord
    except KeyboardInterrupt:
        await client.logout()

    _logger.info(f"{client.user} has connected to Discord!")
    _logger.info("startup_event complete for ME Bot")


@app.get("/oauth/callback")
def callback(code=None, state=None):
    token_dict = app.discord_requestor.exchange_code(code=code)

    # user_auth = app.discord_requestor.get_user_info(token_dict)
    app.user_sessions[state] = session_info.SessionInfo(code, token_dict)
    return RedirectResponse(url=app.config.website_url)


@app.get("/logged-in/")
async def logged_in(session_id: str):
    session_id = str(session_id)
    status = len(session_id) == 16 and session_id in app.user_sessions
    return status


@app.get("/whoami/")
async def whoami(session_id=None):
    session = requests.session()
    # print("COOKIES", session.cookies)
    # if "session_id" in session.cookies:
    #     print(session.cookies["session_id"])
    session.cookies["session_id"] = 123
    # print("->", session.cookies["session_id"])
    # print("-> COOKIES", session.cookies)

    if session_id is None or session_id not in app.user_sessions:
        info = session_info.get_session_info()
    else:
        info = app.user_sessions[session_id]
    ret_dict = dataclasses.asdict(info)
    ret_dict["logged_in"] = info.is_logged_in()
    _logger.info(f"LOGGED IN {ret_dict}")
    return ret_dict
