from datetime import timedelta, datetime

from discord import Bot
from discord.abc import GuildChannel

from nt_api import Team, NTAPI, UserIdentity
from persistent_data import Persistence
from ui.embeds import DefaultEmbed


async def task_inactivity_alerts(bot: Bot) -> None:
    now: datetime = datetime.now()

    for server in Persistence.get().servers:
        if server.inactivity_alerts:
            alert_channel: GuildChannel = bot.get_channel(int(server.inactivity_alerts.channel))
            if not alert_channel:
                continue  # channel not found -> skip

            team: Team = NTAPI.get_team(server.team.tag)
            max_inactive_duration: timedelta = timedelta(days=server.inactivity_alerts.days)

            inactive_text: str = (f"Some members on team {server.team.tag} are inactive and "
                                  f"have not been racing since {server.inactivity_alerts.days} days. "
                                  f"Those team members are:\n\n")
            for member in team.members:
                last_race_delta: timedelta = now - member.last_race
                is_inactive: bool = last_race_delta > max_inactive_duration
                is_new_member: bool = now - member.member_since < max_inactive_duration
                if is_inactive and not is_new_member:
                    user: UserIdentity = member.identity
                    display_name: str = user.display_name if user.display_name else user.username
                    inactive_text += f" - [{display_name}](https://www.nitrotype.com/racer/{user.username})\n"

            # noinspection PyUnresolvedReferences
            await alert_channel.send(
                embed=DefaultEmbed(
                    title="Inactive Racers Report",
                    description=inactive_text
                )
            )
