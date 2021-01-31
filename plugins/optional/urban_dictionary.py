import html
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
        commands=utils.GetCommandsVariants(
            commands=["ud", "urban", "urbandictionary"], del_=True
        ),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdUrbanDictionary(client: pyrogram.Client, msg: pyrogram.types.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
            plugin="urban_dictionary", chat=msg.chat.id
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == "private"
    if allowed:
        try:
            r = requests.get(
                "http://api.urbandictionary.com/v0/define?term="
                + urllib.parse.quote_plus(msg.text[len(msg.command[0]) + 2 :])
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
            data = r.json()
            if data["list"]:
                text = f"<code>{msg.text[len(msg.command[0]) + 2 :].upper()}</code>"
                for i, entry in enumerate(data["list"]):
                    text += (
                        "<b>"
                        + html.escape(entry["definition"])
                        + "</b>\n<i>"
                        + html.escape(entry["example"])
                        + "</i>\n\n"
                    )
                    if i >= 2:
                        break

                text = text.replace("[", "")
                text = text.replace("]", "")
                methods.ReplyText(client=client, msg=msg, text=text, parse_mode="html")
