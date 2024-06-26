import re

from discord.ext import commands
from pink_accents import Accent
from pink_accents.errors import BadSeverityError

from src.context import Context

from .constants import ALL_ACCENTS


# inherit to make linters sleep well
class PINKAccent(Accent, register=False):
    MAX_SEVERITY = 10

    @classmethod
    async def convert(cls, _: Context, argument: str) -> Accent:
        match = re.fullmatch(r"(.+?)(:?\[(.+?)\])?", argument)
        assert match

        name = match[1].lower()
        try:
            severity = 1 if match[3] is None else int(match[3])
        except ValueError:
            raise commands.BadArgument(f"{name}: severity must be integer") from None

        if severity > cls.MAX_SEVERITY:
            raise commands.BadArgument(f"{name}: severity must be lower or equal to {cls.MAX_SEVERITY}")

        try:
            accent = ALL_ACCENTS[name.lower()]
        except KeyError:
            raise commands.BadArgument(f"not a valid accent: {name}") from None

        try:
            return accent(severity)
        except BadSeverityError as e:
            raise commands.BadArgument(f"{name}: bad severity: {e}") from None
