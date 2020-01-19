import re
import typing

import pyrogram


def callback_data(data: typing.Union[str, bytes]):
    return pyrogram.Filters.create(
        lambda fil, callback_query: fil.data == callback_query.data,
        data=data,  # "data" kwarg is accessed with "fil.data"
        name="callback_data",
    )


def callback_command(
    commands: typing.Union[bytes, list],
    separator: typing.Union[str, bytes] = " ",
    case_sensitive: bool = False,
):
    """Filter commands.
    Args:
        commands (``str`` | ``list``):
            The command or list of commands as string the filter should look for.
            Examples: "start", ["start", "help", "settings"]. When a message text containing
            a command arrives, the command itself and its arguments will be stored in the *commands*
            field of the :class:`Message <pyrogram.Message>`.
        separator (``str``, *optional*):
            The command arguments separator. Defaults to " " (white space).
            Examples: /start first second, /start-first-second, /start.first.second.
        case_sensitive (``bool``, *optional*):
            Pass True if you want your command(s) to be case sensitive. Defaults to False.
            Examples: when True, commands="Start" would trigger /Start but not /start.
    """

    def f(fil, callback_query):
        if callback_query.data:
            t = callback_query.data.split(fil.separator)
            c, a = t[0], t[1:]
            c = c if fil.case_sensitive else c.lower()
            command = ([c] + a) if c in fil.commands else None
        return bool(command)

    return pyrogram.Filters.create(
        f,
        commands={commands if case_sensitive else commands.lower()}
        if not isinstance(commands, list)
        else {c if case_sensitive else c.lower() for c in commands},
        separator=separator,
        case_sensitive=case_sensitive,
        name="Commands",
    )


def callback_regex(pattern: str, flags=None):
    """Filter messages that match a given RegEx pattern.

    Args:
        pattern (``str``):
            The RegEx pattern as string, it will be applied to the text of a message. When a pattern matches,
            all the `Match Objects <https://docs.python.org/3/library/re.html#match-objects>`_
            are stored in the *matches* field of the :class:`Message <pyrogram.Message>` itself.

        flags (``int``, *optional*):
            RegEx flags.
    """

    def f(fil, callback_query):
        matches = [i for i in fil.regex.finditer(callback_query.data)]
        return bool(matches)

    return pyrogram.Filters.create(
        f, regex=re.compile(pattern=pattern, flags=flags), name="Regex"
    )


callback_private = pyrogram.Filters.create(
    lambda _, cb_qry: bool(
        cb_qry.message.chat and cb_qry.message.chat.type == "private"
    ),
    name="Private",
)
"""Filter callback queries sent in private chats."""

callback_group = pyrogram.Filters.create(
    lambda _, cb_qry: bool(
        cb_qry.message.chat
        and (
            cb_qry.message.chat.type == "group"
            or cb_qry.message.chat.type == "supergroup"
        )
    ),
    name="Group",
)
"""Filter callback queries sent in group chats."""

callback_channel = pyrogram.Filters.create(
    lambda _, cb_qry: bool(
        cb_qry.message.chat and cb_qry.message.chat.type == "channel"
    ),
    name="Channel",
)
"""Filter callback queries sent in channels."""
