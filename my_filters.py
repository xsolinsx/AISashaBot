import typing

import pyrogram


"""Filter anonymous messages."""
message_anonymous = pyrogram.filters.create(
    lambda _, client, msg: bool(msg.sender_chat), name="Anonymous",
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
            field of the :class:`Message <pyrogram.types.Message>`.
        separator (``str``, *optional*):
            The command arguments separator. Defaults to " " (white space).
            Examples: /start first second, /start-first-second, /start.first.second.
        case_sensitive (``bool``, *optional*):
            Pass True if you want your command(s) to be case sensitive. Defaults to False.
            Examples: when True, commands="Start" would trigger /Start but not /start.
    """

    def f(fil, client, callback_query):
        command = None
        if callback_query.data:
            t = callback_query.data.split(fil.separator)
            c, a = t[0], t[1:]
            c = c if fil.case_sensitive else c.lower()
            if c in fil.commands:
                command = [c] + a
        return bool(command)

    return pyrogram.filters.create(
        f,
        commands={commands if case_sensitive else commands.lower()}
        if not isinstance(commands, list)
        else {c if case_sensitive else c.lower() for c in commands},
        separator=separator,
        case_sensitive=case_sensitive,
        name="Commands",
    )


"""Filter callback queries sent in private chats."""
callback_private = pyrogram.filters.create(
    lambda _, client, cb_qry: bool(
        cb_qry.message.chat and cb_qry.message.chat.type == "private"
    ),
    name="Private",
)

"""Filter callback queries sent in group chats."""
callback_group = pyrogram.filters.create(
    lambda _, client, cb_qry: bool(
        cb_qry.message.chat
        and (
            cb_qry.message.chat.type == "group"
            or cb_qry.message.chat.type == "supergroup"
        )
    ),
    name="Group",
)

"""Filter callback queries sent in channels."""
callback_channel = pyrogram.filters.create(
    lambda _, client, cb_qry: bool(
        cb_qry.message.chat and cb_qry.message.chat.type == "channel"
    ),
    name="Channel",
)
