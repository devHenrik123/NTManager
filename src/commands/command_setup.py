from datetime import timedelta
from typing import cast

from discord import Interaction, ButtonStyle, SelectOption
from discord.abc import GuildChannel
from discord.ext.commands import Context
from discord.ui import button, Button, View, Modal, InputText, select, Select

from meta_world import MetaObject, MetaWorld
from persistent_data import Persistence, Server, DailyRaceLogs, InactivityAlerts, Team
from ui.embeds import DefaultEmbed
from ui.select_channel_view import SelectChannelView


class TempInMemorySetup(MetaObject):
    def __init__(self, id_: str) -> None:
        super().__init__(id_, timedelta(minutes=30))
        self._inactive_members_channel: GuildChannel | None = None
        self._max_inactivity_duration: timedelta | None = None
        self._daily_race_logs_channel: GuildChannel | None = None
        self._team_tag: str | None = None

    @property
    def inactive_members_channel(self):
        return self._inactive_members_channel

    @inactive_members_channel.setter
    def inactive_members_channel(self, value):
        self._inactive_members_channel = value

    @property
    def max_inactive_duration(self):
        return self._max_inactivity_duration

    @max_inactive_duration.setter
    def max_inactive_duration(self, value):
        self._max_inactivity_duration = value

    @property
    def daily_race_logs_channel(self):
        return self._daily_race_logs_channel

    @daily_race_logs_channel.setter
    def daily_race_logs_channel(self, value):
        self._daily_race_logs_channel = value

    @property
    def team_tag(self):
        return self._team_tag

    @team_tag.setter
    def team_tag(self, value):
        self._team_tag = value



def get_setup_id(interaction: Interaction) -> str:
    return f"{interaction.guild_id}_{interaction.user.id}_command_setup"


def get_setup(interaction: Interaction) -> TempInMemorySetup:
    return cast(TempInMemorySetup, MetaWorld.get(get_setup_id(interaction)))


# ====================================================================================================================
#   4 - Confirm And Exit
# ====================================================================================================================

class Step_4_ConfirmAndExit(View):  # noqa 801
    # noinspection PyTypeChecker
    @button(label="Save", style=ButtonStyle.green)
    async def _button_save(self, _: Button, interaction: Interaction) -> None:
        tmp_setup: TempInMemorySetup = get_setup(interaction)

        server: Server = Persistence.get_server(str(interaction.guild.id))
        server.team = Team(tmp_setup.team_tag)
        server.daily_race_logs = DailyRaceLogs(tmp_setup.daily_race_logs_channel.id, None) if tmp_setup.daily_race_logs_channel else None
        server.inactivity_alerts = InactivityAlerts(
            tmp_setup.inactive_members_channel.id,
            tmp_setup.max_inactive_duration.days
        ) if tmp_setup.inactive_members_channel else None
        Persistence.write()

        await interaction.respond(
            embed=DefaultEmbed(
                title="Setup Finished",
                description="The Setup has now finished and the changes were saved."
            ),
            ephemeral=True
        )

    # noinspection PyTypeChecker
    @button(label="Restart", style=ButtonStyle.red)
    async def _button_restart(self, _: Button, interaction: Interaction) -> None:
        await step_1_link_nt_team(interaction)


async def step_4_confirm_and_exit(interaction: Interaction) -> None:
    setup: TempInMemorySetup = get_setup(interaction)
    setup_report: str = f"- **Team Tag:** *{setup.team_tag}*\n"
    if setup.inactive_members_channel:
        setup_report += (f"- **Inactivity Alerts Channel:** *{setup.inactive_members_channel.mention}*\n"
                         f"- **Inactivity Duration:** *{setup.max_inactive_duration.days} days*\n")
    else:
        setup_report += "- **No Inactivity Alerts**\n"
    if setup.daily_race_logs_channel:
        setup_report += f"- **Daily Race Logs Channel:** *{setup.daily_race_logs_channel.mention}*\n"
    else:
        setup_report += "- **No Daily Race Logs**\n"
    await interaction.respond(
        embed=DefaultEmbed(
            title="Setup Review",
            description=f"You have now entered all required information. Please review the settings below:\n\n"
                        f"{setup_report}\n\n"
                        f"(If you would like to edit your settings in the future, just use the /setup command again.)"
        ),
        view=Step_4_ConfirmAndExit(),
        ephemeral=True
    )

# ====================================================================================================================
#   3 - Daily Race Logs
# ====================================================================================================================

class Step_3_ChannelSelect(SelectChannelView):  # noqa 801
    def __init__(self):
        super().__init__(callback=Step_3_ChannelSelect._on_channel_selected)

    @staticmethod
    async def _on_channel_selected(interaction: Interaction, value: GuildChannel) -> None:
        get_setup(interaction).daily_race_logs_channel = value
        await step_4_confirm_and_exit(interaction)


class Step_3_WouldYouLikeToReceiveLogs(View):  # noqa 801
    # noinspection PyTypeChecker
    @button(label="Yes", style=ButtonStyle.green)
    async def _button_yes(self, _: Button, interaction: Interaction) -> None:
        await interaction.respond(
            embed=DefaultEmbed(
                title="Daily Race Logs",
                description="Please select a channel from the list below, which the daily race logs should be posted to."
            ),
            view=Step_3_ChannelSelect(),
            ephemeral=True
        )

    # noinspection PyTypeChecker
    @button(label="No", style=ButtonStyle.red)
    async def _button_no(self, _: Button, interaction: Interaction) -> None:
        await step_4_confirm_and_exit(interaction)


