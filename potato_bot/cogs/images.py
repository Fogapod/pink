import os
import math
import itertools

from io import BytesIO
from typing import Any, Dict, Tuple, Optional, Sequence

import PIL
import discord

from PIL import ImageDraw, ImageFont, ImageFilter
from discord.ext import commands

from potato_bot.bot import Bot
from potato_bot.cog import Cog
from potato_bot.types import Image, StaticImage, AnimatedImage
from potato_bot.context import Context

_VertexType = Dict[str, int]
_VerticesType = Tuple[_VertexType, _VertexType, _VertexType, _VertexType]

OCR_API_URL = "https://api.tsu.sh/google/ocr"

FONT_PATH = "DejaVuSans.ttf"

PX_TO_PT_RATIO = 1.3333333

TRANSLATE_CAP = 10
BLUR_CAP = 40


class TROCRException(Exception):
    pass


class AngleUndetectable(TROCRException):
    pass


class TextField:
    def __init__(self, full_text: str, src: PIL.Image, padding: int = 3):
        self.text = full_text

        self.left: Optional[int] = None
        self.upper: Optional[int] = None
        self.right: Optional[int] = None
        self.lower: Optional[int] = None

        self.angle = 0

        self._src_width, self._src_height = src.size

        self._padding = padding

    def add_word(self, vertices: _VerticesType, src_size: Tuple[int, int]) -> None:
        if not self.initialized:
            # Get angle from first word
            self.angle = self._get_angle(vertices)

        left, upper, right, lower = self._vertices_to_coords(
            vertices, src_size, self.angle
        )

        self.left = left if self.left is None else min((self.left, left))
        self.upper = upper if self.upper is None else min((self.upper, upper))
        self.right = right if self.right is None else max((self.right, right))
        self.lower = lower if self.lower is None else max((self.lower, lower))

    @staticmethod
    def _vertices_to_coords(
        vertices: _VerticesType, src_size: Tuple[int, int], angle: int
    ) -> Tuple[int, int, int, int]:
        """Returns Pillow style coordinates (left, upper, right, lower)."""

        # A - 0
        # B - 1
        # C - 2
        # D - 3
        #
        # A----B
        # |    |  angle = 360/0
        # D----C
        #
        #    A
        #  /   \
        # D     B  angle = 315
        #  \   /
        #    C
        #
        # D----A
        # |    |  angle = 270
        # C----B
        #
        #    D
        #  /   \
        # C     A  angle = 225
        #  \   /
        #    B
        #
        # C---D
        # |   | angle = 180
        # B---A
        #
        #    C
        #  /   \
        # B     D angle = 135
        #  \   /
        #    A
        #
        # B---C
        # |   | angle = 90
        # A---D
        #
        #    B
        #  /   \
        # A     C  angle = 45
        #  \   /
        #    D
        if 0 <= angle <= 90:
            left = vertices[0].get("x")
            upper = vertices[1].get("y")
            right = vertices[2].get("x")
            lower = vertices[3].get("y")
        elif 90 < angle <= 180:
            left = vertices[1].get("x")
            upper = vertices[2].get("y")
            right = vertices[3].get("x")
            lower = vertices[0].get("y")
        elif 180 < angle <= 270:
            left = vertices[2].get("x")
            upper = vertices[3].get("y")
            right = vertices[0].get("x")
            lower = vertices[1].get("y")
        elif 270 < angle <= 360:
            left = vertices[3].get("x")
            upper = vertices[0].get("y")
            right = vertices[1].get("x")
            lower = vertices[2].get("y")

        if left is None:
            left = 0
        if upper is None:
            upper = 0
        if right is None:
            right = src_size[0]
        if lower is None:
            lower = src_size[1]

        return (left, upper, right, lower)

    @staticmethod
    def _get_angle(vertices: _VerticesType) -> int:
        # https://stackoverflow.com/a/27481611
        def get_coords(vertex: _VertexType) -> Tuple[Optional[int], Optional[int]]:
            return vertex.get("x"), vertex.get("y")

        cycle = itertools.cycle(vertices)
        for i in range(4):
            x, y = get_coords(next(cycle))
            next_x, next_y = get_coords(next(cycle))

            # Any vertex coordinate can be missing
            if None not in (x, y, next_x, next_y):
                x_diff, y_diff = next_x - x, y - next_y  # type: ignore
                degrees = math.degrees(math.atan2(y_diff, x_diff))

                # compensate missing vertices
                degrees += 90 * i

                break
        else:
            raise AngleUndetectable

        if degrees < 0:
            degrees += 360
        elif degrees > 360:
            degrees -= 360

        return round(degrees)

    @property
    def coords(self) -> Tuple[int, int, int, int]:
        return (self.left, self.upper, self.right, self.lower)  # type: ignore

    @property
    def coords_padded(self) -> Tuple[int, int, int, int]:
        return (
            max((0, self.left - self._padding)),  # type: ignore
            max((0, self.upper - self._padding)),  # type: ignore
            min((self._src_width, self.right + self._padding)),  # type: ignore
            min((self._src_height, self.lower + self._padding)),  # type: ignore
        )

    @property
    def width(self) -> int:
        return self.right - self.left  # type: ignore

    @property
    def height(self) -> int:
        return self.lower - self.upper  # type: ignore

    @property
    def font_size(self) -> int:
        return max((1, int(PX_TO_PT_RATIO * self.height) - 2))

    @property
    def stroke_width(self) -> int:
        return max((1, round(self.font_size / 12)))

    @property
    def initialized(self) -> bool:
        return None not in self.coords

    def __repr__(self) -> str:
        return f"<TextField text='{self.text}' coords={self.coords} angle={self.angle}>"


