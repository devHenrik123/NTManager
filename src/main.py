from typing import Any

from discord import Intents, Bot
from discord.ext import commands, tasks
from discord.ext.commands import Context

from background_tasks.task_daily_race_logs import task_daily_race_logs
from background_tasks.task_inactivity_alerts import task_inactivity_alerts
from commands.command_setup import command_setup
from commands.command_verify import command_verify
from meta_world import MetaWorld
from util import EnvVars


def main() -> None:
    intents: Intents = Intents(
        guilds=True,
        messages=True,
        message_content=True,
        members=True
    )

    if EnvVars["operation_mode"] == "development":
        bot: Bot = Bot(
            intents=intents,
            sync_commands=False,
            auto_sync_commands=False,
            default_guild_ids=[int(EnvVars["dev_server_id"])]
        )
    else:
        bot: Bot = Bot(intents=intents)

    @tasks.loop(hours=24)
    async def daily_background_tasks() -> Any:
        print("run daily trigger")
        await task_inactivity_alerts(bot)
        await task_daily_race_logs(bot)

    @tasks.loop(minutes=10)
    async def meta_world_cleaner() -> Any:
        print("run meta world cleaner")
        await MetaWorld.clean()

    @bot.event
    async def on_ready() -> Any:
        meta_world_cleaner.start()
        daily_background_tasks.start()

    @commands.has_permissions(administrator=True)
    @bot.slash_command(description="Admin command for configuring the behaviour of this bot.")
    async def setup(ctx: Context) -> Any:
        await command_setup(ctx)

    @bot.slash_command(description="Verify your profile and link your NT account.")
    async def verify(ctx: Context) -> Any:
        await command_verify(ctx)

    bot.run(EnvVars["discord_bot_token"])


if __name__ == '__main__':
    main()
