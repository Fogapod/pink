# ruff: noqa: RUF001
import random
import re

from typing import Optional

from _shared import DISCORD_MESSAGE_END, DISCORD_MESSAGE_START  # type: ignore[import-not-found]
from pink_accents import Accent, Match, Replacement
from pink_accents.types import PatternMapType

NYAS = (
    ":3",
    ">w<",
    "^w^",
    "owo",
    "OwO",
    "nya",
    "Nya",
    "nyaa",
    "nyan",
    "!!!",
    "(=^‥^=)",
    "(=；ｪ；=)",
    "ヾ(=｀ω´=)ノ”",
    "~~",
    "*wings their tail*",
    "\N{PAW PRINTS}",
    # most of these are taken from: https://github.com/tgstation/tgstation/blob/67ec6e8daa0fc58eeda91d96468960f4ad29b5db/code/modules/language/nekomimetic.dm#L7-L11
    "neko",
    "mimi",
    "moe",
    "mofu",
    "fuwa",
    "kyaa",
    "kawaii",
    "poka",
    "munya",
    "puni",
    "munyu",
    "ufufu",
    "uhuhu",
    "icha",
    "doki",
    "kyun",
    "kusu",
    "desu",
    "kis",
    "ama",
    "chuu",
    "baka",
    "hewo",
    "boop",
    "gato",
    "kit",
    "sune",
    "yori",
    "sou",
    "baka",
    "chan",
    "san",
    "kun",
    "mahou",
    "yatta",
    "suki",
    "usagi",
    "domo",
    "ori",
    "uwa",
    "zaazaa",
    "shiku",
    "puru",
    "ira",
    "heto",
    "etto",
)

FORBIDDEN_NYAS = (
    ";)",
    ";3",
    "uwu",
    "UwU",
)

ALL_NYAS = (
    *NYAS,
    *FORBIDDEN_NYAS,
)

FORBIDDEN_NYA_TRESHOLD = 5


def nya(m: Match) -> str:
    weights = [1] * len(NYAS)

    if m.severity > FORBIDDEN_NYA_TRESHOLD:
        weights += [m.severity - FORBIDDEN_NYA_TRESHOLD] * len(FORBIDDEN_NYAS)
    else:
        weights += [0] * len(FORBIDDEN_NYAS)

    max_nyas_x100 = int((0.5 + m.severity * 0.25) * 100)

    count = round(random.randint(0, max_nyas_x100) / 100)

    return " ".join(random.choices(ALL_NYAS, weights, k=count))


# since nya is not guaranteed to produce value, using something like
# lambda m: f"{nya(m)} "
# may leave empty whitespace which isn't stripped
def nya_message_start(m: Match) -> Optional[str]:
    if value := nya(m):
        return f"{value} "

    return None


def nya_message_end(m: Match) -> Optional[str]:
    if value := nya(m):
        return f" {value}"

    return None


# TODO: add 2-8 severities
#
# this is free real estate:
# https://github.com/goonstation/goonstation/blob/master/code/modules/medical/genetics/bioEffects/speech.dm
# also has ideas for other accents

PATTERNS_1: PatternMapType = {
    r"[rlv]": "w",
    r"ove": "uv",
    r"(?<!ow)o(?!wo)": {
        "owo": 0.2,
    },
    # do not break discord mentions by avoiding @
    r"(?<!@)!": lambda _: f" {random.choice(NYAS)}!",
    r"ni": "nyee",
    r"na": "nya",
    r"ne": "nye",
    r"no": "nyo",
    r"nu": "nyu",
}

# 2 - 8
PATTERNS_2: PatternMapType = {
    **PATTERNS_1,
    DISCORD_MESSAGE_START: nya_message_start,
    DISCORD_MESSAGE_END: nya_message_end,
}

PATTERNS_9: PatternMapType = {
    **PATTERNS_2,
    r"\s+": lambda _: f" {random.choice(ALL_NYAS)} ",
}

PATTERNS_10: PatternMapType = {
    **PATTERNS_2,
    # https://stackoverflow.com/a/6314634
    r"[^\W\d_]+": lambda _: random.choice(ALL_NYAS),
    DISCORD_MESSAGE_END: lambda _: "!" * random.randrange(5, 10),
}


class OwO(Accent):
    """What's this"""

    def register_patterns(self) -> None:
        patterns: PatternMapType
        flags = re.IGNORECASE

        if self.severity == 1:
            patterns = PATTERNS_1
        elif self.severity == 9:
            patterns = PATTERNS_9
        elif self.severity > 9:
            patterns = PATTERNS_10
            flags = re.UNICODE
        else:
            patterns = PATTERNS_2

        for k, v in patterns.items():
            self.register_replacement(Replacement(k, v, flags=flags))