class Images(Cog):
    """Image manipulation"""

    async def setup(self) -> None:
        self.font = ImageFont.truetype(FONT_PATH)

        # TODO: fetch list of languages from API or hardcode

    @commands.command(hidden=True)
    async def i(self, ctx: Context, i: Image = None) -> None:
        if i is None:
            i = await Image.from_history(ctx)

        await ctx.send(i)

    @commands.command(hidden=True)
    async def si(self, ctx: Context, i: StaticImage = None) -> None:
        if i is None:
            i = await StaticImage.from_history(ctx)

        await ctx.send(i)

    @commands.command(hidden=True)
    async def ai(self, ctx: Context, i: AnimatedImage = None) -> None:
        if i is None:
            i = await AnimatedImage.from_history(ctx)

        await ctx.send(i)

    async def _ocr(
        self, ctx: Context, image_url: str, *, raw: bool = False
    ) -> Dict[str, Any]:
        params = {"q": image_url}
        if raw:
            params["raw"] = "1"

        async with ctx.session.get(
            OCR_API_URL,
            params=params,
            headers={
                "authorization": os.environ["OCR_API_TOKEN"],
            },
        ) as r:
            if r.status != 200:
                if r.content_type.lower() != "application/json":
                    reason = await r.text()
                    if reason.count("\n") > 1:
                        # we got some garbage HTML response
                        reason = "unknown error"

                    await ctx.reply(
                        f"Something really bad happened with underlying API[{r.status}]: {reason}",
                        exit=True,
                    )

                try:
                    json = await r.json()
                except json.JSONDecodeError:
                    await ctx.reply(
                        f"Unable to process response from API[{r.status}]",
                        exit=True,
                    )

                await ctx.reply(
                    f"Error in underlying API[{r.status}]: "
                    f'{json.get("message", "unknown error")}',
                    exit=True,
                )
            json = await r.json()

        return json

    @commands.command()
    async def ocr(self, ctx: Context, image: Image = None) -> None:
        """Read text on image"""

        if image is None:
            image = await Image.from_history(ctx)

        json = await self._ocr(ctx, image.url)

        if not (text := json["text"]):
            return await ctx.reply("No text detected")

        await ctx.send(f"```\n{text}```")

    @commands.command()
    async def trocr(
        self, ctx: Context, language: str = "en", image: StaticImage = None
    ) -> None:
        """!!! UNFINISHED !!! Translate text on image"""

        if language == "list":
            await ctx.send("TODO: send language list")

        # TODO: check language argument

        if image is None:
            image = await StaticImage.from_history(ctx)

        src = await image.to_pil_image(ctx)

        json = await self._ocr(ctx, image.url, raw=True)

        if not (text_annotations := json["responses"][0].get("textAnnotations")):
            return await ctx.reply("No text detected")

        # error reporting
        notes = ""

        # Google OCR API returns entry for each word separately, but they can be joined
        # by checking full image description. In description words are combined into
        # lines, lines are separated by newlines, there is a trailing newline.
        # Coordinates from words in the same line can be merged
        current_word = 1  # 1st annotation is entire text
        translations_count = 0
        fields = []
        for line in text_annotations[0]["description"].split("\n")[:-1]:
            translated_line = line
            if translations_count < TRANSLATE_CAP:
                in_lang = text_annotations[0]["locale"]
                # seems like "und" is an unknown language
                if in_lang != "und" and in_lang != language:
                    translated_line = await self.translate(line, in_lang, language)
                    translations_count += 1

            field = TextField(translated_line, src)

            for word in text_annotations[current_word:]:
                text = word["description"]
                if line.startswith(text):
                    current_word += 1
                    line = line[len(text) :].lstrip()
                    # TODO: merge multiple lines into box
                    try:
                        field.add_word(word["boundingPoly"]["vertices"], src.size)
                    except AngleUndetectable:
                        notes += f"angle for `{word}` is undetectable\n"
                else:
                    break

            if field.initialized:
                fields.append(field)

        result = await self.bot.loop.run_in_executor(None, self.draw, src, fields)

        stats = f"Words: {current_word - 1}\nLines: {len(fields)}\nTranslated: {translations_count}"
        if notes:
            stats += f"\nNotes: {notes}"

        await ctx.send(stats, file=discord.File(result, filename="trocr.png"))

    def draw(self, src: PIL.Image, fields: Sequence[TextField]) -> BytesIO:
        src = src.convert("RGBA")

        fields = fields[:BLUR_CAP]

        for field in fields:
            cropped = src.crop(field.coords_padded)

            # NOTE: next line causes segfaults if coords are wrong, debug from here
            blurred = cropped.filter(ImageFilter.GaussianBlur(10))

            # Does not work anymore for some reason, black stroke is good anyway
            # field.inverted_avg_color = ImageOps.invert(
            #     blurred.resize((1, 1)).convert("L")
            # ).getpixel((0, 0))  # ugly!!!

            src.paste(blurred, field.coords_padded)

            # might not be needed, but fly command creates memory leak
            cropped.close()
            blurred.close()

        for field in fields:
            # TODO: figure out how to fit text into boxes with Pillow without creating
            # extra images
            font = self.font.font_variant(size=field.font_size)

            text_im = PIL.Image.new(
                "RGBA",
                size=font.getsize(field.text, stroke_width=field.stroke_width),
            )
            draw = ImageDraw.Draw(text_im)

            draw.text(
                (0, 0),
                text=field.text,
                font=font,
                spacing=0,
                stroke_width=field.stroke_width,
                stroke_fill=(0, 0, 0),
            )

            src.alpha_composite(
                text_im.resize(
                    (
                        min((text_im.width, field.width)),
                        min((text_im.height, field.height)),
                    )
                ).rotate(field.angle, expand=True, resample=PIL.Image.BICUBIC),
                field.coords_padded[:2],
            )

            text_im.close()

        result = BytesIO()
        src.save(result, format="PNG")

        src.close()

        return BytesIO(result.getvalue())

    async def translate(self, text: str, in_lang: str, out_lang: str) -> str:
        return text


def setup(bot: Bot) -> None:
    bot.add_cog(Images(bot))