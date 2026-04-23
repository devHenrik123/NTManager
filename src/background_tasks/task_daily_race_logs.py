from dataclasses import dataclass

from discord import Bot
from discord.abc import GuildChannel

from nt_api import Team, NTAPI, TeamMember, UserIdentity
from persistent_data import Persistence, RaceLogEntry
from ui.embeds import DefaultEmbed


@dataclass
class RaceLog24Hours:
    log_entry: RaceLogEntry
    race_count_24_h: int


async def task_daily_race_logs(bot: Bot) -> None:
    for server in Persistence.get().servers:
        if server.daily_race_logs:
            alert_channel: GuildChannel = bot.get_channel(int(server.daily_race_logs.channel))
            if not alert_channel:
                continue  # channel not found -> skip

            team: Team = NTAPI.get_team(server.team.tag)
            members_map: dict[str, TeamMember] = dict((str(x.identity.id), x) for x in team.members)

            is_first_log: bool = server.daily_race_logs.previous_log_entries is None

            previous: dict[str, RaceLogEntry] = {} \
                if is_first_log \
                else dict((e.user_id, e) for e in server.daily_race_logs.previous_log_entries)
            new: dict[str, RaceLog24Hours] = {}
            for member in team.members:
                nt_user_id: str = str(member.identity.id)
                race_count_before: int = previous.get(nt_user_id, RaceLogEntry(nt_user_id, 0)).race_count
                race_count_now: int = member.team_races
                race_count_24_h: int = max(race_count_now - race_count_before, 0)
                new[nt_user_id] = RaceLog24Hours(
                    RaceLogEntry(nt_user_id, race_count_now),
                    race_count_24_h
                )

            server.daily_race_logs.previous_log_entries = [x.log_entry for x in new.values()]
            Persistence.write()

            if not is_first_log:
                total_race_count_24_h: int = sum(x.race_count_24_h for x in new.values())
                text: str = (f"A total of {total_race_count_24_h} races have been completed for team {server.team.tag} "
                             f"during the last 24 hours.\n\n")

                for entry_24_h in sorted(new.values(), key=lambda x: -x.race_count_24_h):
                    user: UserIdentity = members_map[entry_24_h.log_entry.user_id].identity
                    display_name: str = user.display_name if user.display_name else user.username
                    text += f"{entry_24_h.race_count_24_h} [{display_name}](https://www.nitrotype.com/racer/{user.username})\n"

                # noinspection PyUnresolvedReferences
                await alert_channel.send(
                    embed=DefaultEmbed(
                        title="Daily Race Log",
                        description=text
                    )
                )
