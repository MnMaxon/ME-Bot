import dataclasses
import logging

import requests

FORM_URLENCODED = "application/x-www-form-urlencoded"
DEFAULT_DISCORD_API_ENDPOINT = "https://discord.com/api/v10"

_logger = logging.getLogger(__name__)


def get_form_encoded_headers():
    return {"Content-Type": FORM_URLENCODED}


@dataclasses.dataclass
class Requestor:
    pass


@dataclasses.dataclass
class DiscordRequestor(Requestor):
    bot_id: int
    oauth_secret: str
    oauth_redirect_uri: str
    api_endpoint: str = DEFAULT_DISCORD_API_ENDPOINT

    def get_auth_tuple(self):
        return str(self.bot_id), self.oauth_secret

    # Gets account information about user
    def get_oauth_info(self, token_dict: dict[str, str]):
        headers = {
            "Authorization": f"{token_dict['token_type']} {token_dict['access_token']}"
        }
        r = requests.get("%s/oauth2/@me" % self.api_endpoint, headers=headers)
        # _logger.info(r.json())
        r.raise_for_status()
        return r.json()

    # TODO Document
    def exchange_code(self, code) -> dict[str, str]:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.oauth_redirect_uri,
        }
        headers = get_form_encoded_headers()
        r = requests.post(
            "%s/oauth2/token" % self.api_endpoint,
            data=data,
            headers=headers,
            auth=self.get_auth_tuple(),
        )
        try:
            r.raise_for_status()
        except Exception as ex:
            _logger.info(f"Failed to process oauth response: {r.json()}")
            raise ex
        return r.json()

    # Bot token requests?
    def get_bot_token_dict(self, session, scope="identify connections"):
        data = {
            "grant_type": "client_credentials",  # client_credentials always gives the bot owner
            "redirect_uri": self.oauth_redirect_uri,
            "scope": scope,
        }
        r = session.post(
            "%s/oauth2/token" % self.api_endpoint,
            data=data,
            headers=get_form_encoded_headers(),
        )
        r.raise_for_status()
        return r.json()


@dataclasses.dataclass
class MERequestor(Requestor):
    pass
