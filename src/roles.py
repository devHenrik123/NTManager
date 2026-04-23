from enum import StrEnum, auto

from discord import Guild, Role
from discord.utils import get


class RoleName(StrEnum):
    Verified = "Verified"
    TeamMember = "Team Member"


async def get_role_safe(server: Guild, role_name: RoleName) -> Role:
    """
    Gets a role from the given server / guild. If it does not exist, then the role will be created.
    :param server: Guild / server instance
    :param role_name: Name of desired role
    :return: instance of Role
    """
    role: Role = get(server.roles, name=role_name)
    if not role:
        role = await server.create_role(name=role_name)
    return role
