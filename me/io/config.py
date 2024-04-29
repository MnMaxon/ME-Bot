import os
from dataclasses import dataclass, fields


@dataclass
class Config:
    me_run_token: str
    me_bot_id: int  # kind of a str
    oauth_secret: str
    oauth_url: str
    oauth_redirect_uri: str
    website_url: str = "http://localhost:3000/"

    # Used for instant updates on startup, not necessary
    me_run_guilds: str = ""
    discord_api_endpoint: str = "https://discord.com/api/v10"


def get_config(use_env_vars=True, **kwargs) -> Config:
    conf_vars = {}
    if use_env_vars:
        conf_vars.update(get_config_env_vars())

    # TODO One day calculate with redirect_ui
    # OAUTH_URL: 'https://discord.com/api/oauth2/authorize?client_id={client_id}&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Foauth%2Fcallback&response_type=code&scope=identify' TODO SHOULD BE CALCULATED?!
    # if 'oauth_url' not in kwargs:
    #     kwargs['oauth_url']=f'https://discord.com/api/oauth2/authorize?client_id={kwargs['me_bot_id']}&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Foauth%2Fcallback&response_type=code&scope=identify'

    conf_vars.update(kwargs)
    return Config(**conf_vars)


def get_config_env_vars():
    env_vars = {}
    for f in fields(Config):
        var_val = get_env_var(f.name)
        if var_val is not None:
            env_vars[f.name] = var_val
    return env_vars


def get_env_var(var_name):
    for me_name in [f"me_{var_name}", var_name]:
        for case_name in [me_name.upper(), me_name.lower()]:
            if case_name in os.environ:
                return os.environ[case_name]
    return None


def get_example_dict(**kwargs):
    conf_vars = kwargs.copy()
    def_vars = {
        "me_run_token": "vdshsv44553",
        "me_bot_id": 135163,  # kind of a str,
        "oauth_secret": "f3tt43w",
        "oauth_url": f"https://discord.com/api/oauth2/authorize?client_id={kwargs['me_bot_id']}&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Foauth%2Fcallback&response_type=code&scope=identify",
        "oauth_redirect_uri": "http://127.0.0.1:8000/oauth/callback",
        "me_run_guilds": [5376],
    }
    conf_vars.update(def_vars)
    return get_config(use_env_vars=False, **conf_vars)
