from __future__ import annotations

import asyncio
import itertools
import math

from collections.abc import Sequence
from io import BytesIO
from typing import Any, ClassVar, Optional

from PIL import Image as PilImage, ImageDraw, ImageFilter, ImageFont
from PIL.Image import Resampling
from pink_accents import Accent

from src.context import Context
from src.decorators import in_executor
from src.errors import PINKError
from src.settings import BaseSettings, settings

from .types import Image, StaticImage

__all__ = (
    "ocr",
    "ocr_translate",
    "textboxes",
)


class CogSettings(BaseSettings):
    ocr_api_token: str

    class Config(BaseSettings.Config):
        section = "cog.images"


cog_settings = settings.subsettings(CogSettings)

_VertexType = dict[str, int]
_VerticesType = tuple[_VertexType, _VertexType, _VertexType, _VertexType]

OCR_API_URL = "https://content-vision.googleapis.com/v1/images:annotate"
OCR_RATELIMIT = 30

FONT = ImageFont.truetype("DejaVuSans.ttf")

_ocr_queue: asyncio.Queue[tuple[asyncio.Future[dict[str, Any]], bytes, Context]] = asyncio.Queue(5)
_task: Optional[asyncio.Task[Any]] = None


class GoogleOCRError(PINKError):
    KNOWN_HINTS: ClassVar[dict[int | None, str]] = {
        None: "The world is on fire, something really bad happened. I have no idea.",
        14: "This means Google cannot access image URL. Try using a different one.",
    }

    def __init__(self, code: Optional[int], message: str):
        self.code = code
        self.message = message

        super().__init__(str(self))

    @classmethod
    def from_response(cls, response: dict[str, Any]) -> GoogleOCRError:
        error = response.get("error", {})

        code = error.get("code")
        message = error.get("message", "unknown")

        return cls(code, message)

    def __str__(self) -> str:
        base = f"**{type(self).__name__}**[{self.code}]: {self.message}"

        if (hint := self.KNOWN_HINTS.get(self.code)) is not None:
            base += f"\n\nHint: {hint}"

        return base


class TROCRError(Exception):
    pass


class AngleUndetectableError(TROCRError):
    pass


class TextField:
    def __init__(self, full_text: str, src: PilImage.Image, padding: int = 3):
        self.text = full_text

        self.left: Optional[int] = None
        self.upper: Optional[int] = None
        self.right: Optional[int] = None
        self.lower: Optional[int] = None

        self.angle = 0

        self._src_width, self._src_height = src.size

        self._padding = padding

    def add_word(self, vertices: _VerticesType, src_size: tuple[int, int]) -> None:
        if not self.initialized:
            # Get angle from first word
            self.angle = self._get_angle(vertices)

        left, upper, right, lower = self._vertices_to_coords(vertices, src_size, self.angle)

        self.left = left if self.left is None else min((self.left, left))
        self.upper = upper if self.upper is None else min((self.upper, upper))
        self.right = right if self.right is None else max((self.right, right))
        self.lower = lower if self.lower is None else max((self.lower, lower))

    @staticmethod
    def _vertices_to_coords(vertices: _VerticesType, src_size: tuple[int, int], angle: int) -> tuple[int, int, int, int]:
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
        def get_coords(vertex: _VertexType) -> tuple[Optional[int], Optional[int]]:
            return vertex.get("x"), vertex.get("y")

        cycle = itertools.cycle(vertices)
        x, y = get_coords(next(cycle))
        for i in range(4):
            next_x, next_y = get_coords(next(cycle))

            # Any vertex coordinate can be missing
            if None in (x, y, next_x, next_y):
                x, y = next_x, next_y
                continue

            # algo: https://stackoverflow.com/a/27481611

            # mypy literally does not see previous statement
            delta_y = y - next_y  # type: ignore
            delta_x = next_x - x  # type: ignore

            degrees = math.degrees(math.atan2(delta_y, delta_x))

            if degrees < 0:
                degrees += 360

            # compensate missing vertices
            degrees += 90 * i

            break
        else:
            raise AngleUndetectableError

        # # truncate last digit, OCR often returns 1-2 degree tilted text, ignore this
        # TEMPORARY: truncate angle to 90 degrees
        return 90 * round(degrees / 90)

    @property
    def coords(self) -> tuple[int, int, int, int]:
        return (self.left, self.upper, self.right, self.lower)  # type: ignore

    @property
    def coords_padded(self) -> tuple[int, int, int, int]:
        return (
            max((0, self.left - self._padding)),  # type: ignore
            max((0, self.upper - self._padding)),  # type: ignore
            min((self._src_width, self.right + self._padding)),  # type: ignore
            min((self._src_height, self.lower + self._padding)),  # type: ignore
        )

    # TODO: implement w/h detection ASAP, this is temporary
    # solutions:
    # 1) https://stackoverflow.com/a/9972699
    # text surrounding box dimensions are known, but i had no success implementing this
    # 2) try to keep track of full coords and just calculate distance
    # a lot of coordinates might be missing, 1st solution is more reliable if it worked
    @property
    def width(self) -> int:
        if self.angle in (0, 180, 360):
            return self.right - self.left  # type: ignore

        if self.angle in (90, 270):
            return self.lower - self.upper  # type: ignore

        assert False  # noqa

    @property
    def height(self) -> int:
        if self.angle in (0, 180, 360):
            return self.lower - self.upper  # type: ignore

        if self.angle in (90, 270):
            return self.right - self.left  # type: ignore

        assert False  # noqa

    @property
    def font_size(self) -> int:
        return max((1, int(1.3333333 * self.height) - 2))

    @property
    def stroke_width(self) -> int:
        return max((1, round(self.font_size / 12)))

    @property
    def initialized(self) -> bool:
        return None not in self.coords

    def __repr__(self) -> str:
        return f"<TextField text='{self.text}' coords={self.coords} angle={self.angle}>"


