import os
import traceback
import urllib

import pyrogram
import requests

import db_management
import methods
import utils

_ = utils.GetLocalizedString


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["qrencode"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdQrEncode(client: pyrogram.Client, msg: pyrogram.types.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = (
            db_management.RChatPlugin.get_or_none(plugin="qrify", chat=msg.chat.id)
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == "private"
    if allowed:
        expression = msg.text[len(msg.command[0]) + 2 :]
        url = f"http://api.qrserver.com/v1/create-qr-code/?size=600x600&data={urllib.parse.quote_plus(expression)}"

        # if color then
        #    url = url .. "&color=" .. get_hex(color)
        # end
        # if bgcolor then
        #    url = url .. "&bgcolor=" .. get_hex(back)
        # end
        methods.ReplyPhoto(client=client, msg=msg, photo=url)


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["qrdecode"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.reply
)
def CmdQrDecode(client: pyrogram.Client, msg: pyrogram.types.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = (
            db_management.RChatPlugin.get_or_none(plugin="qrify", chat=msg.chat.id)
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == "private"
    if allowed:
        path = msg.reply_to_message.download()
        try:
            with open(path, "rb") as f:
                r = requests.post(
                    "http://api.qrserver.com/v1/read-qr-code/", files=dict(file=f)
                )
        except Exception as ex:
            print(ex)
            traceback.print_exc()
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "error_try_again") + f"\n{ex}",
            )
        else:
            data = r.json()[0]["symbol"][0]["data"]
            methods.ReplyText(client=client, msg=msg, text=data)
            os.remove(path)
