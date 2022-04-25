import urllib

import db_management
import methods
import pyrogram
import utils

_ = utils.GetLocalizedString


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["latex", "tex"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
)
@pyrogram.Client.on_edited_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["latex", "tex"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdLatex(client: pyrogram.Client, msg: pyrogram.types.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = (
            db_management.RChatPlugin.get_or_none(plugin="latex", chat=msg.chat.id)
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == pyrogram.enums.chat_type.ChatType.PRIVATE
    if allowed:
        methods.ReplyPhoto(
            client=client,
            msg=msg,
            photo="http://latex.codecogs.com/png.view?\\dpi{300}%20\\LARGE%20"
            + urllib.parse.quote_plus(msg.text[len(msg.command[0]) + 2 :]),
        )
