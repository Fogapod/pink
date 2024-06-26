from typing import Optional

import discord

from discord.ext import commands

from src.bot import PINK
from src.cog import Cog
from src.context import Context
from src.utils import run_process

from .constants import GIFSICLE_ARGUMENTS
from .flies import draw_flies
from .types import AnimatedImage, Image, StaticImage

try:
    from src.cogs.translator.types import Language
except ImportError:
    raise Exception("This cog relies on the existance of translator cog") from None

try:
    from src.cogs.accents.types import PINKAccent
except ImportError:
    raise Exception("This cog relies on the existance of accents cog") from None

from pink_accents import Accent

from .ocr import ocr, ocr_translate, textboxes

_StrOrAccent = str | Accent


class LanguageOrAccent(commands.Converter[_StrOrAccent]):
    async def convert(self, ctx: Context, argument: str) -> _StrOrAccent:  # type: ignore[override]
        try:
            language = await Language.convert(ctx, argument)
        except commands.BadArgument as e:
            try:
                accent = await PINKAccent.convert(ctx, argument)
            except commands.BadArgument:
                raise e

            return accent

        return language


class Images(Cog):
    """
    Image manipulation

    There are multiple ways to provide image arguments.

    If you don't provide text, image is searched in:
      - referenced message attachements/embeds
      - current message atatchments/embeds
      - attachments/embeds in up to 200 messages in history

    If you provide argument, it is checked in the following order:
      - referenced message is checked for attachements/embeds
      - special values (see below)
      - emote/emote id
      - emoji
      - user (id/mention/name/name#discriminator)
      - image URL

    Special values:
      ~ checks history. useful in rare cases when you must provide text
      ^ checks previous message for attachements/embeds. multiple symbols can
        be stacked. each ^ means go 1 message back in history
    """

    @commands.command(hidden=True)
    async def i(
        self,
        ctx: Context,
        i: Image = None,  # type: ignore
    ) -> None:
        if i is None:
            i = await Image.from_history(ctx)

        await ctx.send(i, accents=[])

    @commands.command(hidden=True)
    async def si(
        self,
        ctx: Context,
        i: StaticImage = None,  # type: ignore
    ) -> None:
        if i is None:
            i = await StaticImage.from_history(ctx)

        await ctx.send(i, accents=[])

    @commands.command(hidden=True)
    async def ai(
        self,
        ctx: Context,
        i: AnimatedImage = None,  # type: ignore
    ) -> None:
        if i is None:
            i = await AnimatedImage.from_history(ctx)

        await ctx.send(i, accents=[])

    @commands.command()
    @commands.cooldown(1, 5, type=commands.BucketType.channel)
    async def ocr(
        self,
        ctx: Context,
        image: Image = None,  # type: ignore
    ) -> None:
        """Read text on image"""

        async with ctx.typing():
            if image is None:
                image = await Image.from_history(ctx)

            annotations = await ocr(ctx, image)

        await ctx.send(f"```\n{annotations['fullTextAnnotation']['text']}```")

    @commands.command()
    @commands.cooldown(1, 5, type=commands.BucketType.channel)
    async def trocr(
        self,
        ctx: Context,
        language: _StrOrAccent = commands.parameter(converter=LanguageOrAccent()),  # noqa: B008
        image: Optional[StaticImage] = commands.parameter(converter=StaticImage, default=None),
    ) -> None:
        """
        Translate text on image

        Note: text rotation is truncated to 90 degrees for now
        Note:
            Entire text is translated at once for the sake of optimization,
            this might produce bad results. This might be improved in future
            (for multi-language images)
        """

        async with ctx.typing():
            if image is None:
                image = await StaticImage.from_history(ctx)

            result, stats = await ocr_translate(ctx, image, language)

        await ctx.send(
            stats,
            file=discord.File(result, filename="trocr.png", spoiler=image.is_spoiler),
        )

    @commands.command(aliases=["textbox", "textboxes"])
    @commands.cooldown(1, 5, type=commands.BucketType.channel)
    async def text(
        self,
        ctx: Context,
        image: StaticImage = None,  # type: ignore
    ) -> None:
        """Draws boxes around text on image"""

        async with ctx.typing():
            if image is None:
                image = await StaticImage.from_history(ctx)

            # hardcoded outline color for now
            result, stats = await textboxes(ctx, image, (127, 255, 0))

        await ctx.send(
            stats,
            file=discord.File(result, filename="textboxes.png", spoiler=image.is_spoiler),
        )

    @commands.command(aliases=["flies"])
    @commands.cooldown(1, 12, type=commands.BucketType.channel)
    async def fly(
        self,
        ctx: Context,
        image: StaticImage = None,  # type: ignore
        amount: int = 1,
        fly_image: StaticImage = None,  # type: ignore
    ) -> None:
        """Animates flies on image"""

        if image is None:
            image = await StaticImage.from_history(ctx)

        src = await image.to_pil(ctx)

        if fly_image is not None:
            fly_src = await fly_image.to_pil(ctx)
        else:
            fly_src = None

        min_amount = 1
        max_amount = 50

        if not min_amount <= amount <= max_amount:
            raise commands.BadArgument(f"fly amount should be between **{min_amount}** and **{max_amount}**")

        # TODO: make configurable
        steps = 100
        velocity = 10

        async with ctx.channel.typing():
            filename = await draw_flies(src, fly_src, steps, velocity, amount)

            # optimize gif using gifsicle
            await run_process("gifsicle", *GIFSICLE_ARGUMENTS, str(filename))

        await ctx.send(file=discord.File(filename, filename="fly.gif", spoiler=image.is_spoiler))

        filename.unlink()


async def setup(bot: PINK) -> None:
    await bot.add_cog(Images(bot))
