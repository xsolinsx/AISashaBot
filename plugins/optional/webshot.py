import pyrogram

import db_management
import methods
import utils

_ = utils.GetLocalizedString


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["webshot"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdWebshot(client: pyrogram.Client, msg: pyrogram.types.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
            plugin="webshot", chat=msg.chat.id
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == "private"
    if allowed:
        methods.ReplyText(
            client=client, msg=msg, text=f"http://webshot.deam.io/{msg.command[1]}"
        )
