import typing

import pyrogram


async def anonymous_filter(_, __, msg: pyrogram.types.Message):
    """Filter anonymous messages."""
    return bool(msg.sender_chat and msg.sender_chat.id == msg.chat.id)


message_anonymous = pyrogram.filters.create(anonymous_filter, name="Anonymous")


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

    async def f(fil, _, cb_query: pyrogram.types.CallbackQuery) -> bool:
        command = None
        if cb_query.data:
            t = cb_query.data.split(fil.separator)
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


async def private_callback_filter(_, __, cb_qry: pyrogram.types.CallbackQuery) -> bool:
    """Filter callback queries sent in private chats."""
    return bool(
        cb_qry.message.chat
        and cb_qry.message.chat.type == pyrogram.enums.chat_type.ChatType.PRIVATE
    )


callback_private = pyrogram.filters.create(private_callback_filter, name="Private")


async def group_callback_filter(_, __, cb_qry: pyrogram.types.CallbackQuery) -> bool:
    """Filter callback queries sent in group chats."""
    return bool(
        cb_qry.message.chat
        and (
            cb_qry.message.chat.type == pyrogram.enums.chat_type.ChatType.GROUP
            or cb_qry.message.chat.type == pyrogram.enums.chat_type.ChatType.SUPERGROUP
        )
    )


callback_group = pyrogram.filters.create(group_callback_filter, name="Group")


async def channel_callback_filter(_, __, cb_qry: pyrogram.types.CallbackQuery) -> bool:
    """Filter callback queries sent in channels."""
    return bool(
        cb_qry.message.chat
        and cb_qry.message.chat.type == pyrogram.enums.chat_type.ChatType.CHANNEL
    )


callback_channel = pyrogram.filters.create(channel_callback_filter, name="Channel")
