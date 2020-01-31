import re
import secrets

import peewee
import pyrogram

import db_management
import dictionaries
import keyboards
import methods
import my_filters
import utils

_ = utils.GetLocalizedString


@pyrogram.Client.on_message(
    pyrogram.Filters.group
    & (
        pyrogram.Filters.regex(pattern="[/!#.]start@(\\w+) new_group", flags=re.I)
        | pyrogram.Filters.group_chat_created
        | pyrogram.Filters.new_chat_members
    ),
    group=-10,
)
def AddGroup(client: pyrogram.Client, msg: pyrogram.Message):
    if msg.new_chat_members:
        if client.ME.id in map(lambda new_member: new_member.id, msg.new_chat_members):
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "group_start_message"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    [
                        [
                            pyrogram.InlineKeyboardButton(
                                text=_(msg.chat.settings.language, "start_private"),
                                url=f"t.me/{client.ME.username}",
                            )
                        ]
                    ]
                ),
            )
            msg.stop_propagation()
    else:
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "group_start_message"),
            reply_markup=pyrogram.InlineKeyboardMarkup(
                [
                    [
                        pyrogram.InlineKeyboardButton(
                            text=_(msg.chat.settings.language, "start_private"),
                            url=f"t.me/{client.ME.username}",
                        )
                    ]
                ]
            ),
        )
        msg.stop_propagation()


@pyrogram.Client.on_message(
    pyrogram.Filters.left_chat_member, group=-10,
)
def DeleteGroup(client: pyrogram.Client, msg: pyrogram.Message):
    if client.ME.id == msg.left_chat_member.id:
        msg.chat.settings.chat.delete_instance()
        msg.stop_propagation()


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^start", flags=re.I)
)
def CbQryStart(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry,
        text=_(cb_qry.from_user.settings.language, "updating"),
        show_alert=False,
    )
    services = [
        [pyrogram.InlineKeyboardButton(text=service, url=url)]
        for service, url in utils.config["donations"].items()
    ]
    services.append(
        [
            pyrogram.InlineKeyboardButton(
                text=_(cb_qry.from_user.settings.language, "back_to_main_menu"),
                callback_data="start",
            )
        ]
    )
    cb_qry.message.edit_text(
        text=_(cb_qry.from_user.settings.language, "private_start_message"),
        reply_markup=pyrogram.InlineKeyboardMarkup(
            keyboards.BuildStartMenu(
                user_settings=cb_qry.from_user.settings,
                bot_username=client.ME.username,
                channel_username=utils.config["channel"]["username"],
            )
        ),
        parse_mode="html",
    )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["start"], prefixes=["/", "!", "#", "."])
    & pyrogram.Filters.private
)
def CmdStartPrivate(client: pyrogram.Client, msg: pyrogram.Message):
    methods.ReplyText(
        client=client,
        msg=msg,
        text=_(msg.from_user.settings.language, "private_start_message"),
        reply_markup=pyrogram.InlineKeyboardMarkup(
            keyboards.BuildStartMenu(
                user_settings=msg.from_user.settings,
                bot_username=client.ME.username,
                channel_username=utils.config["channel"]["username"],
            )
        ),
    )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^mainhelp PAGES[<<|\-|\+|>>]", flags=re.I)
)
def CbQryHelpPages(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    page = int(parameters[1])
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry, text=_(cb_qry.from_user.settings.language, "turning_page")
    )
    if cb_qry.data.endswith("<<"):
        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildHelpMenu(user_settings=cb_qry.from_user.settings, page=0)
            )
        )
    elif cb_qry.data.endswith("-"):
        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildHelpMenu(
                    user_settings=cb_qry.from_user.settings, page=page - 1
                )
            )
        )
    elif cb_qry.data.endswith("+"):
        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildHelpMenu(
                    user_settings=cb_qry.from_user.settings, page=page + 1
                )
            )
        )
    elif cb_qry.data.endswith(">>"):
        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildHelpMenu(
                    user_settings=cb_qry.from_user.settings, page=-1,
                )
            )
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^mainhelp (.*)", flags=re.I)
)
def CbQryHelpPlugin(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry,
        text=_(cb_qry.from_user.settings.language, "updating"),
        show_alert=False,
    )
    text = ""
    rank = utils.GetRank(user_id=cb_qry.from_user.id)
    plugin = cb_qry.data.replace("mainhelp ", "")
    if plugin not in dictionaries.HELP_DICTIONARY:
        text = _(cb_qry.from_user.settings.language, "error_try_again")
    else:
        tmp_text = ""
        for cmd in dictionaries.HELP_DICTIONARY[plugin]:
            if cmd.isupper() and cmd.lower() in dictionaries.RANK_STRING:
                if rank < dictionaries.RANK_STRING[cmd.lower()]:
                    break
                else:
                    # print rank
                    tmp_text += (
                        "<i>"
                        + _(
                            cb_qry.from_user.settings.language, f"{cmd.lower()}"
                        ).upper()
                        + "</i>\n"
                    )
            else:
                tmp_text += (
                    _(cb_qry.from_user.settings.language, f"help_{plugin}_{cmd}") + "\n"
                )

        if tmp_text:
            text = (
                _(cb_qry.from_user.settings.language, f"help_intro")
                + "<b>"
                + _(cb_qry.from_user.settings.language, f"{plugin}").upper()
                + "</b>\n"
                + tmp_text
            )
    cb_qry.message.edit_text(
        text=text,
        reply_markup=pyrogram.InlineKeyboardMarkup(
            keyboards.BuildHelpMenu(
                user_settings=cb_qry.from_user.settings,
                selected_setting=cb_qry.data.replace("mainhelp ", ""),
            )
        ),
        parse_mode="html",
    )


