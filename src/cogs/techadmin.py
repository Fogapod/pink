from __future__ import annotations

import ast
import asyncio
import copy
import io
import random
import re
import sqlite3
import textwrap
import traceback

from contextlib import redirect_stdout
from pprint import pformat
from typing import Any, Optional, Union

import discord

from discord.ext import commands

from src.bot import PINK
from src.checks import is_owner
from src.cog import Cog
from src.context import Context
from src.converters import Code
from src.utils import run_process_shell

COG_MODULE_PREFIX = "src.cogs."
PG_UNNAMED_COLUMN = "?column?"


class TechAdmin(Cog):
    """Commands for bot administrators"""

    async def cog_check(self, ctx: Context) -> None:  # type: ignore
        return await is_owner().predicate(ctx)  # type: ignore[attr-defined]

    async def cog_load(self) -> None:
        # take possible provious reload from bot (means this cog was reloaded)
        stupid_var_name = f"_{type(self).__name__}__i_am_sorry_this_is_needed_for_reload_will_delete_later_i_promise"

        if (last_reloaded := getattr(self.bot, stupid_var_name, None)) is not None:
            delattr(self.bot, stupid_var_name)

        self._last_reloaded_extension: Optional[str] = last_reloaded

    async def cog_unload(self) -> None:
        self.bot.__i_am_sorry_this_is_needed_for_reload_will_delete_later_i_promise = self._last_reloaded_extension  # type: ignore

    # TODO: a converter
    # TODO: resolve cogs inside groups properly (folders without __ini__.py)
    @staticmethod
    def _resolve_extension(ctx: Context, name: str) -> str:
        if (command := ctx.bot.get_command(name)) is not None:
            extension = command.cog.__module__
        elif (cog := ctx.bot.get_cog(name)) is not None:
            extension = cog.__module__
        elif name.startswith("on_"):
            if (events := ctx.bot.extra_events.get(name)) is not None:
                if len(events) > 1:
                    raise commands.BadArgument(
                        f"More than one event matched: {', '.join((e.__module__) for e in events)}"
                    )

                return events[0].__module__

            raise commands.BadArgument("Event not found")
        else:
            extension = f"{COG_MODULE_PREFIX}{name.lstrip(COG_MODULE_PREFIX)}"

        # in some cases folder cogs are located in module_name/cog.py
        return extension.rstrip(".cog")

    @commands.command()
    async def load(self, ctx: Context, *, thing: str) -> None:
        """Load extension"""

        extension = self._resolve_extension(ctx, thing)
        await self.bot.load_extension(extension)

        await ctx.send(f"loaded `{extension}`")

    @commands.command()
    async def unload(self, ctx: Context, *, thing: str) -> None:
        """Unload extension"""

        extension = self._resolve_extension(ctx, thing)
        await self.bot.unload_extension(extension)

        await ctx.send(f"unloaded `{extension}`")

    @commands.command(aliases=["re"])
    async def reload(self, ctx: Context, *, thing: Optional[str]) -> None:
        """Reload extension"""

        if thing is None:
            if self._last_reloaded_extension is None:
                return await ctx.send("No previous reloaded module")

            extension = self._last_reloaded_extension
        else:
            extension = self._resolve_extension(ctx, thing)
            self._last_reloaded_extension = extension

        await self.bot.reload_extension(extension)

        # try deleting message for easier testing with frequent reloads
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            # cleanup where we can. otherwise leave bot message as well
            delete_after = None
        else:
            delete_after = 10

        await ctx.send(f"reloaded `{extension}`", delete_after=delete_after)

    # https://github.com/Rapptz/RoboDanny/blob/715a5cf8545b94d61823f62db484be4fac1c95b1/cogs/admin.py#L422
    @commands.command(aliases=["doas", "da"])
    async def runas(self, ctx: Context, user: Union[discord.Member, discord.User], *, command: str) -> None:
        """Run command as other user"""

        msg = copy.copy(ctx.message)
        msg.channel = ctx.channel
        msg.author = user
        msg.content = f"{ctx.prefix}{command}"
        new_ctx = await self.bot.get_context(msg, cls=type(ctx))

        await self.bot.invoke(new_ctx)
        await ctx.ok()

    @commands.command(aliases=["eva!", "eval!"])
    async def eval(self, ctx: Context, *, code: Code) -> None:
        """
        Evaluate code inside bot, with async support
        Has conveniece shortcuts like
        - ctx
        - discord
        """

        async with ctx.typing():
            result = await self._eval(ctx, code, insert_return=not ctx.invoked_with.endswith("!"))  # type: ignore
            result = result.replace(self.bot.http.token, "TOKEN_LEAKED")  # type: ignore

        await ctx.send(f"```py\n{result}```")

    @commands.command()
    async def exec(self, ctx: Context, *, code: Code) -> None:
        """Execute shell command"""

        async with ctx.typing():
            result = await self._exec(ctx, code.body)

        result.replace(self.bot.http.token, "TOKEN_LEAKED")  # type: ignore

        await ctx.send(f"```bash\n{result}```")

    @commands.command(aliases=["select"])
    async def sql(self, ctx: Context, *, code: Code) -> None:
        """Run SQL code against bot database"""

        # same parameters as eval
        query = code.body.format(ctx=ctx, message=ctx.message, guild=ctx.guild, author=ctx.author, channel=ctx.channel)

        if ctx.invoked_with == "select":
            query = f"SELECT {query}"

        async with ctx.typing():
            try:
                db = ctx.db.execute(query)
                data = db.fetchall()
            except sqlite3.Error as e:
                return await ctx.send(f"Error: **{type(e).__name__}**: `{e}`")

            if not data:
                await ctx.ok()
                return

            result = await self._sql_table(data)

        # replacing token because of variable formatting
        await ctx.send(result.replace(self.bot.http.token, "TOKEN_LEAKED"))  # type: ignore

    async def _eval(self, ctx: Context, code: Code, *, insert_return: bool = False) -> str:
        # copied from https://github.com/Fogapod/KiwiBot/blob/49743118661abecaab86388cb94ff8a99f9011a8/modules/owner/module_eval.py
        # (originally copied from R. Danny bot)
        glob = {
            "bot": self.bot,
            "ctx": ctx,
            "message": ctx.message,
            "guild": ctx.guild,
            "author": ctx.author,
            "channel": ctx.channel,
            "asyncio": asyncio,
            "discord": discord,
            "random": random,
        }

        fn_body = code.body

        if insert_return:
            # insert return
            code_no_last_line, maybe_nl, last_line = fn_body.rpartition("\n")

            last_line_and_indent = re.fullmatch(r"(\s*)(.*)", last_line)
            assert last_line_and_indent is not None
            last_line_indent, last_line = last_line_and_indent[1], last_line_and_indent[2]

            # ignore code that is already invalid. this may also fail if there is a multiline expression since we
            # only take last line, we do not want to put return there either
            if not last_line.startswith(("return ", "raise ", "yield ", " ", "\t")) and self._is_valid_syntax(last_line):
                last_line_with_return = f"return {last_line}"
                # may fail if this is assignment and probably some other cases
                if self._is_valid_syntax(last_line_with_return):
                    last_line = last_line_with_return

            fn_body = f"{code_no_last_line}{maybe_nl}{last_line_indent}{last_line}"

        wrapped_source = f"""\
async def __pink_eval__():
{textwrap.indent(fn_body, "    ")}\
"""

        # NOTE: docs exclicitly say exception value can be passed to format_exception_only since 3.10
        try:
            # SAFETY: owner only command
            exec(wrapped_source, glob)
        except Exception as e:
            return "".join(traceback.format_exception_only(e))

        fake_stdout = io.StringIO()

        try:
            with redirect_stdout(fake_stdout):
                returned = await glob["__pink_eval__"]()  # type: ignore
        except Exception as e:
            return f"{fake_stdout.getvalue()}{''.join(traceback.format_exception_only(e))}"

        from_stdout = fake_stdout.getvalue()

        if returned is None:
            if from_stdout:
                return from_stdout

            return "Evaluated"

        # pprint is ugly but it is better than nothing.
        # json.dumps(..., indent=2, default=lambda o: str(o)) does the job but it adds quotes around everything
        return f"{from_stdout}{pformat(returned)}"

    @staticmethod
    def _is_valid_syntax(source: str) -> bool:
        try:
            ast.parse(source)
        except SyntaxError:
            return False

        return True

    async def _exec(self, _: Context, arguments: str) -> str:
        stdout, stderr = await run_process_shell(arguments)

        if stderr:
            result = f"STDERR:\n{stderr}\n{stdout}"
        else:
            result = stdout

        return result

    async def _sql_table(self, result: list[sqlite3.Row]) -> str:
        # convert to list because otherwise iterator is exhausted
        columns = list(result[0].keys())

        no_named_columns = not list(filter(lambda c: c != PG_UNNAMED_COLUMN, columns))
        col_widths = [0 if no_named_columns and c == PG_UNNAMED_COLUMN else len(c) for c in columns]

        for row in result:
            for i, value in enumerate(row):
                col_widths[i] = max((col_widths[i], len(str(value))))

        if no_named_columns:
            header = ""
        else:
            header = f"""\
{" | ".join(f"{column:^{col_widths[i]}}" for i, column in enumerate(columns))}
{"-+-".join("-" * width for width in col_widths)}
"""

        def sanitize_value(value: Any) -> str:
            return str(value).replace("\n", "\\n")

        body = "\n".join(
            " | ".join(f"{sanitize_value(value):<{col_widths[i]}}" for i, value in enumerate(row)) for row in result
        )

        return f"```prolog\n{header}{body}```"


async def setup(bot: PINK) -> None:
    await bot.add_cog(TechAdmin(bot))
