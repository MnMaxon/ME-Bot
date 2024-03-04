import asyncio
import logging
import os

import click
import uvicorn
import yaml

_logger = logging.getLogger(__name__)


@click.group(chain=True, invoke_without_command=True, no_args_is_help=True)
@click.version_option(package_name='me')
# @click.option('--debug')
@click.pass_context
def main(ctx):
    ctx.obj = {
        # 'debug': debug,
    }


async def test_message(client):
    print("Sending test event message in 10 seconds")
    await asyncio.sleep(10)
    msg = 'example event message'
    print(f"Sent message after waiting {msg}")
    client.dispatch("test_event", msg=msg)


@main.command()
# @click.option('--token', '-t', required=False)
# @click.option('--guilds', '-g', required=False)
@click.option('--app', '-a', required=False, default="me.me_api:app")
@click.option('--host', '-a', required=False, default="127.0.0.1")
@click.option('--port', '-a', required=False, default=8000, type=int)
@click.option('--reload', '-r', required=False, default=True, type=bool)
@click.option('--env-vars-path', '-e', required=False, type=click.Path(exists=True),
              help='env_variables yaml, imports environment variables -- not secure for secret information')
def run(app, host, port, reload, env_vars_path=None):
    if env_vars_path is not None:
        update_env_vars_from_yml(env_vars_path)

    print(f'Starting server {app} with uvicorn on {host} - port {port} - reload={reload}')
    uvicorn.run(app, host=host, port=port, reload=reload)


def update_env_vars_from_yml(yml_path):
    print(f"Loading env vars from {yml_path}")
    with open(yml_path, "r") as f:
        env = yaml.safe_load(f).get('env_variables', {})
        if len(env) == 0:
            print(f"WARNING: Could not find env_variables in {yml_path}, not overriding environment variables")
        os.environ.update(env)


if __name__ == "__main__":
    main(auto_envvar_prefix='ME')
