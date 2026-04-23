from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from json import loads
from typing import Final
from re import compile as re_compile, M, S

from requests import Response, get


class AccountNotFoundError(Exception):
    pass


@dataclass
class UserIdentity:
    id: int
    username: str
    display_name: str


class AccountStatus(StrEnum):
    Active = "active"
    Banned = "banned"


class TeamMemberRole(StrEnum):
    Captain = "captain"  # <- ! Does not exist in NT API. ! The captain is a regular officer for some reason.
    Officer = "officer"
    Member = "member"


@dataclass
class Car:
    id: int
    name: str


@dataclass
class Account:
    identity: UserIdentity
    selected_car: Car
    cars: list[Car]
    team_id: int | None


@dataclass
class TeamMember:
    identity: UserIdentity
    account_status: AccountStatus
    role: TeamMemberRole
    last_race: datetime
    team_races: int
    member_since: datetime


@dataclass
class Team:
    id: int
    name: str
    tag: str
    captain: UserIdentity
    members: list[TeamMember]


@dataclass
class NTBootstrap:
    cars: list[Car]


class NTAPI(ABC):
    BaseUrl: Final[str] = "https://www.nitrotype.com"
    ApiUrl: Final[str] = BaseUrl + "/api"
    ApiV2Url: Final[str] = ApiUrl + "/v2"
    TeamsUrl: Final[str] = ApiV2Url + "/teams/{team_name}"
    RacerUrl: Final[str] = BaseUrl + "/racer/{username}"
    BootstrapUrl: Final[str] = BaseUrl + "/index/624/bootstrap.js"

    DefaultHeaders: Final[dict] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0"
    }

    _NTBootstrap: NTBootstrap | None = None

    @staticmethod
    def get_bootstrap() -> NTBootstrap:
        if NTAPI._NTBootstrap:
            return NTAPI._NTBootstrap

        # TODO: Add all values to the NTBootstrap class and parse + assign them below!

        resp: Response = get(NTAPI.BootstrapUrl, headers=NTAPI.DefaultHeaders)
        data: list = loads(resp.text[40:-59])
        active_seasons = data.pop(0)
        active_events = data.pop(0)
        achievements = data.pop(0)
        cars = data.pop(0)
        products = data.pop(0)
        cash_bundles = data.pop(0)
        top_players = data.pop(0)
        global_alert = data.pop(0)
        loot = data.pop(0)
        shop = data.pop(0)
        dealerships = data.pop(0)
        leagues = data.pop(0)
        challenges = data.pop(0)
        stripe_key = data.pop(0)
        stripe_api_version = data.pop(0)
        world_descriptions = data.pop(0)
        lesson_descriptions = data.pop(0)
        starting_cars = data.pop(0)
        friend_limits = data.pop(0)
        page_labels = data.pop(0)
        player_levels = data.pop(0)
        one_way_friend_ids = data.pop(0)
        team_info = data.pop(0)
        season_levels = data.pop(0)
        event_levels = data.pop(0)
        event_loot_item_bonus = data.pop(0)
        teachers_url = data.pop(0)
        sites = data.pop(0)
        # TODO: Complete list of values. (data list is not empty at this point, yet)

        NTAPI._NTBootstrap = NTBootstrap(
            cars=[Car(c["id"], c["name"]) for c in cars[1]]
        )
        return NTAPI._NTBootstrap

    @staticmethod
    def get_account(username: str) -> Account:
        resp: Response = get(NTAPI.RacerUrl.format(username=username), headers=NTAPI.DefaultHeaders)
        racer_info_regex = re_compile(
            r"^\s+RACER_INFO: (.+),\s+}\n\s+if \(typeof NTBOOTSTRAP === 'function'\) {",
            flags=M | S
        )
        try:
            matched_group: str = racer_info_regex.search(resp.text).group(1)
        except AttributeError as ex:
            raise AccountNotFoundError(ex)

        data: dict = loads(matched_group)

        boot: NTBootstrap = NTAPI.get_bootstrap()
        car_boot: dict[int, Car] = {c.id: c for c in boot.cars}

        cars: list[Car] = [car_boot[c[0]] for c in data["cars"]]

        return Account(
            UserIdentity(
                data["userID"],
                data["username"],
                data["displayName"]
            ),
            car_boot[data["carID"]],
            cars,
            data["teamID"]
        )

    @staticmethod
    def get_team(tag: str) -> Team:
        resp: Response = get(NTAPI.TeamsUrl.format(team_name=tag.upper()), headers=NTAPI.DefaultHeaders)
        data: dict = resp.json()["results"]

        team_info: dict = data["info"]
        captain: UserIdentity = UserIdentity(
            team_info["userID"],
            team_info["username"],
            team_info["displayName"]
        )

        members: list[TeamMember] = []
        for member in data["members"]:
            identity: UserIdentity = UserIdentity(
                    member["userID"],
                    member["username"],
                    member["displayName"]
                )
            members.append(
                TeamMember(
                    identity,
                    AccountStatus(member["status"]),
                    TeamMemberRole(member["role"]) if identity.id != captain.id else TeamMemberRole.Captain,
                    datetime.fromtimestamp(member["lastActivity"]),
                    member["played"],
                    datetime.fromtimestamp(member["joinStamp"])
                )
            )

        team: Team = Team(
            team_info["teamID"],
            team_info["name"],
            team_info["tag"],
            captain,
            members
        )

        return team


if __name__ == '__main__':
    # fresh account name for testing: 728828948349389 (only 1 car, no team, etc.)
    test = NTAPI.get_account("usckdck")
    pass
