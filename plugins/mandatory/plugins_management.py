import re
import traceback

import db_management
import dictionaries
import keyboards
import methods
import pyrogram
import utils

_ = utils.GetLocalizedString


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^\(i\)chatplugins", flags=re.I)
)
def CbQryChatPluginsInfo(client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery):
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry,
        text=_(cb_qry.from_user.settings.language, cb_qry.data[:3] + cb_qry.data[7:]),
        show_alert=True,
    )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^chatplugins PAGES[<<|\-|\+|>>]", flags=re.I)
)
def CbQryChatPluginsPages(
    client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    page = int(parameters[2])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsJuniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry, text=_(cb_qry.from_user.settings.language, "turning_page")
        )
        if cb_qry.data.endswith("<<"):
            cb_qry.message.edit_reply_markup(
                reply_markup=keyboards.BuildChatPluginsMenu(
                    chat_settings=chat_settings, page=0
                )
            )
        elif cb_qry.data.endswith("-"):
            cb_qry.message.edit_reply_markup(
                reply_markup=keyboards.BuildChatPluginsMenu(
                    chat_settings=chat_settings, page=page - 1
                )
            )
        elif cb_qry.data.endswith("+"):
            cb_qry.message.edit_reply_markup(
                reply_markup=keyboards.BuildChatPluginsMenu(
                    chat_settings=chat_settings, page=page + 1
                )
            )
        elif cb_qry.data.endswith(">>"):
            cb_qry.message.edit_reply_markup(
                reply_markup=keyboards.BuildChatPluginsMenu(
                    chat_settings=chat_settings,
                    page=-1,
                )
            )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^chatplugins is_enabled_on_chat (\w+)", flags=re.I)
)
def CbQryChatPluginsEnableDisableOnChat(
    client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    page = int(parameters[2])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        r_chat_plugin: db_management.RChatPlugin = (
            db_management.RChatPlugin.get_or_none(
                chat=chat_id,
                plugin=cb_qry.data.replace("chatplugins is_enabled_on_chat ", ""),
            )
        )
        if r_chat_plugin:
            r_chat_plugin.is_enabled_on_chat = not r_chat_plugin.is_enabled_on_chat
            try:
                r_chat_plugin.save()
            except Exception as ex:
                print(ex)
                traceback.print_exc()
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "error_try_again"),
                    show_alert=True,
                )
            else:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(
                        cb_qry.from_user.settings.language,
                        "plugin_X_enabled"
                        if r_chat_plugin.is_enabled_on_chat
                        else "plugin_X_disabled",
                    ).format(r_chat_plugin.plugin),
                    show_alert=True,
                )
                utils.Log(
                    client=client,
                    chat_id=chat_id,
                    executer=cb_qry.from_user.id,
                    action=f"{cb_qry.data} {r_chat_plugin.is_enabled_on_chat}",
                    target=chat_id,
                )
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "error_try_again"),
                show_alert=True,
            )

        cb_qry.message.edit_reply_markup(
            reply_markup=keyboards.BuildChatPluginsMenu(
                chat_settings=chat_settings, page=page
            )
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^chatplugins min_rank (\w+)", flags=re.I)
)
def CbQryChatPluginsMinRank(
    client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    page = int(parameters[2])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        r_chat_plugin: db_management.RChatPlugin = (
            db_management.RChatPlugin.get_or_none(
                chat=chat_id, plugin=cb_qry.data.replace("chatplugins min_rank ", "")
            )
        )
        if r_chat_plugin:
            i = r_chat_plugin.min_rank + 1
            if utils.IsOwnerOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
                if i > dictionaries.RANK_STRING["owner"]:
                    i = 0
            else:
                if i > dictionaries.RANK_STRING["senior_mod"]:
                    i = 0
            r_chat_plugin.min_rank = i
            try:
                r_chat_plugin.save()
            except Exception as ex:
                print(ex)
                traceback.print_exc()
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "error_try_again"),
                    show_alert=True,
                )
            else:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(
                        cb_qry.from_user.settings.language, "plugin_X_min_rank_Y"
                    ).format(
                        _(cb_qry.from_user.settings.language, r_chat_plugin.plugin),
                        _(
                            cb_qry.from_user.settings.language,
                            dictionaries.RANK_STRING[r_chat_plugin.min_rank],
                        ),
                    ),
                    show_alert=True,
                )
                utils.Log(
                    client=client,
                    chat_id=chat_id,
                    executer=cb_qry.from_user.id,
                    action=f"{cb_qry.data} {r_chat_plugin.min_rank}",
                    target=chat_id,
                )
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "error_try_again"),
                show_alert=True,
            )

        cb_qry.message.edit_reply_markup(
            reply_markup=keyboards.BuildChatPluginsMenu(
                chat_settings=chat_settings, page=page
            )
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^chatplugins (\-\d+) (\d+)", flags=re.I)
)
def CbQryChatPlugins(client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery):
    parameters = cb_qry.data.split(" ")
    chat_id = int(parameters[1])
    page = int(parameters[2])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsJuniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        cb_qry.message.edit_text(
            text=_(cb_qry.message.chat.settings.language, "chatplugins")
            + f" {utils.PrintChat(chat=chat_settings.chat)}",
            reply_markup=keyboards.BuildChatPluginsMenu(
                chat_settings=chat_settings, page=page
            ),
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(
            commands=["chatplugins", "plugins"], del_=True, pvt=True
        ),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
def CmdChatPlugins(client: pyrogram.Client, msg: pyrogram.types.Message):
    if utils.IsJuniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        if msg.command[0].lower().endswith("pvt"):
            methods.SendMessage(
                client=client,
                chat_id=msg.from_user.id,
                text=_(msg.from_user.settings.language, "chatplugins")
                + f" {utils.PrintChat(chat=msg.chat)}",
                reply_markup=keyboards.BuildChatPluginsMenu(
                    chat_settings=msg.chat.settings, page=0
                ),
            )

            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "sent_to_pvt").format(
                    client.ME.id
                ),
                parse_mode="html",
            )
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "chatplugins")
                + f" {utils.PrintChat(chat=msg.chat)}",
                reply_markup=keyboards.BuildChatPluginsMenu(
                    chat_settings=msg.chat.settings, page=0
                ),
            )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=["chatplugins", "plugins"],
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
def CmdChatPluginsChat(client: pyrogram.Client, msg: pyrogram.types.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = (
            db_management.ChatSettings.get_or_none(chat_id=chat_id)
        )
        if chat_settings:
            if utils.IsJuniorModOrHigher(user_id=msg.from_user.id, chat_id=chat_id):
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(chat_settings.language, "chatplugins")
                    + f" {utils.PrintChat(chat=chat_settings.chat)}",
                    reply_markup=keyboards.BuildChatPluginsMenu(
                        chat_settings=chat_settings, page=0
                    ),
                )
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )
