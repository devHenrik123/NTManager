from typing import Callable, Any, override, Coroutine

from discord import ComponentType, SelectOption, ChannelType, Interaction
from discord.ui import Select


class SelectWithCallback(Select):
    def __init__(
            self,
            select_type: ComponentType = ComponentType.string_select,
            custom_id: str | None = None,
            placeholder: str | None = None,
            min_values: int = 1,
            max_values: int = 1,
            options: list[SelectOption] = None,
            channel_types: list[ChannelType] = None,
            disabled: bool = False,
            row: int | None = None,
            on_select: Callable[[Interaction, list[Any]], Coroutine[Interaction, list[Any], None]] = None
    ) -> None:
        super().__init__(
            select_type=select_type,
            custom_id=custom_id,
            placeholder=placeholder,
            min_values=min_values,
            max_values=max_values,
            options=options,
            channel_types=channel_types,
            disabled=disabled,
            row=row
        )
        self._on_select: Callable[[Interaction, list[Any]], Coroutine[Interaction, list[Any], None]] =\
            on_select if on_select is not None else SelectWithCallback.__placeholder_routine

    @staticmethod
    async def __placeholder_routine(interaction: Interaction, __: list[Any]) -> None:
        await interaction.respond()

    @override
    async def callback(self, interaction: Interaction) -> None:
        await self._on_select(interaction, self.values)
