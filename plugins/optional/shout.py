import html

import pyrogram

import db_management
import methods
import utils

_ = utils.GetLocalizedString


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["shout"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdShout(client: pyrogram.Client, msg: pyrogram.types.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = (
            db_management.RChatPlugin.get_or_none(plugin="shout", chat=msg.chat.id)
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == "private"
    if allowed:
        # 30 chars maximum
        to_shout = msg.text[len(msg.command[0]) + 2 : len(msg.command[0]) + 31].upper()
        text = ""
        for character in to_shout:
            text += f"{html.escape(character)} "
        text = f"<code>{text}</code>\n"
        for i, character in enumerate(to_shout[1:]):
            spacing = "  " * i
            text += f"<code>{html.escape(character)} {spacing}{html.escape(character)}</code>\n"

        methods.ReplyText(client=client, msg=msg, text=text, parse_mode="html")