# language iterator is broken. it returns languages for words instead of lines
#
# def _language_iterator(blocks: Sequence[Any]) -> Iterator[Optional[str]]:
#     """Extracts language for each paragraph in Google OCR output"""

#     def extract_language(data: Any) -> Optional[str]:
#         if (properties := data.get("property")) is None:
#             return None

#         if (languages := properties.get("detectedLanguages")) is None:
#             return None

#         return sorted(languages, key=lambda l: l.get("confidence", 1))[-1]["languageCode"]

#     for block in blocks:
#         block_language = extract_language(block)

#         for paragraph in block["paragraphs"]:
#             paragraph_language = extract_language(paragraph)

#             yield paragraph_language or block_language

#             # line grouping differs between simple annotations and paragraph grouping in
#             # full annotations. "EOL_SURE_SPACE" indicates line break matching simple
#             # annotations
#             for word in paragraph["words"]:
#                 last_symbol = word["symbols"][-1]
#                 if (symbol_properties := last_symbol.get("property")) is None:
#                     continue

#                 if (detected_break := symbol_properties.get("detectedBreak")) is None:
#                     continue

#                 if detected_break["type"] != "EOL_SURE_SPACE":
#                     continue

#                 yield paragraph_language or block_language or extract_language(word)


async def _fetch_ocr(ctx: Context, image_b64: bytes) -> dict[str, Any]:
    async with ctx.session.post(
        OCR_API_URL,
        params={
            "key": cog_settings.ocr_api_token,
        },
        json={
            "requests": [
                {
                    "features": [{"type": "TEXT_DETECTION"}],
                    "image": {"content": image_b64.decode()},
                }
            ]
        },
        headers={
            "x-origin": "https://explorer.apis.google.com",
            "x-referer": "https://explorer.apis.google.com",
        },
    ) as r:
        if r.status != 200:
            if r.content_type.lower() != "application/json":
                reason = await r.text()
                if reason.count("\n") > 1:
                    # we got some garbage HTML response
                    reason = "unknown error"

                raise PINKError(f"Something really bad happened with underlying API[{r.status}]: {reason}")

            json = await r.json()

            raise PINKError(f"Error in underlying API[{r.status}]: " f'{json.get("message", "unknown error")}')
        json = await r.json()

    if not (responses := json["responses"]):
        return {}

    maybe_annotations = responses[0]

    if "textAnnotations" not in maybe_annotations:
        if "error" in maybe_annotations:
            raise GoogleOCRError.from_response(maybe_annotations)
        else:
            raise PINKError("no text detected", formatted=False)

    return maybe_annotations


