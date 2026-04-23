from asyncio import sleep
from dataclasses import dataclass
from datetime import timedelta, datetime
from random import choice
from typing import cast, Final

from discord import Interaction, ChannelType, Role
from discord.ext.commands import Context
from discord.ui import View, Modal, button, Button, InputText

from meta_world import MetaObject, MetaWorld
from nt_api import Account, NTAPI, AccountNotFoundError, Car
from persistent_data import Persistence
from roles import get_role_safe, RoleName
from ui.embeds import DefaultEmbed


@dataclass
class VerificationData:
    account: Account
    new_car: Car
    start_time: datetime


class VerificationProcess(MetaObject):
    MaximumAllowedDurationInMinutes: Final[int] = 60

    def __init__(self, id_: str, account: Account) -> None:
        super().__init__(id_, timedelta(minutes=VerificationProcess.MaximumAllowedDurationInMinutes))
        self._data_model: VerificationData = VerificationData(
            account,
            choice([c for c in account.cars if c.id != account.selected_car.id]),
            datetime.now()
        )

    @property
    def data(self) -> VerificationData:
        return self._data_model

    @staticmethod
    def get_id(guild_id: int, user_id: int) -> str:
        return f"{guild_id}_{user_id}_command_verify"

    @staticmethod
    def get_instance(guild_id: int, user_id: int) -> "VerificationProcess":
        return cast(VerificationProcess, MetaWorld.get(VerificationProcess.get_id(guild_id, user_id)))


# ====================================================================================================================
#   5 - Verified!
# ====================================================================================================================

async def step_5_verified(interaction: Interaction) -> None:
    thread = await interaction.channel.create_thread(name="Verification", type=ChannelType.private_thread)
    await thread.add_user(interaction.user)

    await thread.send(
        embed=DefaultEmbed(
            title=f"Verification",
            description=(
                f"{interaction.user.mention} Your accounts has successfully been verified!"
            )
        )
    )

# ====================================================================================================================
#   4 - Could not verify
# ====================================================================================================================

async def step_4_could_not_verify(interaction: Interaction) -> None:
    thread = await interaction.channel.create_thread(name="Verification", type=ChannelType.private_thread)
    await thread.add_user(interaction.user)

    await thread.send(
        embed=DefaultEmbed(
            title=f"Verification",
            description=(
                f"{interaction.user.mention} "
                f"Verification of your account failed.\n"
                f"Please try again later."
            )
        )
    )

# ====================================================================================================================
#   3 - Verify
# ====================================================================================================================

async def step_3_verify(interaction: Interaction) -> None:
    process: VerificationProcess = VerificationProcess.get_instance(interaction.guild_id, interaction.user.id)
    this_guilds_nt_team_id: int = NTAPI.get_team(Persistence.get_server(str(interaction.guild.id)).team.tag).id
    is_verified: bool = False
    is_team_member: bool = this_guilds_nt_team_id == process.data.account.team_id
    delay_between_check_in_s: float = 120

    while not is_verified and datetime.now() < process.destruction_date:
        account: Account = NTAPI.get_account(process.data.account.identity.username)
        is_verified = account.selected_car.id == process.data.new_car.id

        if not is_verified:
            await sleep(delay_between_check_in_s)

    if is_verified:
        role_verified: Role = await get_role_safe(interaction.guild, RoleName.Verified)
        role_team_member: Role = await get_role_safe(interaction.guild, RoleName.TeamMember)
        await interaction.user.add_roles(role_verified)
        if is_team_member:
            await interaction.user.add_roles(role_team_member)
        await step_5_verified(interaction)
    else:
        await step_4_could_not_verify(interaction)


# ====================================================================================================================
#   2 - Confirmation and Start Verification Process
# ====================================================================================================================

