import datetime
import json
import os
import re
import secrets
import sys
import time
import traceback
import urllib.request
from threading import Thread

import pyrogram

import db_management
import keyboards
import methods
import my_filters
import utils

_ = utils.GetLocalizedString


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(commands=["oldping"], prefixes=["/", "!", "#", "."])
)
def CmdOldPing(client: pyrogram.Client, msg: pyrogram.Message):
    methods.ReplyText(
        client=client,
        msg=msg,
        text=f"oldpong!\n{utils.TimeFormatter((abs(datetime.datetime.utcnow() - datetime.datetime.utcfromtimestamp(msg.date))).total_seconds() * 1000)}",
    )


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(commands=["ping"], prefixes=["/", "!", "#", "."])
)
def CmdPing(client: pyrogram.Client, msg: pyrogram.Message):
    # adapted from https://git.colinshark.de/PyroBot/PyroBot/src/branch/develop/pyrobot/modules/www.py
    start = datetime.datetime.utcnow()
    tmp: pyrogram.Message = methods.ReplyText(
        client=client, msg=msg, text="pong!",
    )
    end = datetime.datetime.utcnow()
    tmp.edit(f"pong!\n{utils.TimeFormatter((end - start).microseconds / 1000)}")


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(commands=["uptime"], prefixes=["/", "!", "#", "."])
)
def CmdUptime(client: pyrogram.Client, msg: pyrogram.Message):
    methods.ReplyText(
        client=client, msg=msg, text=f"{datetime.datetime.utcnow() - utils.start_date}"
    )


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(commands=["leave"], prefixes=["/", "!", "#", "."])
)
def CmdLeave(client: pyrogram.Client, msg: pyrogram.Message):
    client.leave_chat(msg.command[1])
    methods.ReplyText(
        client=client, msg=msg, text=_(msg.from_user.settings.language, "left_chat_X")
    )


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(commands=["pm"], prefixes=["/", "!", "#", "."])
)
def CmdPm(client: pyrogram.Client, msg: pyrogram.Message):
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(user_id, str):
        methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        methods.SendMessage(
            client=client,
            chat_id=user_id,
            text=msg.text.replace(f"{msg.command[0]} {msg.command[1]} ", "", 1),
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["todo"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdTodo(client: pyrogram.Client, msg: pyrogram.Message):
    text = f"#{msg.text[1:]}"
    fwd = None
    if msg.reply_to_message:
        fwd = msg.reply_to_message.forward(chat_id=utils.config["log_chat"])
    methods.SendMessage(
        client=client,
        chat_id=utils.config["log_chat"],
        text=text,
        reply_to_message_id=fwd.message_id if fwd else None,
    )


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["getip"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdGetIP(client: pyrogram.Client, msg: pyrogram.Message):
    ip = urllib.request.urlopen("https://ipecho.net/plain").read().decode("utf8")
    methods.ReplyText(client=client, msg=msg, text=ip)
    utils.Log(
        client=client,
        chat_id=client.ME.id,
        executer=msg.from_user.id,
        action=f"{msg.command[0]} = {ip}",
    )


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(commands=["backup"], prefixes=["/", "!", "#", "."])
)
def CmdBackup(client: pyrogram.Client, msg: pyrogram.Message):
    utils.Log(
        client=client,
        chat_id=client.ME.id,
        executer=msg.from_user.id,
        action=f"{msg.command[0]}",
    )
    methods.SendBackup(client=client)


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["exec"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdExec(client: pyrogram.Client, msg: pyrogram.Message):
    expression = msg.text[len(msg.command[0]) + 2 :]

    if expression:
        text = None
        try:
            text = str(exec(expression, dict(client=client, msg=msg)))
        except Exception as error:
            text = str(error)

        if text:
            utils.Log(
                client=client,
                chat_id=client.ME.id,
                executer=msg.from_user.id,
                action=msg.text,
            )
            if len(text) > 4096:
                file_name = f"./downloads/message_too_long_{secrets.token_hex(5)}_{time.time()}.txt"
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(text)
                if msg.command[0].lower().endswith("pvt"):
                    methods.SendDocument(
                        client=client, chat_id=msg.from_user.id, document=file_name
                    )
                    if not msg.text.startswith("del", 1):
                        methods.ReplyText(
                            client=client,
                            msg=msg,
                            text=_(
                                msg.from_user.settings.language, "sent_to_pvt"
                            ).format(client.ME.id),
                            parse_mode="html",
                        )
                else:
                    if not msg.text.startswith("del", 1):
                        methods.ReplyDocument(
                            client=client, msg=msg, document=file_name
                        )
            else:
                if msg.command[0].lower().endswith("pvt"):
                    methods.SendMessage(
                        client=client, chat_id=msg.from_user.id, text=text
                    )
                    if not msg.text.startswith("del", 1):
                        methods.ReplyText(
                            client=client,
                            msg=msg,
                            text=_(
                                msg.from_user.settings.language, "sent_to_pvt"
                            ).format(client.ME.id),
                            parse_mode="html",
                        )
                else:
                    if not msg.text.startswith("del", 1):
                        methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["eval"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdEval(client: pyrogram.Client, msg: pyrogram.Message):
    expression = msg.text[len(msg.command[0]) + 2 :]

    if expression:
        text = None
        try:
            text = str(eval(expression, dict(client=client, msg=msg)))
        except Exception as error:
            text = str(error)
        if text:
            utils.Log(
                client=client,
                chat_id=client.ME.id,
                executer=msg.from_user.id,
                action=msg.text,
            )
            if len(text) > 4096:
                file_name = f"./downloads/message_too_long_{secrets.token_hex(5)}_{time.time()}.txt"
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write(text)
                if msg.command[0].lower().endswith("pvt"):
                    methods.SendDocument(
                        client=client, chat_id=msg.from_user.id, document=file_name
                    )
                    if not msg.text.startswith("del", 1):
                        methods.ReplyText(
                            client=client,
                            msg=msg,
                            text=_(
                                msg.from_user.settings.language, "sent_to_pvt"
                            ).format(client.ME.id),
                            parse_mode="html",
                        )
                else:
                    if not msg.text.startswith("del", 1):
                        methods.ReplyDocument(
                            client=client, msg=msg, document=file_name
                        )
            else:
                if msg.command[0].lower().endswith("pvt"):
                    methods.SendMessage(
                        client=client, chat_id=msg.from_user.id, text=text
                    )
                    if not msg.text.startswith("del", 1):
                        methods.ReplyText(
                            client=client,
                            msg=msg,
                            text=_(
                                msg.from_user.settings.language, "sent_to_pvt"
                            ).format(client.ME.id),
                            parse_mode="html",
                        )
                else:
                    if not msg.text.startswith("del", 1):
                        methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["vardump"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdVardump(client: pyrogram.Client, msg: pyrogram.Message):
    text = None
    try:
        if msg.reply_to_message:
            text = msg.reply_to_message
        text = str(utils.CensorPhone(msg))
    except Exception as e:
        text = str(e)
    if text:
        if len(text) > 4096:
            file_name = (
                f"./downloads/message_too_long_{secrets.token_hex(5)}_{time.time()}.txt"
            )
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(text)
            if msg.command[0].lower().endswith("pvt"):
                methods.SendDocument(
                    client=client, chat_id=msg.from_user.id, document=file_name
                )
                if not msg.text.startswith("del", 1):
                    methods.ReplyText(
                        client=client,
                        msg=msg,
                        text=_(msg.from_user.settings.language, "sent_to_pvt").format(
                            client.ME.id
                        ),
                        parse_mode="html",
                    )
            else:
                if not msg.text.startswith("del", 1):
                    methods.ReplyDocument(client=client, msg=msg, document=file_name)
        else:
            if msg.command[0].lower().endswith("pvt"):
                methods.SendMessage(
                    client=client, chat_id=msg.from_user.id, text=f"VARDUMP\n{text}"
                )
                if not msg.text.startswith("del", 1):
                    methods.ReplyText(
                        client=client,
                        msg=msg,
                        text=_(msg.from_user.settings.language, "sent_to_pvt").format(
                            client.ME.id
                        ),
                        parse_mode="html",
                    )
            else:
                if not msg.text.startswith("del", 1):
                    methods.ReplyText(client=client, msg=msg, text=f"VARDUMP\n{text}")


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(commands=["setstring"], prefixes=["/", "!", "#", "."])
)
def CmdSetString(client: pyrogram.Client, msg: pyrogram.Message):
    if len(msg.command) == 4:
        utils.langs[msg.command[1]][msg.command[2]] = msg.command[3]
        with open(file="langs.json", mode="w", encoding="utf-8") as f:
            json.dump(obj=utils.langs, fp=f, indent=4)
        with open(file="langs.json", mode="r", encoding="utf-8") as f:
            utils.langs = json.load(fp=f)
        utils.Log(
            client=client,
            chat_id=client.ME.id,
            executer=msg.from_user.id,
            action=f"{msg.text}",
        )
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "string_X_set").format(msg.command[2]),
        )
    else:
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "error_try_again"),
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["getstring"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdGetString(client: pyrogram.Client, msg: pyrogram.Message):
    if len(msg.command) == 3:
        methods.ReplyText(
            client=client, msg=msg, text=_(msg.command[1], msg.command[2])
        )
    else:
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "error_try_again"),
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(commands=["reboot"], prefixes=["/", "!", "#", "."])
)
def CmdReboot(client: pyrogram.Client, msg: pyrogram.Message):
    utils.Log(
        client=client,
        chat_id=client.ME.id,
        executer=msg.from_user.id,
        action=f"{msg.command[0]}",
    )
    python = sys.executable
    db_management.DB.close()
    os.execl(python, python, *sys.argv)


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(commands=["reload"], prefixes=["/", "!", "#", "."])
)
def CmdReload(client: pyrogram.Client, msg: pyrogram.Message):
    with open(file="config.json", encoding="utf-8") as f:
        utils.config = json.load(fp=f)
    with open(file="langs.json", encoding="utf-8") as f:
        utils.langs = json.load(fp=f)
    utils.Log(
        client=client,
        chat_id=client.ME.id,
        executer=msg.from_user.id,
        action=f"{msg.command[0]}",
    )
    Thread(target=utils.ReloadPlugins, kwargs=dict(client=client, msg=msg)).start()


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^\(i\)botplugins", flags=re.I)
)
def CbQryBotPluginsInfo(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry,
        text=_(cb_qry.from_user.settings.language, cb_qry.data[3:]),
        show_alert=True,
    )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^botplugins is_enabled (\w+)", flags=re.I)
)
def CbQryBotPluginsEnableDisable(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    page = int(parameters[1])
    if utils.IsMasterOrBot(user_id=cb_qry.from_user.id):
        plugin: db_management.Plugins = db_management.Plugins.get_or_none(
            name=cb_qry.data.replace("botplugins is_enabled ", "")
        )
        if plugin and plugin.is_optional:
            plugin.is_enabled = not plugin.is_enabled
            try:
                plugin.save()
            except Exception as ex:
                print(ex)
                traceback.print_exc()
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "tg_error_X").format(ex),
                    show_alert=True,
                )
            else:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(
                        cb_qry.from_user.settings.language,
                        "plugin_X_enabled"
                        if plugin.is_enabled
                        else "plugin_X_disabled",
                    ).format(plugin.name),
                    show_alert=True,
                )
                utils.Log(
                    client=client,
                    chat_id=client.ME.id,
                    executer=cb_qry.from_user.id,
                    action=f"{cb_qry.data} {plugin.is_enabled}",
                    target=client.ME.id,
                )
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "error_try_again"),
                show_alert=True,
            )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildBotPluginsMenu(
                    user_settings=cb_qry.from_user.settings, page=page
                )
            ),
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^botplugins is_optional (\w+)", flags=re.I)
)
def CbQryBotPluginsMandatoryOptional(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    page = int(parameters[1])
    if utils.IsMasterOrBot(user_id=cb_qry.from_user.id):
        plugin: db_management.Plugins = db_management.Plugins.get_or_none(
            name=cb_qry.data.replace("botplugins is_optional ", "")
        )
        if plugin:
            plugin.is_optional = not plugin.is_optional
            try:
                plugin.save()
            except Exception as ex:
                print(ex)
                traceback.print_exc()
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "tg_error_X").format(ex),
                    show_alert=True,
                )
            else:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(
                        cb_qry.from_user.settings.language,
                        "plugin_X_optional"
                        if plugin.is_optional
                        else "plugin_X_mandatory",
                    ).format(plugin.name),
                    show_alert=True,
                )
                utils.Log(
                    client=client,
                    chat_id=client.ME.id,
                    executer=cb_qry.from_user.id,
                    action=f"{cb_qry.data} {plugin.is_optional}",
                    target=client.ME.id,
                )
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "error_try_again"),
                show_alert=True,
            )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildBotPluginsMenu(
                    user_settings=cb_qry.from_user.settings, page=page
                )
            ),
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^botplugins PAGES[<<|\-|\+|>>]", flags=re.I)
)
def CbQryBotPluginsPages(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    page = int(parameters[1])
    if utils.IsMasterOrBot(user_id=cb_qry.from_user.id):
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry, text=_(cb_qry.from_user.settings.language, "turning_page")
        )
        if cb_qry.data.endswith("<<"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildBotPluginsMenu(
                        user_settings=cb_qry.from_user.settings, page=0
                    )
                )
            )
        elif cb_qry.data.endswith("-"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildBotPluginsMenu(
                        user_settings=cb_qry.from_user.settings, page=page - 1
                    )
                )
            )
        elif cb_qry.data.endswith("+"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildBotPluginsMenu(
                        user_settings=cb_qry.from_user.settings, page=page + 1
                    )
                )
            )
        elif cb_qry.data.endswith(">>"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildBotPluginsMenu(
                        user_settings=cb_qry.from_user.settings, page=-1
                    )
                )
            )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(commands=["botplugins"], prefixes=["/", "!", "#", "."])
)
def CmdBotPlugins(client: pyrogram.Client, msg: pyrogram.Message):
    methods.ReplyText(
        client=client,
        msg=msg,
        text=_(msg.chat.settings.language, "botplugins"),
        reply_markup=pyrogram.InlineKeyboardMarkup(
            keyboards.BuildBotPluginsMenu(user_settings=msg.from_user.settings)
        ),
    )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^\(i\)gbanned", flags=re.I)
)
def CbQryGbannedInfo(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    text = ""
    if cb_qry.data == "(i)gbanned":
        text = _(cb_qry.from_user.settings.language, cb_qry.data)
    else:
        user = db_management.Users.get_or_none(
            id=int(cb_qry.data.replace("(i)gbanned ", ""))
        )
        if user:
            text = utils.PrintUser(user=user)
        else:
            text = int(cb_qry.data.replace("(i)gbanned ", ""))
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry, text=text, show_alert=True,
    )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^gbanned PAGES[<<|\-|\+|>>]", flags=re.I)
)
def CbQryGbannedPages(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    page = int(parameters[1])
    if utils.IsMasterOrBot(user_id=cb_qry.from_user.id):
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry, text=_(cb_qry.from_user.settings.language, "turning_page")
        )
        if cb_qry.data.endswith("<<"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildGloballyBannedUsersList(
                        chat_settings=cb_qry.from_user.settings, page=0
                    )
                )
            )
        elif cb_qry.data.endswith("-"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildGloballyBannedUsersList(
                        chat_settings=cb_qry.from_user.settings, page=page - 1
                    )
                )
            )
        elif cb_qry.data.endswith("+"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildGloballyBannedUsersList(
                        chat_settings=cb_qry.from_user.settings, page=page + 1
                    )
                )
            )
        elif cb_qry.data.endswith(">>"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildGloballyBannedUsersList(
                        chat_settings=cb_qry.from_user.settings, page=-1,
                    )
                )
            )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^gbanned add", flags=re.I)
)
def CbQryGbannedAdd(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    if utils.IsMasterOrBot(user_id=cb_qry.from_user.id):
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "ok"),
            show_alert=False,
        )
        utils.tmp_steps[cb_qry.message.chat.id] = (cb_qry, cb_qry.data)
        cb_qry.message.edit_text(
            text=_(cb_qry.from_user.settings.language, "send_user_to_gban"),
            reply_markup=pyrogram.InlineKeyboardMarkup(
                [
                    [
                        pyrogram.InlineKeyboardButton(
                            text=_(cb_qry.from_user.settings.language, "cancel"),
                            callback_data=f"cancel gbanned",
                        )
                    ]
                ]
            ),
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^gbanned remove", flags=re.I)
)
def CbQryGbannedRemove(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    page = int(parameters[1])
    if utils.IsMasterOrBot(user_id=cb_qry.from_user.id):
        user_id = int(cb_qry.data.replace("gbanned remove ", ""))
        text = methods.Ungban(
            client=client,
            executer=cb_qry.from_user.id,
            target=user_id,
            chat_id=cb_qry.from_user.id,
            chat_settings=cb_qry.from_user.settings,
        )
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=text or _(cb_qry.from_user.settings.language, "error_try_again"),
            show_alert=False,
        )
        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGloballyBannedUsersList(
                    chat_settings=cb_qry.from_user.settings, page=page
                )
            )
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["gbanned"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdGbanned(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsMasterOrBot(user_id=msg.from_user.id):
        if msg.command[0].lower().endswith("pvt"):
            methods.SendMessage(
                client=client,
                chat_id=msg.from_user.id,
                text=_(msg.chat.settings.language, "globally_banned_users"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildGloballyBannedUsersList(
                        chat_settings=msg.chat.settings, page=0
                    )
                ),
            )
            if not msg.text.startswith("del", 1):
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
                text=_(msg.chat.settings.language, "globally_banned_users"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildGloballyBannedUsersList(
                        chat_settings=msg.chat.settings, page=0
                    )
                ),
            )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^\(i\)blocked", flags=re.I)
)
def CbQryBlockedInfo(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    text = ""
    if cb_qry.data == "(i)blocked":
        text = _(cb_qry.from_user.settings.language, cb_qry.data)
    else:
        user = db_management.Users.get_or_none(
            id=int(cb_qry.data.replace("(i)blocked ", ""))
        )
        if user:
            text = utils.PrintUser(user=user)
        else:
            text = int(cb_qry.data.replace("(i)blocked ", ""))
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry, text=text, show_alert=True,
    )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^blocked PAGES[<<|\-|\+|>>]", flags=re.I)
)
def CbQryBlockedPages(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    page = int(parameters[1])
    if utils.IsMasterOrBot(user_id=cb_qry.from_user.id):
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry, text=_(cb_qry.from_user.settings.language, "turning_page")
        )
        if cb_qry.data.endswith("<<"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildBlockedUsersList(
                        chat_settings=cb_qry.from_user.settings, page=0
                    )
                )
            )
        elif cb_qry.data.endswith("-"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildBlockedUsersList(
                        chat_settings=cb_qry.from_user.settings, page=page - 1
                    )
                )
            )
        elif cb_qry.data.endswith("+"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildBlockedUsersList(
                        chat_settings=cb_qry.from_user.settings, page=page + 1
                    )
                )
            )
        elif cb_qry.data.endswith(">>"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildBlockedUsersList(
                        chat_settings=cb_qry.from_user.settings, page=-1,
                    )
                )
            )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^blocked add", flags=re.I)
)
def CbQryBlockedAdd(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    if utils.IsMasterOrBot(user_id=cb_qry.from_user.id):
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "ok"),
            show_alert=False,
        )
        utils.tmp_steps[cb_qry.message.chat.id] = (cb_qry, cb_qry.data)
        cb_qry.message.edit_text(
            text=_(cb_qry.from_user.settings.language, "send_user_to_block"),
            reply_markup=pyrogram.InlineKeyboardMarkup(
                [
                    [
                        pyrogram.InlineKeyboardButton(
                            text=_(cb_qry.from_user.settings.language, "cancel"),
                            callback_data=f"cancel blocked",
                        )
                    ]
                ]
            ),
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^blocked remove", flags=re.I)
)
def CbQryBlockedRemove(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    page = int(parameters[1])
    if utils.IsMasterOrBot(user_id=cb_qry.from_user.id):
        user_id = int(cb_qry.data.replace("blocked remove ", ""))
        text = methods.Unblock(
            client=client,
            executer=cb_qry.from_user.id,
            target=user_id,
            chat_id=cb_qry.from_user.id,
            chat_settings=cb_qry.from_user.settings,
        )
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=text or _(cb_qry.from_user.settings.language, "error_try_again"),
            show_alert=False,
        )
        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildBlockedUsersList(
                    chat_settings=cb_qry.from_user.settings, page=page
                )
            )
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["blocked"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdBlocked(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsMasterOrBot(user_id=msg.from_user.id):
        if msg.command[0].lower().endswith("pvt"):
            methods.SendMessage(
                client=client,
                chat_id=msg.from_user.id,
                text=_(msg.chat.settings.language, "blocked_users"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildBlockedUsersList(
                        chat_settings=msg.chat.settings, page=0
                    )
                ),
            )
            if not msg.text.startswith("del", 1):
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
                text=_(msg.chat.settings.language, "blocked_users"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildBlockedUsersList(
                        chat_settings=msg.chat.settings, page=0
                    )
                ),
            )