async def _ocr_fetch_task() -> None:
    while True:
        fut, image_b64, ctx = await _ocr_queue.get()

        try:
            ocr_result = await _fetch_ocr(ctx, image_b64)
        except Exception as e:
            fut.set_exception(e)
        else:
            fut.set_result(ocr_result)

        await asyncio.sleep(OCR_RATELIMIT)


async def ocr(ctx: Context, image: Image) -> dict[str, Any]:
    global _task

    if _task is None:
        _task = asyncio.create_task(_ocr_fetch_task())

    fut = asyncio.get_running_loop().create_future()
    image_b64 = await image.to_base64(ctx)

    try:
        _ocr_queue.put_nowait((fut, image_b64, ctx))
    except asyncio.QueueFull:
        raise PINKError(f"OCR queue full ({_ocr_queue.maxsize}), try again later") from None

    if (qsize := _ocr_queue.qsize()) > 1:
        qsize -= 1

        await ctx.reply(
            f"please wait **~ {round((qsize - 1) * OCR_RATELIMIT + OCR_RATELIMIT / 2)}s**",
            delete_after=5,
        )

    return await fut


@in_executor()
def _draw_trocr(src: PilImage.Image, fields: Sequence[TextField]) -> BytesIO:
    field_cap = 150

    fields = fields[:field_cap]

    src = src.convert("RGBA")

    for field in fields:
        cropped = src.crop(field.coords_padded)

        # NOTE: next line causes segfaults if coords are wrong, debug from here
        blurred = cropped.filter(ImageFilter.GaussianBlur(10))

        # Does not work anymore for some reason, black stroke is good anyway
        # field.inverted_avg_color = ImageOps.invert(
        #     blurred.resize((1, 1)).convert("L")
        # ).getpixel((0, 0))  # ugly!!!

        src.paste(blurred, field.coords_padded)

    for field in fields:
        # TODO: figure out how to fit text into boxes with Pillow without creating
        # extra images
        font = FONT.font_variant(size=field.font_size)

        left, top, right, bottom = font.getbbox(field.text, stroke_width=field.stroke_width)
        text_im = PilImage.new("RGBA", size=(int(right - left), int(bottom - top)))

        ImageDraw.Draw(text_im).text(
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
                ),
            ).rotate(field.angle, expand=True, resample=Resampling.BICUBIC),
            field.coords_padded[:2],
        )

    result = BytesIO()
    src.save(result, format="PNG")
    result.seek(0)

    return result


def _apply_accents(ctx: Context, lines: list[str], accent: Accent) -> list[str]:
    if (accent_cog := ctx.bot.get_cog("Accents")) is None:
        raise RuntimeError("No accents cog loaded")

    return [
        # trocr fully depends on newlines, apply accents to each line separately and
        # replace any newlines with spaces to make sure text order is preserved
        accent_cog.apply_accents_to_text(line, [accent]).replace("\n", " ")  # type: ignore[attr-defined]
        for line in lines
    ]


async def _apply_translation(
    ctx: Context,
    lines: list[str],
    language: str,
    _block_annotations: Any,
) -> list[str]:
    if (translator_cog := ctx.bot.get_cog("Translator")) is None:
        raise RuntimeError("No translator cog loaded")

    # # TODO: group by input languages to improve translation?
    # need_trasnslation = {}
    # paragraph_languages = _language_iterator(block_annotations)

    # for i, line in enumerate(lines):
    #     if next(paragraph_languages) is not None:
    #         need_trasnslation[i] = line

    # if not need_trasnslation:
    #     raise PINKError(
    #         "nothing to translate on image (either entire text is in target language or language is undetected)",
    #         formatted=False,
    #     )

    # until language iterator is fixed we translate everything
    need_trasnslation = dict(enumerate(lines))

    translated = await translator_cog.translate(  # type: ignore[attr-defined]
        "\n".join(need_trasnslation.values()), language
    )

    translated_lines = translated.split("\n")
    if len(translated_lines) != len(need_trasnslation):
        raise RuntimeError(f"expected {len(need_trasnslation)} translated lines, got {len(translated_lines)}")

    new_lines = lines.copy()
    for idx, translated_line in zip(need_trasnslation.keys(), translated_lines, strict=True):
        new_lines[idx] = translated_line

    return new_lines


async def ocr_translate(ctx: Context, image: StaticImage, language: str | Accent) -> tuple[BytesIO, str]:
    src = await image.to_pil(ctx)

    annotations = await ocr(ctx, image)

    word_annotations = annotations["textAnnotations"][1:]
    block_annotations = annotations["fullTextAnnotation"]["pages"][0]["blocks"]

    # Google OCR API returns entry for each word separately, but they can be joined
    # by checking full image description. In description words are combined into
    # lines, lines are separated by newlines, there is a trailing newline (usually).
    # Coordinates from words in the same line can be merged
    lines = annotations["fullTextAnnotation"]["text"].rstrip("\n").split("\n")

    if isinstance(language, Accent):
        new_lines = _apply_accents(ctx, lines, language)
    else:
        new_lines = await _apply_translation(ctx, lines, language, block_annotations)

    # error reporting
    notes = ""

    current_word = 0
    fields = []

    for original_line, line in zip(lines, new_lines, strict=True):
        field = TextField(line, src)

        remaining_line = original_line

        # TODO: sane iterator instead of this
        for word in word_annotations[current_word:]:
            text = word["description"]
            if remaining_line.startswith(text):
                current_word += 1
                remaining_line = remaining_line[len(text) :].lstrip()
                # TODO: merge multiple lines into box
                try:
                    field.add_word(word["boundingPoly"]["vertices"], src.size)
                except AngleUndetectableError:
                    notes += f"angle for `{word}` is undetectable\n"
            else:
                break

        if field.initialized and line.casefold() != original_line.casefold():
            fields.append(field)

    if not fields:
        raise PINKError("could not translate anything on image", formatted=False)

    result = await _draw_trocr(src, fields)

    stats = f"Words: {current_word}\nLines: {len(fields)}"
    if notes:
        stats += f"\nNotes: {notes}"

    return result, stats


async def textboxes(ctx: Context, image: StaticImage, outline: tuple[int, int, int]) -> tuple[BytesIO, str]:
    src = await image.to_pil(ctx)

    annotations = await ocr(ctx, image)

    word_annotations = annotations["textAnnotations"][1:]

    # Google OCR API returns entry for each word separately, but they can be joined
    # by checking full image description. In description words are combined into
    # lines, lines are separated by newlines, there is a trailing newline (usually).
    # Coordinates from words in the same line can be merged
    lines = annotations["fullTextAnnotation"]["text"].rstrip("\n").split("\n")

    # error reporting
    notes = ""

    current_word = 0
    fields = []

    for original_line, line in zip(lines, lines, strict=True):
        field = TextField(line, src)

        remaining_line = original_line

        # TODO: sane iterator instead of this
        for word in word_annotations[current_word:]:
            text = word["description"]
            if remaining_line.startswith(text):
                current_word += 1
                remaining_line = remaining_line[len(text) :].lstrip()
                # TODO: merge multiple lines into box
                try:
                    field.add_word(word["boundingPoly"]["vertices"], src.size)
                except AngleUndetectableError:
                    notes += f"angle for `{word}` is undetectable\n"
            else:
                break

        if field.initialized:
            fields.append(field)

    if not fields:
        raise PINKError("No drawable textboxes", formatted=False)

    result = await _draw_textboxes(src, fields, outline)

    stats = f"Words: {current_word}\nLines: {len(fields)}"
    if notes:
        stats += f"\nNotes: {notes}"

    return result, stats


@in_executor()
def _draw_textboxes(src: PilImage.Image, fields: Sequence[TextField], outline: tuple[int, int, int]) -> BytesIO:
    field_cap = 150

    fields = fields[:field_cap]

    src = src.convert("RGBA")
    draw = ImageDraw.Draw(src)

    for field in fields:
        draw.rectangle(field.coords_padded, outline=outline, width=field.stroke_width)

    result = BytesIO()
    src.save(result, format="PNG")
    result.seek(0)

    return result
