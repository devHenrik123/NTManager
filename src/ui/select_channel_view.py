from typing import Callable, Coroutine

from discord import ChannelType, Interaction, ComponentType
from discord.abc import GuildChannel
from discord.ui import View

from ui.select_with_callback import SelectWithCallback


class SelectChannelView(View):

    def __init__(
            self,
            callback: Callable[[Interaction, GuildChannel], Coroutine[Interaction, GuildChannel, None]],
            channel_types: list[ChannelType] = None
    ) -> None:
        super().__init__()

        if channel_types is None:
            channel_types = [ChannelType.text]

        self._callback: Callable[[Interaction, GuildChannel], Coroutine[Interaction, GuildChannel, None]] = callback
        self._select: SelectWithCallback = SelectWithCallback(
            select_type=ComponentType.channel_select,
            channel_types=channel_types,
            on_select=self._on_select
        )
        self.add_item(self._select)

    async def _on_select(self, interaction: Interaction, values: list[GuildChannel]) -> None:
        self._select.disabled = True
        await interaction.response.edit_message(view=self)
        await self._callback(interaction, values[0])