async def step_2_confirm_and_start_verification_process(interaction: Interaction, process: VerificationProcess) -> None:
    await interaction.respond(
        embed=DefaultEmbed(
            title=f"Verification",
            description=(
                f"{interaction.user.mention} "
                f"The verification for **{process.data.account.identity.username} ({process.data.account.identity.display_name})** is now in progress.\n"
                f"To prove that you are the owner of the account, please change your selected car to **{process.data.new_car.name}**.\n\n"
                f"It may take a couple of minutes for the verification process to complete.\n"
                f"Please wait until then. You will be notified upon completion."
            )
        ),
        ephemeral=True
    )
    await step_3_verify(interaction)

# ====================================================================================================================
#   1.5 - Invalid Username
# ====================================================================================================================

async def step_1_5_invalid_username(interaction: Interaction, username: str) -> None:
    await interaction.respond(
        embed=DefaultEmbed(
            title=f"Verification",
            description=(
                f"{interaction.user.mention} "
                f"The given username **\"{username}\"** does not belong to a valid NitroType account. "
                f"Please make sure to enter a valid username.\n\n"
                f"*(Important: The username is different from your display name. Your username is the name you use"
                f" to sign into your account and which is part of the url of your public profile. Please make sure "
                f"to use this, instead of the display name.)*"
            )
        ),
        view=Step_0_StartVerification(),
        ephemeral=True
    )

# ====================================================================================================================
#   1 - Enter Username
# ====================================================================================================================

class Step_1_EnterUsername(Modal):  # noqa 801
    def __init__(self):
        super().__init__(
            title="Enter NT Username"
        )

        self._username: InputText = InputText(
            label="Your NT username:",
            placeholder="Username",
            required=True
        )
        self.add_item(self._username)

    async def callback(self, interaction: Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        username: str = self._username.value

        try:
            account: Account = NTAPI.get_account(username)
            process: VerificationProcess = VerificationProcess(
                VerificationProcess.get_id(interaction.guild_id, interaction.user.id),
                account
            )
            MetaWorld.add(process)
            await step_2_confirm_and_start_verification_process(interaction, process)

        except (AccountNotFoundError, IndexError):
            await step_1_5_invalid_username(interaction, username)

# ====================================================================================================================
#   0.5 - Verification is already in progress
# ====================================================================================================================

async def step_0_5_verification_already_in_progress(ctx: Context, process: VerificationProcess) -> None:
    time_left_minutes: int = int((process.destruction_date - datetime.now()).total_seconds() / 60)

    # noinspection PyUnresolvedReferences
    await ctx.respond(
        embed=DefaultEmbed(
            title=f"Verification",
            description=(
                f"{ctx.author.mention} "
                f"Verification of your account (*{process.data.account.identity.username}*) is already in progress.\n"
                f"If you have not done so, yet: Please change your selected car to the **{process.data.new_car.name}**.\n"
                f"It may take up to {time_left_minutes} minutes until your verification is complete.\n"
                f"Please wait until then. You will be notified upon completion."
            )
        ),
        ephemeral=True
    )

# ====================================================================================================================
#   0 - Start
# ====================================================================================================================

class Step_0_StartVerification(View):  # noqa 801
    @button(label="Start Verification")
    async def button_start_verification(self, _: Button, interaction: Interaction) -> None:
        await interaction.response.send_modal(Step_1_EnterUsername())


async def command_verify(ctx: Context) -> None:
    # noinspection PyUnresolvedReferences
    await ctx.response.defer(ephemeral=True)

    process: VerificationProcess | None = VerificationProcess.get_instance(ctx.guild.id, ctx.author.id)
    if process:
        await step_0_5_verification_already_in_progress(ctx, process)
    else:
        # noinspection PyUnresolvedReferences
        await ctx.respond(
            embed=DefaultEmbed(
                title=f"Verification",
                description=(
                    f"{ctx.author.mention} "
                    f"The verification process will link a NitroType account to your discord account. "
                    f"You can not add multiple NT accounts to your discord account. In the future, if you want to link a "
                    f"different NT account to your server profile, just run the */verify* command again.\n"
                    f"Press the button below to start the verification process."
                )
            ),
            view=Step_0_StartVerification(),
            ephemeral=True
        )