async def step_3_loremipsum(interaction: Interaction) -> None:
    await interaction.respond(
        embed=DefaultEmbed(
            title="Daily Race Logs",
            description="Would you like to receive daily race logs?"
        ),
        view=Step_3_WouldYouLikeToReceiveLogs(),
        ephemeral=True
    )


# ====================================================================================================================
#   2 - Inactive Member Alerts
# ====================================================================================================================


class Step_2_SelectInactivityDuration(View):  # noqa 801
    @select(
        placeholder="Duration In Days",
        min_values=1,
        max_values=1,
        options=[SelectOption(label=str(i)) for i in list(range(1, 8)) + [14, 30]]
    )
    async def _on_duration_selected(self, sel: Select, interaction: Interaction) -> None:
        selected_value: str = sel.values[0]
        get_setup(interaction).max_inactive_duration = timedelta(days=int(selected_value))
        await step_3_loremipsum(interaction)


class Step_2_ChannelSelect(SelectChannelView):  # noqa 801
    def __init__(self):
        super().__init__(callback=Step_2_ChannelSelect._on_channel_selected)

    @staticmethod
    async def _on_channel_selected(interaction: Interaction, value: GuildChannel) -> None:
        get_setup(interaction).inactive_members_channel = value
        await interaction.respond(
            embed=DefaultEmbed(
                title="Inactive Member Alerts",
                description="Please select a duration from the list below, after which a team member is flagged for inactivity.\n"
                            "(The duration is set in days. So for example, if you select '5', team members will be alerted after 5 days without racing.)"
            ),
            view=Step_2_SelectInactivityDuration(),
            ephemeral=True
        )


class Step_2_DoYouWishToReceiveInactiveAlerts(View):  # noqa 801
    # noinspection PyTypeChecker
    @button(label="Yes", style=ButtonStyle.green)
    async def button_yes(self, _: Button, interaction: Interaction) -> None:
        await interaction.respond(
            embed=DefaultEmbed(
                title="Inactive Member Alerts",
                description="Please select a channel below, in which to send the alerts."
            ),
            view=Step_2_ChannelSelect(),
            ephemeral=True
        )

    # noinspection PyTypeChecker
    @button(label="No", style=ButtonStyle.red)
    async def button_no(self, _: Button, interaction: Interaction) -> None:
        await step_3_loremipsum(interaction)


async def step_2_set_inactive_members_channel(interaction: Interaction) -> None:
    await interaction.respond(
        embed=DefaultEmbed(
            title="Inactive Member Alerts",
            description="Do you wish to enable inactivity alerts, if NT team members have not raced in a long time?"
        ),
        view=Step_2_DoYouWishToReceiveInactiveAlerts(),
        ephemeral=True
    )

# ====================================================================================================================
#   1 - Link NT Team
# ====================================================================================================================

class Step_1_LinkTeamInput(Modal):  # noqa 801
    def __init__(self):
        super().__init__(
            title="Link Team"
        )

        self._team_tag: InputText = InputText(
            label="Tag of your NitroType Team (e.g. ZH)",
            placeholder="##",
            required=True
        )
        self.add_item(self._team_tag)

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        get_setup(interaction).team_tag = self._team_tag.value.strip().upper()
        await step_2_set_inactive_members_channel(interaction)


class Step_1_PleaseLinkATeam(View):  # noqa 801
    @button(label="Set Team")
    async def button_set_team(self, _: Button, interaction: Interaction) -> None:
        await interaction.response.send_modal(Step_1_LinkTeamInput())


async def step_1_link_nt_team(interaction: Interaction) -> None:
    await interaction.respond(
        embed=DefaultEmbed(
            title="Link NT Team",
            description="On the following page, please enter the tag associated with your NT team."
        ),
        view=Step_1_PleaseLinkATeam(),
        ephemeral=True
    )

# ====================================================================================================================
#   0 - Start
# ====================================================================================================================

class Step_0_StartSetup(View):  # noqa 801
    @button(label="Start Setup")
    async def button_start_setup(self, _: Button, interaction: Interaction) -> None:
        self.disable_all_items()
        await interaction.response.edit_message(view=self)
        MetaWorld.add(TempInMemorySetup(get_setup_id(interaction)))
        await step_1_link_nt_team(interaction)


async def command_setup(ctx: Context) -> None:
    # noinspection PyUnresolvedReferences
    await ctx.response.defer(ephemeral=True)

    # noinspection PyUnresolvedReferences
    await ctx.respond(
        embed=DefaultEmbed(
            title=f"Setup",
            description=(
                f"{ctx.author.mention} "
                f"Before I can help you with your NT team management, I will need to ask you some questions.\n"
                f"(If you have started this setup procedure on accident, you can just abandon it. "
                f"In that case, nothing will change and your previous settings will stay untouched.)"
            )
        ),
        view=Step_0_StartSetup(),
        ephemeral=True
    )
