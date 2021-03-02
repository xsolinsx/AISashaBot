import urllib

import db_management
import methods
import pyrogram
import utils

_ = utils.GetLocalizedString


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["doge", "dogify"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdDogify(client: pyrogram.Client, msg: pyrogram.types.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = (
            db_management.RChatPlugin.get_or_none(plugin="dogify", chat=msg.chat.id)
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == "private"
    if allowed:
        tmp = msg.text[len(msg.command[0]) + 2 :].split("/")
        doge_query = list(map(lambda x: urllib.parse.quote_plus(x), tmp))
        tmp = "/".join(doge_query)
        methods.ReplyPhoto(
            client=client,
            msg=msg,
            photo=f"http://dogr.io/{tmp}.png?split=false",
        )