@pyrogram.Client.on_callback_query(my_filters.callback_command(commands=["mainhelp"]))
def CbQryHelp(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry,
        text=_(cb_qry.from_user.settings.language, "updating"),
        show_alert=False,
    )
    text = ""
    rank = utils.GetRank(user_id=cb_qry.from_user.id)
    user_viewable_plugins = (
        p.name
        for p in db_management.Plugins.select()
        .where(db_management.Plugins.is_enabled)
        .order_by(peewee.fn.LOWER(db_management.Plugins.name))
        if p.name in dictionaries.HELP_DICTIONARY
        and dictionaries.HELP_DICTIONARY[p.name][0].lower() in dictionaries.RANK_STRING
        and rank
        >= dictionaries.RANK_STRING[dictionaries.HELP_DICTIONARY[p.name][0].lower()]
    )
    for plugin in user_viewable_plugins:
        text += (
            "<b>"
            + _(cb_qry.from_user.settings.language, f"{plugin}").upper()
            + "</b>: "
            + _(cb_qry.from_user.settings.language, f"(i)plugins {plugin}")
            + "\n"
        )
    cb_qry.message.edit_text(
        text=text,
        reply_markup=pyrogram.InlineKeyboardMarkup(
            keyboards.BuildHelpMenu(user_settings=cb_qry.from_user.settings)
        ),
        parse_mode="html",
    )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["help"], prefixes=["/", "!", "#", "."])
)
def CmdHelp(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    rank = utils.GetRank(user_id=msg.from_user.id)
    if len(msg.command) == 1:
        user_viewable_plugins = (
            p.name
            for p in db_management.Plugins.select()
            .where(db_management.Plugins.is_enabled)
            .order_by(peewee.fn.LOWER(db_management.Plugins.name))
            if p.name in dictionaries.HELP_DICTIONARY
            and dictionaries.HELP_DICTIONARY[p.name][0].lower()
            in dictionaries.RANK_STRING
            and rank
            >= dictionaries.RANK_STRING[dictionaries.HELP_DICTIONARY[p.name][0].lower()]
        )
        for plugin in user_viewable_plugins:
            text += (
                "<b>"
                + _(msg.from_user.settings.language, f"{plugin}").upper()
                + "</b>: "
                + _(msg.from_user.settings.language, f"(i)plugins {plugin}")
                + "\n"
            )

        methods.SendMessage(
            client=client,
            chat_id=msg.from_user.id,
            text=text,
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildHelpMenu(user_settings=msg.from_user.settings)
            ),
            parse_mode="html",
        )
    else:
        plugin = "_".join(msg.command[1:])
        if plugin not in dictionaries.HELP_DICTIONARY:
            text = _(msg.from_user.settings.language, "error_try_again")
        else:
            tmp_text = ""
            for cmd in dictionaries.HELP_DICTIONARY[plugin]:
                if cmd.isupper() and cmd.lower() in dictionaries.RANK_STRING:
                    if rank < dictionaries.RANK_STRING[cmd.lower()]:
                        break
                    else:
                        # print rank
                        tmp_text += (
                            "<i>"
                            + _(
                                msg.from_user.settings.language, f"{cmd.lower()}"
                            ).upper()
                            + "</i>\n"
                        )
                else:
                    tmp_text += (
                        _(msg.from_user.settings.language, f"help_{plugin}_{cmd}")
                        + "\n"
                    )

            if tmp_text:
                text = (
                    _(msg.from_user.settings.language, f"help_intro")
                    + "<b>"
                    + _(msg.from_user.settings.language, f"{plugin}").upper()
                    + "</b>\n"
                    + tmp_text
                )

        methods.SendMessage(
            client=client,
            chat_id=msg.from_user.id,
            text=text,
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildHelpMenu(
                    user_settings=msg.from_user.settings, selected_setting=plugin
                )
            ),
            parse_mode="html",
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["helpall"], prefixes=["/", "!", "#", "."])
)
def CmdHelpAll(client: pyrogram.Client, msg: pyrogram.Message):
    text = _(msg.from_user.settings.language, f"help_intro")
    rank = utils.GetRank(user_id=msg.from_user.id)
    user_viewable_plugins = (
        p.name
        for p in db_management.Plugins.select()
        .where(db_management.Plugins.is_enabled)
        .order_by(peewee.fn.LOWER(db_management.Plugins.name))
        if p.name in dictionaries.HELP_DICTIONARY
        and dictionaries.HELP_DICTIONARY[p.name][0].lower() in dictionaries.RANK_STRING
        and rank
        >= dictionaries.RANK_STRING[dictionaries.HELP_DICTIONARY[p.name][0].lower()]
    )
    for plugin in user_viewable_plugins:
        text += (
            f'<b><a href="#{plugin}">'
            + _(msg.from_user.settings.language, f"{plugin}").upper()
            + "</a></b>: "
            + _(msg.from_user.settings.language, f"(i)plugins {plugin}")
            + "\n</br>"
        )

    for plugin, list_of_commands in dictionaries.HELP_DICTIONARY.items():
        tmp_text = ""
        for cmd in list_of_commands:
            if cmd.isupper() and cmd.lower() in dictionaries.RANK_STRING:
                if rank < dictionaries.RANK_STRING[cmd.lower()]:
                    # next plugin
                    break
                else:
                    # print rank
                    tmp_text += (
                        "<i>"
                        + _(msg.from_user.settings.language, f"{cmd.lower()}").upper()
                        + "</i>\n</br>"
                    )
            else:
                tmp_text += (
                    _(msg.from_user.settings.language, f"help_{plugin}_{cmd}").replace(
                        "\n", "\n</br>"
                    )
                    + "\n</br>"
                )

        if tmp_text:
            text += (
                f'\n</br><b><a name="{plugin}">'
                + _(msg.from_user.settings.language, f"{plugin}").upper()
                + "</a></b>\n</br>"
                + tmp_text
            )
    file_name = f"./downloads/help_all_{secrets.token_hex(5)}.html"
    with open(file_name, mode="w", encoding="utf-8") as f:
        f.write('<meta charset="UTF-8">\n</br>')
        f.write(text)

    methods.SendDocument(client=client, chat_id=msg.from_user.id, document=file_name)


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^about", flags=re.I)
)
def CbQryAbout(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry,
        text=_(cb_qry.from_user.settings.language, "updating"),
        show_alert=False,
    )
    services = [
        [pyrogram.InlineKeyboardButton(text=service, url=url)]
        for service, url in utils.config["donations"].items()
    ]
    services.append(
        [
            pyrogram.InlineKeyboardButton(
                text=_(cb_qry.from_user.settings.language, "back_to_main_menu"),
                callback_data="start",
            )
        ]
    )
    cb_qry.message.edit_text(
        text=_(cb_qry.from_user.settings.language, "about_message"),
        reply_markup=pyrogram.InlineKeyboardMarkup(services),
        parse_mode="html",
    )
