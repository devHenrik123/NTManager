from abc import ABC
from threading import Lock
from dataclasses import dataclass
from json import load, dump
from pathlib import Path
from typing import Final

from util import RootDir

"""
Example persistence file:

{
    "servers": {
        "82839239": {  <- server_id: Server
            "team": {
                "tag": "ZH"
            },
            "inactivity_alerts": {
                "channel": 728245897,
                "days": 7
            },
            "daily_race_logs": {
                "channel": 728245897,
                "previous_log": {
                    "12345": 100  <- NT user id: race count
                }
            }
        }
    }
}

"""

@dataclass
class RaceLogEntry:
    user_id: str
    race_count: int


@dataclass
class DailyRaceLogs:
    channel: int
    previous_log_entries: list[RaceLogEntry] | None


@dataclass
class Team:
    tag: str


@dataclass
class InactivityAlerts:
    channel: int
    days: int


@dataclass
class Server:
    id: str
    team: Team | None
    inactivity_alerts: InactivityAlerts | None
    daily_race_logs: DailyRaceLogs | None


@dataclass
class PersistentData:
    servers: list[Server]


class Persistence(ABC):
    PersistenceFile: Final[Path] = RootDir / "persistence.json"
    Encoding: Final[str] = "utf-8"
    Indent: Final[int] = 4
    FileLock: Final[Lock] = Lock()

    __Instance: PersistentData | None = None

    @staticmethod
    def get(force_reload: bool = False) -> PersistentData:
        if not Persistence.PersistenceFile.is_file():
            Persistence.write()

        if not force_reload and Persistence.__Instance:
            return Persistence.__Instance

        with Persistence.FileLock:
            with open(Persistence.PersistenceFile, "r", encoding=Persistence.Encoding) as persistence:
                per: dict = load(persistence)
            Persistence.__Instance = PersistentData(
                servers=[
                    Server(
                        server_id,
                        team=Team(
                            server["team"]["tag"]
                        ) if "team" in server and server["team"] else None,
                        inactivity_alerts=InactivityAlerts(
                            server["inactivity_alerts"]["channel"],
                            server["inactivity_alerts"]["days"]
                        ) if "inactivity_alerts" in server and server["inactivity_alerts"] else None,
                        daily_race_logs=DailyRaceLogs(
                            server["daily_race_logs"]["channel"],
                            [
                                RaceLogEntry(
                                    user_id, race_count
                                ) for user_id, race_count in server["daily_race_logs"]["previous_log"].items()
                            ] if "previous_log" in server["daily_race_logs"] and server["daily_race_logs"]["previous_log"] else None
                        ) if "daily_race_logs" in server and server["daily_race_logs"] else None
                    ) for server_id, server in per["servers"].items()
                ]
            )
        return Persistence.__Instance

    @staticmethod
    def get_server(server_id: str) -> Server:
        output: Server | None = None
        for server in Persistence.get().servers:
            if server.id == server_id:
                output = server
                break
        if output is None:
            # Create a new server and add it to in-memory persistence:
            output = Server(
                id=server_id,
                team=None,
                inactivity_alerts=None,
                daily_race_logs=None
            )
            Persistence.__Instance.servers.append(output)
        return output

    @staticmethod
    def write() -> None:
        with Persistence.FileLock:
            with open(Persistence.PersistenceFile, "w", encoding=Persistence.Encoding) as persistence:
                if Persistence.__Instance is None:
                    dump(
                        {
                            "servers": {}
                        },
                        persistence,
                        indent=Persistence.Indent
                    )
                else:
                    dump(
                        {
                            "servers": {
                                server.id: {
                                    "team": {
                                        "tag": server.team.tag
                                    } if server.team else None,
                                    "inactivity_alerts": {
                                        "channel": server.inactivity_alerts.channel,
                                        "days": server.inactivity_alerts.days
                                    } if server.inactivity_alerts else None,
                                    "daily_race_logs": {
                                        "channel": server.daily_race_logs.channel,
                                        "previous_log": dict(
                                            (log_entry.user_id, log_entry.race_count)
                                            for log_entry in server.daily_race_logs.previous_log_entries
                                        ) if server.daily_race_logs.previous_log_entries else None
                                    } if server.daily_race_logs else None
                                } for server in Persistence.__Instance.servers
                            }
                        },
                        persistence,
                        indent=Persistence.Indent
                    )
        Persistence.get(force_reload=True)
