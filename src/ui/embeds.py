
from discord import Embed, Colour


class DefaultEmbed(Embed):

    def __init__(self, title: str, description: str = "", *args, **kwargs) -> None:
        super().__init__(
            title=title,
            description=description,
            color=Colour.blurple(),
            *args,
            **kwargs
        )
