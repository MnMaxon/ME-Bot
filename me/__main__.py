import asyncio
import click
import uvicorn

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
@click.option('--token', '-t', required=False)
@click.option('--guilds', '-g', required=False)
def run(token, guilds):
    print('Starting server')
    print("WARNING COMMAND ARGS NOT WORKING -- MUST USE TOKEN")
    # me_api.client.sync_guilds = guilds
    # me_api.client.token = token
    uvicorn.run("me.me_api:app", host="127.0.0.1", port=1111, reload=True)
    # me_api.client.loop.create_task(uvicorn.run(me_api.app, host="127.0.0.1", port=8080))
    # asyncio.run(me_api.client.start(token))

    # server = uvicorn.Server(config)
    # server.run()
    # api = me_api.MEApi()
    # asyncio.run(api.run_bot(token, guilds))

# async def start_server_and_bot(token):
#     async with asyncio.TaskGroup() as tg:
#         task1 = tg.create_task(client.run(token))
#
#         task2 = tg.create_task(
#             say_after(2, 'world'))
#
#         print(f"started at {time.strftime('%X')}")
#
#     # The await is implicit when the context manager exits.
#
#     print(f"finished at {time.strftime('%X')}")


if __name__ == "__main__":
    main(auto_envvar_prefix='ME')
