import pyrogram

import db_management
import methods
import utils

_ = utils.GetLocalizedString


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["convertseconds"], prefixes=["/", "!", "#", "."])
)
def CmdConvertSeconds(client: pyrogram.Client, msg: pyrogram.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
            plugin="misc", chat=msg.chat.id
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == "private"
    if allowed:
        duration = utils.ConvertUnixToDuration(int(msg.command[1]))
        methods.ReplyText(
            client=client,
            msg=msg,
            text=(
                (f"{duration[0]} " + _(msg.chat.settings.language, "weeks") + " ")
                if duration[0]
                else ""
            )
            + (
                (f"{duration[1]} " + _(msg.chat.settings.language, "days") + " ")
                if duration[1]
                else ""
            )
            + (
                (f"{duration[2]} " + _(msg.chat.settings.language, "hours") + " ")
                if duration[2]
                else ""
            )
            + (
                (f"{duration[3]} " + _(msg.chat.settings.language, "minutes") + " ")
                if duration[3]
                else ""
            )
            + (
                (f"{duration[4]} " + _(msg.chat.settings.language, "seconds"))
                if duration[4]
                else ""
            ),
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=["convertduration"], prefixes=["/", "!", "#", "."]
    )
)
def CmdConvertDuration(client: pyrogram.Client, msg: pyrogram.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
            plugin="misc", chat=msg.chat.id
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == "private"
    if allowed:
        duration = [0] * 5
        duration[: len(msg.command[1:])] = msg.command[1:]
        duration = list(map(lambda x: int(x), reversed(duration)))
        methods.ReplyText(
            client=client,
            msg=msg,
            text=f"{utils.ConvertDurationToUnix(*duration)} "
            + _(msg.chat.settings.language, "seconds"),
        )
