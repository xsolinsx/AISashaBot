# greetings
import datetime
import html
import re
import traceback

import peewee
import pyrogram

import db_management
import dictionaries
import keyboards
import methods
import my_filters
import utils

_ = utils.GetLocalizedString


@pyrogram.Client.on_message(pyrogram.Filters.new_chat_members, group=-5)
def SendWelcome(client: pyrogram.Client, msg: pyrogram.Message):
    welcome = (
        msg.chat.settings.extras.where(
            (db_management.ChatExtras.key == "welcome")
            & (db_management.ChatExtras.is_group_data)
        )
        .get()
        .value
    )
    if welcome and msg.chat.settings.welcome_members:
        # exclude bots and people punished with kick^ from welcome
        members_to_welcome = [
            x
            for x in msg.new_chat_members
            if not x.is_bot and x.id not in utils.tmp_dicts["kickedPeople"][msg.chat.id]
        ]
        utils.InstantiateGreetingsDictionary(chat_id=msg.chat.id)
        utils.tmp_dicts["greetings"][msg.chat.id]["counter"] += len(members_to_welcome)
        if (
            utils.tmp_dicts["greetings"][msg.chat.id]["counter"]
            >= msg.chat.settings.welcome_members
        ):
            welcome_buttons = (
                msg.chat.settings.extras.where(
                    (db_management.ChatExtras.key == "welcome_buttons")
                    & (db_management.ChatExtras.is_group_data)
                )
                .get()
                .value
            )
            tmp = None
            if welcome.startswith("###"):
                welcome = welcome.split("$")
                media_id = welcome[0][3:]  # skip ###
                caption = ""
                if len(welcome) > 1:
                    # join over $ because they could have been removed with the previous split
                    caption = "$".join(welcome[1:])
                    caption = utils.AdjustMarkers(value=caption, msg=msg, welcome=True)
                try:
                    client.send_chat_action(
                        chat_id=msg.chat.id, action="upload_document",
                    )
                except pyrogram.errors.ChatWriteForbidden as ex:
                    print(ex)
                    traceback.print_exc()
                    msg.chat.settings.forbidden_writing_counter += 1
                    msg.chat.settings.save()
                    if (
                        msg.chat.settings.forbidden_writing_counter
                        >= utils.config["max_forbidden_writing_counter"]
                    ):
                        client.leave_chat(chat_id=msg.chat.id)
                    methods.SendMessage(
                        client=client,
                        chat_id=utils.config["log_chat"],
                        text=_("en", "tg_error_X").format(ex),
                    )
                except pyrogram.errors.RPCError as ex:
                    print(ex)
                    traceback.print_exc()
                    methods.ReplyText(
                        client=client,
                        msg=msg,
                        text=_(msg.chat.settings.language, "tg_error_X").format(ex),
                    )
                else:
                    try:
                        tmp: pyrogram.Message = msg.reply_cached_media(
                            file_id=media_id,
                            caption=caption,
                            reply_markup=pyrogram.InlineKeyboardMarkup(
                                keyboards.BuildWelcomeButtonsKeyboard(
                                    welcome_buttons=welcome_buttons
                                )
                            )
                            if welcome_buttons
                            else None,
                            parse_mode="html",
                        )
                    except pyrogram.errors.FloodWait as ex:
                        print(ex)
                        traceback.print_exc()
                    except pyrogram.errors.RPCError as ex:
                        print(ex)
                        traceback.print_exc()
                        methods.ReplyText(
                            client=client,
                            msg=msg,
                            text=_(msg.chat.settings.language, "tg_error_X").format(ex),
                        )
            else:
                text = utils.AdjustMarkers(value=welcome, msg=msg, welcome=True)
                if text is not None:
                    tmp: pyrogram.Message = methods.ReplyText(
                        client=client,
                        msg=msg,
                        text=text,
                        reply_markup=pyrogram.InlineKeyboardMarkup(
                            keyboards.BuildWelcomeButtonsKeyboard(
                                welcome_buttons=welcome_buttons
                            )
                        )
                        if welcome_buttons
                        else None,
                        parse_mode="html",
                    )
            if tmp:
                if utils.tmp_dicts["greetings"][msg.chat.id]["last_welcome"]:
                    client.delete_messages(
                        chat_id=msg.chat.id,
                        message_ids=utils.tmp_dicts["greetings"][msg.chat.id][
                            "last_welcome"
                        ],
                    )
                utils.tmp_dicts["greetings"][msg.chat.id]["counter"] = 0
                utils.tmp_dicts["greetings"][msg.chat.id][
                    "last_welcome"
                ] = tmp.message_id
    msg.continue_propagation()


@pyrogram.Client.on_message(pyrogram.Filters.left_chat_member, group=-5)
def SendGoodbye(client: pyrogram.Client, msg: pyrogram.Message):
    goodbye = (
        msg.chat.settings.extras.where(
            (db_management.ChatExtras.key == "goodbye")
            & (db_management.ChatExtras.is_group_data)
        )
        .get()
        .value
    )
    if goodbye:
        utils.InstantiateGreetingsDictionary(chat_id=msg.chat.id)
        tmp = None
        if goodbye.startswith("###"):
            goodbye = goodbye.split("$")
            media_id = goodbye[0][3:]
            caption = ""
            if len(goodbye) > 1:
                # join over $ because they could have been removed with the previous split
                caption = "$".join(goodbye[1:])
                caption = utils.AdjustMarkers(value=caption, msg=msg)
                try:
                    client.send_chat_action(
                        chat_id=msg.chat.id, action="typing",
                    )
                except pyrogram.errors.ChatWriteForbidden as ex:
                    print(ex)
                    traceback.print_exc()
                    msg.chat.settings.forbidden_writing_counter += 1
                    msg.chat.settings.save()
                    if (
                        msg.chat.settings.forbidden_writing_counter
                        >= utils.config["max_forbidden_writing_counter"]
                    ):
                        client.leave_chat(chat_id=msg.chat.id)
                    methods.SendMessage(
                        client=client,
                        chat_id=utils.config["log_chat"],
                        text=_("en", "tg_error_X").format(ex),
                    )
                except pyrogram.errors.RPCError as ex:
                    print(ex)
                    traceback.print_exc()
                    methods.ReplyText(
                        client=client,
                        msg=msg,
                        text=_(msg.chat.settings.language, "tg_error_X").format(ex),
                    )
                else:
                    try:
                        tmp: pyrogram.Message = msg.reply_cached_media(
                            file_id=media_id, caption=caption, parse_mode="html",
                        )
                    except pyrogram.errors.FloodWait as ex:
                        print(ex)
                        traceback.print_exc()
                    except pyrogram.errors.RPCError as ex:
                        print(ex)
                        traceback.print_exc()
                        methods.ReplyText(
                            client=client,
                            msg=msg,
                            text=_(msg.chat.settings.language, "tg_error_X").format(ex),
                        )

        else:
            tmp: pyrogram.Message = methods.ReplyText(
                client=client,
                msg=msg,
                text=utils.AdjustMarkers(value=goodbye, msg=msg),
                parse_mode="html",
            )
        if tmp:
            if utils.tmp_dicts["greetings"][msg.chat.id]["last_goodbye"]:
                client.delete_messages(
                    chat_id=msg.chat.id,
                    message_ids=utils.tmp_dicts["greetings"][msg.chat.id][
                        "last_goodbye"
                    ],
                )
            utils.tmp_dicts["greetings"][msg.chat.id]["last_goodbye"] = tmp.message_id
    msg.continue_propagation()


@pyrogram.Client.on_callback_query(
    my_filters.callback_command(
        [
            "mainsettings",
            "telegramsettings",
            "generalsettings",
            "floodsettings",
            "invitesettings",
            "greetingsettings",
            "actionsettings",
            "messagesettings",
            "nightmodesettings",
            "slowmodesettings",
            "temporarypunishmentssettings",
        ]
    )
)
def CbQrySettingsMenu(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = list()
    if len(cb_qry.data.split(" ")) > 1 and utils.IsInt(cb_qry.data.split(" ")[1]):
        parameters = cb_qry.data.split(" ")
    else:
        parameters = cb_qry.message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split(" ")
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )

    if utils.IsJuniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "updating"),
            show_alert=False,
        )
        cb_qry.message.edit_text(
            text=_(chat_settings.language, "settings")
            + f" {utils.PrintChat(chat=chat_settings.chat)}",
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings,
                    current_keyboard=cb_qry.data.split(" ")[0],
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
    my_filters.callback_regex(pattern=r"^settings", flags=re.I), group=-1
)
def CbQryCheckSettingsLocked(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if not cb_qry.data.startswith("(i)"):
        # if not an info button
        if chat_settings.are_locked and not utils.IsOwnerOrHigher(
            user_id=cb_qry.from_user.id, chat_id=chat_id
        ):
            print("locked_settings")
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "locked_settings"),
                show_alert=True,
            )
            cb_qry.stop_propagation()


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^\(i\)settings", flags=re.I)
)
def CbQrySettingsInfo(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    regex_setting_time_punishment_keyboard = re.compile(
        r"^\(i\)settings (max_temp_restrict|max_temp_ban) (weeks|days|hours|minutes|seconds)",
        re.I,
    )
    if regex_setting_time_punishment_keyboard.match(cb_qry.data):
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(
                cb_qry.from_user.settings.language, "max_temp_punishment_select_time"
            ),
            show_alert=True,
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, cb_qry.data),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^settings are_locked", flags=re.I)
)
def CbQrySettingsAreLockedChange(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    if utils.IsOwnerOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        chat_settings.are_locked = not chat_settings.are_locked
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(
                cb_qry.from_user.settings.language,
                "are_locked_on" if chat_settings.are_locked else "are_locked_off",
            ),
            show_alert=True,
        )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {chat_settings.are_locked}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard=kybrd,
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
    my_filters.callback_regex(pattern=r"^settings language", flags=re.I)
)
def CbQrySettingsLanguageChange(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    if utils.IsOwnerOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        i = utils.config["available_languages"].index(chat_settings.language) + 1
        if i >= len(utils.config["available_languages"]):
            i = 0
        chat_settings.language = utils.config["available_languages"][i]
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "selected_language").format(
                dictionaries.LANGUAGE_EMOJI.get(
                    chat_settings.language, pyrogram.Emoji.PIRATE_FLAG
                )
            ),
            show_alert=True,
        )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {chat_settings.language}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard=kybrd,
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
    my_filters.callback_regex(pattern=r"^settings is_bot_on", flags=re.I)
)
def CbQrySettingsIsBotOnChange(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    if utils.IsOwnerOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        chat_settings.is_bot_on = not chat_settings.is_bot_on
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(
                cb_qry.from_user.settings.language,
                "is_bot_enabled_on"
                if chat_settings.is_bot_on
                else "is_bot_enabled_off",
            ),
            show_alert=True,
        )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {chat_settings.is_bot_on}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard=kybrd,
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
    my_filters.callback_regex(
        pattern=r"^settings allow_temporary_punishments", flags=re.I
    )
)
def CbQrySettingsAllowTemporaryPunishmentsChange(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        chat_settings.allow_temporary_punishments = (
            not chat_settings.allow_temporary_punishments
        )
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(
                cb_qry.from_user.settings.language,
                "allow_temporary_punishments_on"
                if chat_settings.allow_temporary_punishments
                else "allow_temporary_punishments_off",
            ),
            show_alert=True,
        )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {chat_settings.allow_temporary_punishments}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard=kybrd,
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
    my_filters.callback_regex(pattern=r"^settings has_tag_alerts", flags=re.I)
)
def CbQrySettingsHasTagAlertsChange(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        chat_settings.has_tag_alerts += 1
        if chat_settings.has_tag_alerts > 2:
            chat_settings.has_tag_alerts = 0
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(
                cb_qry.from_user.settings.language,
                "has_tag_alerts_public"
                if chat_settings.has_tag_alerts == 2
                else (
                    "has_tag_alerts_in_group"
                    if chat_settings.has_tag_alerts == 1
                    else "has_tag_alerts_off"
                ),
            ),
            show_alert=True,
        )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {chat_settings.has_tag_alerts}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard=kybrd,
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
    my_filters.callback_regex(pattern=r"^settings has_pin_markers", flags=re.I)
)
def CbQrySettingsHasPinMarkersChange(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        chat_settings.has_pin_markers = not chat_settings.has_pin_markers
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(
                cb_qry.from_user.settings.language,
                "has_pin_markers_on"
                if chat_settings.has_pin_markers
                else "has_pin_markers_off",
            ),
            show_alert=True,
        )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {chat_settings.has_pin_markers}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard=kybrd,
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
    my_filters.callback_regex(pattern=r"^settings group_notices", flags=re.I)
)
def CbQrySettingsGroupNoticesChange(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    regex_setting_select_value = re.compile(
        r"^settings group_notices selectvalue(\d)", re.I
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    setting = None
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        if "selectvalue" in cb_qry.data:
            chat_settings.group_notices = int(
                regex_setting_select_value.match(cb_qry.data)[1]
            )

            chat_settings.save()
            utils.Log(
                client=client,
                chat_id=chat_id,
                executer=cb_qry.from_user.id,
                action=f"{cb_qry.data} {dictionaries.PUNISHMENT_STRING[chat_settings.group_notices]}",
                target=chat_id,
            )

            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(
                    cb_qry.from_user.settings.language, "group_notices_on_for_X"
                ).format(
                    _(
                        chat_settings.language,
                        dictionaries.PUNISHMENT_STRING[chat_settings.group_notices],
                    )
                )
                if chat_settings.group_notices
                else _(cb_qry.from_user.settings.language, "group_notices_off"),
                show_alert=True,
            )
            setting = None
        else:
            setting = "group_notices"
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "select_value"),
                show_alert=False,
            )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings,
                    current_keyboard=kybrd,
                    selected_setting=setting,
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
    my_filters.callback_regex(pattern=r"^settings is_link_public", flags=re.I)
)
def CbQrySettingsIsLinkPublicChange(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        chat_settings.is_link_public += 1
        if chat_settings.is_link_public > 2:
            chat_settings.is_link_public = 0
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(
                cb_qry.from_user.settings.language,
                "is_link_public_public"
                if chat_settings.is_link_public == 2
                else (
                    "is_link_public_in_group"
                    if chat_settings.is_link_public == 1
                    else "is_link_public_off"
                ),
            ),
            show_alert=True,
        )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {chat_settings.is_link_public}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard=kybrd,
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
    my_filters.callback_regex(
        pattern=r"^settings (.+) select(hour|minute) (\d+)", flags=re.I
    )
)
def CbQrySettingsSelectTime(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    regex_setting_select_time = re.compile(
        r"^settings (.+) select(hour|minute) (\d+)", re.I
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    setting = None
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        match = regex_setting_select_time.match(cb_qry.data)
        if match[2] == "hour":
            setting = f"{match[1]}minute"
            setattr(chat_settings, match[1], int(match[3]))
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "select_time"),
                show_alert=False,
            )
        elif match[2] == "minute":
            setting = None
            setattr(chat_settings, match[1], int(match[3]))
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "ok"),
                show_alert=False,
            )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings,
                    current_keyboard=kybrd,
                    selected_setting=setting,
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
    my_filters.callback_regex(pattern=r"^settings night_mode_(from|to)(.*)", flags=re.I)
)
def CbQrySettingsNightModeTimeChange(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    regex_setting_submenu = re.compile(r"^settings (.+)", re.I)
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    setting = None
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        setting = f"{regex_setting_submenu.match(cb_qry.data)[1]}hour"
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "select_time"),
            show_alert=False,
        )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {utils.ConvertTimedModeToTime(value=chat_settings.night_mode_from)} {utils.ConvertTimedModeToTime(value=chat_settings.night_mode_to)}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings,
                    current_keyboard=kybrd,
                    selected_setting=setting,
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
    my_filters.callback_regex(pattern=r"^settings night_mode_punishment", flags=re.I)
)
def CbQrySettingsNightModePunishmentChange(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    regex_setting_submenu = re.compile(r"^settings (.+)", re.I)
    regex_setting_select_value = re.compile(r"^settings (.+) selectvalue(\d)", re.I)
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    setting = None
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        if "selectvalue" in cb_qry.data:
            new_punishment = int(regex_setting_select_value.match(cb_qry.data)[2])
            chat_settings.night_mode_punishment = new_punishment
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(
                    cb_qry.from_user.settings.language,
                    "night_mode_punishment_on"
                    if chat_settings.night_mode_punishment
                    else "night_mode_punishment_off",
                ).format(
                    utils.ConvertTimedModeToTime(value=chat_settings.night_mode_from),
                    utils.ConvertTimedModeToTime(value=chat_settings.night_mode_to),
                    _(
                        cb_qry.from_user.settings.language,
                        f"punishment{chat_settings.night_mode_punishment}",
                    ),
                ),
                show_alert=True,
            )
        else:
            setting = regex_setting_submenu.match(cb_qry.data)[1]
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "select_value"),
                show_alert=False,
            )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {dictionaries.PUNISHMENT_STRING[chat_settings.night_mode_punishment]}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings,
                    current_keyboard=kybrd,
                    selected_setting=setting,
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
    my_filters.callback_regex(pattern=r"^settings slow_mode_(from|to)(.*)", flags=re.I)
)
def CbQrySettingsSlowModeTimeChange(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    regex_setting_submenu = re.compile(r"^settings (.+)", re.I)
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    setting = None
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        setting = f"{regex_setting_submenu.match(cb_qry.data)[1]}hour"
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "select_time"),
            show_alert=False,
        )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {utils.ConvertTimedModeToTime(value=chat_settings.slow_mode_from)} {utils.ConvertTimedModeToTime(value=chat_settings.slow_mode_to)}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings,
                    current_keyboard=kybrd,
                    selected_setting=setting,
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
    my_filters.callback_regex(pattern=r"^settings slow_mode_value", flags=re.I)
)
def CbQrySettingsSlowModeValueChange(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    regex_setting_submenu = re.compile(r"^settings (.+)", re.I)
    regex_setting_select_value = re.compile(r"^settings (.+) selectvalue(\d)", re.I)
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    setting = None
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        if "selectvalue" in cb_qry.data:
            new_value = int(regex_setting_select_value.match(cb_qry.data)[2])
            chat_settings.slow_mode_value = new_value
            # TODO update value on telegram with appropriate method when implemented by pyrogram
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(
                    cb_qry.from_user.settings.language,
                    "slow_mode_value_on"
                    if chat_settings.slow_mode_value
                    else "slow_mode_value_off",
                ).format(
                    utils.ConvertTimedModeToTime(value=chat_settings.slow_mode_from),
                    utils.ConvertTimedModeToTime(value=chat_settings.slow_mode_to),
                    _(
                        cb_qry.from_user.settings.language,
                        f"slow_mode_value{chat_settings.slow_mode_value}",
                    ),
                ),
                show_alert=True,
            )
        else:
            setting = regex_setting_submenu.match(cb_qry.data)[1]
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "select_value"),
                show_alert=False,
            )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {dictionaries.PUNISHMENT_STRING[chat_settings.night_mode_punishment]}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings,
                    current_keyboard=kybrd,
                    selected_setting=setting,
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
    my_filters.callback_regex(pattern=r"^settings allow_service_messages", flags=re.I)
)
def CbQrySettingsAllowServiceMessagesChange(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        chat_settings.allow_service_messages = not chat_settings.allow_service_messages
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(
                cb_qry.from_user.settings.language,
                "allow_service_messages_on"
                if chat_settings.allow_service_messages
                else "allow_service_messages_off",
            ),
            show_alert=False,
        )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {chat_settings.allow_service_messages}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard=kybrd,
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
    my_filters.callback_regex(pattern=r"^settings allow_media_group", flags=re.I)
)
def CbQrySettingsAllowMediaGroupChange(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        chat_settings.allow_media_group = not chat_settings.allow_media_group
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(
                cb_qry.from_user.settings.language,
                "allow_media_group_on"
                if chat_settings.allow_media_group
                else "allow_media_group_off",
            ),
            show_alert=False,
        )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {chat_settings.allow_media_group}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard=kybrd,
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
    my_filters.callback_regex(pattern=r"^settings generate_link", flags=re.I)
)
def CbQrySettingsGenerateLinkChange(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        link = None
        try:
            link = client.export_chat_invite_link(chat_id=chat_id)
        except pyrogram.errors.FloodWait as ex:
            print(ex)
            traceback.print_exc()
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "tg_flood_wait_X").format(
                    ex.x
                ),
                show_alert=True,
            )
        except pyrogram.errors.RPCError as ex:
            print(ex)
            traceback.print_exc()
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "tg_error_X").format(ex),
                show_alert=True,
            )
        chat_settings.link = link
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "link_generated"),
            show_alert=True,
        )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {chat_settings.link}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard=kybrd,
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
    my_filters.callback_regex(pattern=r"^settings set_(.+)", flags=re.I)
)
def CbQrySettingsSet(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    kybrd = parameters[0].replace("useless", "")
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        variable = cb_qry.data.replace("settings set_", "")
        utils.tmp_steps[cb_qry.message.chat.id] = (cb_qry, cb_qry.data)
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "set_variable_X").format(
                _(cb_qry.from_user.settings.language, variable)
            ),
            show_alert=False,
        )

        cb_qry.message.edit_text(
            text=_(cb_qry.from_user.settings.language, f"{variable}_help") + "\n",
            reply_markup=pyrogram.InlineKeyboardMarkup(
                [
                    [
                        pyrogram.InlineKeyboardButton(
                            text=_(cb_qry.from_user.settings.language, "cancel"),
                            callback_data=f"cancel {kybrd} {chat_id}",
                        )
                    ]
                ]
            ),
            parse_mode="html",
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^settings get_(.+)", flags=re.I)
)
def CbQrySettingsGet(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsJuniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        if cb_qry.data == "settings get_welcome":
            welcome = (
                chat_settings.extras.where(
                    (db_management.ChatExtras.key == "welcome")
                    & (db_management.ChatExtras.is_group_data)
                )
                .get()
                .value
            )
            if welcome:
                welcome_buttons = (
                    chat_settings.extras.where(
                        (db_management.ChatExtras.key == "welcome_buttons")
                        & (db_management.ChatExtras.is_group_data)
                    )
                    .get()
                    .value
                )
                if welcome.startswith("###"):
                    welcome = welcome.split("$")
                    media_id = welcome[0][3:]  # skip ###
                    caption = ""
                    if len(welcome) > 1:
                        # join over $ because they could have been removed with the previous split
                        caption = "$".join(welcome[1:])

                    cb_qry.message.reply_cached_media(
                        file_id=media_id,
                        caption=caption,
                        reply_markup=pyrogram.InlineKeyboardMarkup(
                            keyboards.BuildWelcomeButtonsKeyboard(
                                welcome_buttons=welcome_buttons
                            )
                        )
                        if welcome_buttons
                        else None,
                    )
                else:
                    methods.ReplyText(
                        client=client,
                        msg=cb_qry.message,
                        text=welcome,
                        reply_markup=pyrogram.InlineKeyboardMarkup(
                            keyboards.BuildWelcomeButtonsKeyboard(
                                welcome_buttons=welcome_buttons
                            )
                        )
                        if welcome_buttons
                        else None,
                    )
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "get_variable_X").format(
                        _(cb_qry.from_user.settings.language, "welcome")
                    ),
                    show_alert=True,
                )
            else:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "no_variable_X").format(
                        _(cb_qry.from_user.settings.language, "welcome")
                    ),
                    show_alert=True,
                )
        elif cb_qry.data == "settings get_welcome_buttons":
            welcome_buttons = (
                chat_settings.extras.where(
                    (db_management.ChatExtras.key == "welcome_buttons")
                    & (db_management.ChatExtras.is_group_data)
                )
                .get()
                .value
            )
            if welcome_buttons:
                methods.ReplyText(
                    client=client,
                    msg=cb_qry.message,
                    text=_(cb_qry.from_user.settings.language, "get_variable_X").format(
                        _(cb_qry.from_user.settings.language, "welcome_buttons")
                    ),
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildWelcomeButtonsKeyboard(
                            welcome_buttons=welcome_buttons
                        )
                    ),
                )
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "get_variable_X").format(
                        _(cb_qry.from_user.settings.language, "welcome_buttons")
                    ),
                    show_alert=True,
                )
            else:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "no_variable_X").format(
                        _(cb_qry.from_user.settings.language, "welcome_buttons")
                    ),
                    show_alert=True,
                )
        elif cb_qry.data == "settings get_goodbye":
            goodbye = (
                chat_settings.extras.where(
                    (db_management.ChatExtras.key == "goodbye")
                    & (db_management.ChatExtras.is_group_data)
                )
                .get()
                .value
            )
            if goodbye:
                if goodbye.startswith("###"):
                    goodbye = goodbye.split("$")
                    media_id = goodbye[0][3:]
                    caption = ""
                    if len(goodbye) > 1:
                        # join over $ because they could have been removed with the previous split
                        caption = "$".join(goodbye[1:])

                    cb_qry.message.reply_cached_media(file_id=media_id, caption=caption)
                else:
                    methods.ReplyText(client=client, msg=cb_qry.message, text=goodbye)
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "get_variable_X").format(
                        _(cb_qry.from_user.settings.language, "goodbye")
                    ),
                    show_alert=True,
                )
            else:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "no_variable_X").format(
                        _(cb_qry.from_user.settings.language, "goodbye")
                    ),
                    show_alert=True,
                )
        elif cb_qry.data == "settings get_rules":
            rules = chat_settings.extras.where(
                (db_management.ChatExtras.key == "rules")
                & (db_management.ChatExtras.is_group_data)
            ).get()
            if rules.value:
                methods.ReplyText(client=client, msg=cb_qry.message, text=rules.value)
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "get_variable_X").format(
                        _(cb_qry.from_user.settings.language, "rules")
                    ),
                    show_alert=True,
                )
            else:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "no_variable_X").format(
                        _(cb_qry.from_user.settings.language, "rules")
                    ),
                    show_alert=True,
                )
        elif cb_qry.data == "settings get_link":
            if chat_settings.link:
                methods.ReplyText(
                    client=client, msg=cb_qry.message, text=chat_settings.link
                )
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "get_variable_X").format(
                        _(cb_qry.from_user.settings.language, "link")
                    ),
                    show_alert=True,
                )
            else:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "no_variable_X").format(
                        _(cb_qry.from_user.settings.language, "link")
                    ),
                    show_alert=True,
                )
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data}",
            target=chat_id,
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^settings unset_(.+)", flags=re.I)
)
def CbQrySettingsUnset(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        variable = cb_qry.data.replace("settings unset_", "")
        if (
            variable == "welcome"
            or variable == "welcome_buttons"
            or variable == "goodbye"
            or variable == "rules"
        ):
            db_management.ChatExtras.update(
                value="",
                is_media=False,
                original_chat_id=None,
                original_message_id=None,
            ).where(
                (db_management.ChatExtras.chat_id == chat_settings.chat_id)
                & (db_management.ChatExtras.key == variable)
                & (db_management.ChatExtras.is_group_data)
            ).execute()
        elif variable == "link":
            chat_settings.link = None
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "invalid_variable_X").format(
                    variable
                ),
                show_alert=True,
            )

        try:
            chat_settings.save()
        except Exception as ex:
            print(ex)
            traceback.print_exc()
        else:
            utils.Log(
                client=client,
                chat_id=chat_id,
                executer=cb_qry.from_user.id,
                action=f"{cb_qry.data}",
                target=chat_id,
            )
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "unset_variable_X").format(
                    _(cb_qry.from_user.settings.language, variable)
                ),
                show_alert=True,
            )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(
        pattern=r"^settings welcome_members(\-\-|\+\+)", flags=re.I
    )
)
def CbQrySettingsWelcomeMembersPlusMinus(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        if "--" in cb_qry.data:
            chat_settings.welcome_members = max(chat_settings.welcome_members - 1, 0)
        elif "++" in cb_qry.data:
            chat_settings.welcome_members = min(
                chat_settings.welcome_members + 1, utils.config["max_welcome_members"],
            )
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(
                cb_qry.from_user.settings.language,
                "send_welcome_each_X"
                if chat_settings.welcome_members
                else "never_welcome",
            ).format(chat_settings.welcome_members),
            show_alert=True,
        )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {chat_settings.welcome_members}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard=kybrd,
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
    my_filters.callback_regex(pattern=r"^settings max_invites(\-\-|\+\+)", flags=re.I)
)
def CbQrySettingsMaxInvitesPlusMinus(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        if "--" in cb_qry.data:
            chat_settings.max_invites = max(chat_settings.max_invites - 1, 0)
        elif "++" in cb_qry.data:
            chat_settings.max_invites = min(
                chat_settings.max_invites + 1, utils.config["max_invites"]
            )
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "max_invites_X").format(
                chat_settings.max_invites
            ),
            show_alert=True,
        )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {chat_settings.max_invites}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard=kybrd,
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
    my_filters.callback_regex(
        pattern=r"^settings max_flood_time(\-\-|\+\+)", flags=re.I
    )
)
def CbQrySettingsMaxFloodTimePlusMinus(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        if "--" in cb_qry.data:
            chat_settings.max_flood_time = max(
                chat_settings.max_flood_time - 1, utils.config["min_flood_time"],
            )
        elif "++" in cb_qry.data:
            chat_settings.max_flood_time = min(
                chat_settings.max_flood_time + 1, utils.config["max_flood_time"],
            )
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "max_flood_X").format(
                chat_settings.max_flood, chat_settings.max_flood_time
            ),
            show_alert=True,
        )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {chat_settings.max_flood_time}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard=kybrd,
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
    my_filters.callback_regex(pattern=r"^settings max_flood(\-\-|\+\+)", flags=re.I)
)
def CbQrySettingsMaxFloodPlusMinus(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        if "--" in cb_qry.data:
            chat_settings.max_flood = max(
                chat_settings.max_flood - 1, utils.config["min_flood"]
            )
        elif "++" in cb_qry.data:
            chat_settings.max_flood = min(
                chat_settings.max_flood + 1, utils.config["max_flood"]
            )
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "max_flood_X").format(
                chat_settings.max_flood, chat_settings.max_flood_time
            ),
            show_alert=True,
        )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {chat_settings.max_flood}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard=kybrd,
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
    my_filters.callback_regex(pattern=r"^settings max_warns(\-\-|\+\+)", flags=re.I)
)
def CbQrySettingsMaxWarnsPlusMinus(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        if "--" in cb_qry.data:
            chat_settings.max_warns = max(chat_settings.max_warns - 1, 1)
        elif "++" in cb_qry.data:
            chat_settings.max_warns = min(
                chat_settings.max_warns + 1, utils.config["max_warns"]
            )
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "max_warns_X",).format(
                chat_settings.max_warns
            ),
            show_alert=True,
        )

        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {chat_settings.max_warns}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard=kybrd,
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
    my_filters.callback_regex(
        pattern=r"^settings (.+) (weeks|days|hours|minutes|seconds)(\-\d+|\+\d+)",
        flags=re.I,
    )
)
def CbQrySettingsModifyTempPunishmentTime(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    regex_setting_time_punishment_keyboard = re.compile(
        r"^settings (.+) (weeks|days|hours|minutes|seconds)(\-\d+|\+\d+)", re.I
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        match = regex_setting_time_punishment_keyboard.match(cb_qry.data)
        max_temp_punishment_time = getattr(chat_settings, match[1])
        seconds = 0
        # seconds can be both positive and negative
        if match[2] == "weeks":
            seconds = 60 * 60 * 24 * 7 * int(match[3])
        elif match[2] == "days":
            seconds = 60 * 60 * 24 * int(match[3])
        elif match[2] == "hours":
            seconds = 60 * 60 * int(match[3])
        elif match[2] == "minutes":
            seconds = 60 * int(match[3])
        elif match[2] == "seconds":
            seconds = int(match[3])
        max_temp_punishment_time += seconds
        if (
            max_temp_punishment_time < utils.config["min_temp_punishment_time"]
            or max_temp_punishment_time > utils.config["max_temp_punishment_time"]
        ):
            setattr(chat_settings, match[1], 0)
            max_temp_punishment_time = 0
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "no_temp_punishment"),
                show_alert=True,
            )
        else:
            setattr(chat_settings, match[1], max_temp_punishment_time)
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "ok"),
                show_alert=False,
            )

        time_tuple = utils.ConvertUnixToDuration(timestamp=max_temp_punishment_time)
        time_string = (
            pyrogram.Emoji.INFINITY
            if not max_temp_punishment_time
            else (
                (
                    str(time_tuple[0] * 7 + time_tuple[1])
                    + _(chat_settings.language, "days")
                    if time_tuple[0] * 7 + time_tuple[1]
                    else ""
                )
                + (
                    str(time_tuple[2]) + _(chat_settings.language, "hours")
                    if time_tuple[2]
                    else ""
                )
                + (
                    str(time_tuple[3]) + _(chat_settings.language, "minutes")
                    if time_tuple[3]
                    else ""
                )
                + (
                    str(time_tuple[4]) + _(chat_settings.language, "seconds")
                    if time_tuple[4]
                    else ""
                )
            )
        )
        chat_settings.save()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=cb_qry.from_user.id,
            action=f"{cb_qry.data} {time_string}",
            target=chat_id,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard=kybrd,
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
    my_filters.callback_regex(pattern=r"^settings max_temp_(restrict|ban)", flags=re.I)
)
def CbQrySettingsMaxTempPunishmentChange(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    regex_setting_submenu = re.compile(r"^settings (.+)", re.I)
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        kybrd = regex_setting_submenu.match(cb_qry.data)[1]
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(
                cb_qry.from_user.settings.language, "max_temp_punishment_select_time",
            ),
            show_alert=False,
        )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard=kybrd,
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
    my_filters.callback_regex(pattern=r"^settings (.+)", flags=re.I)
)
def CbQrySettingsChange(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    regex_setting_submenu = re.compile(r"^settings (.+)", re.I)
    regex_setting_select_value = re.compile(r"^settings (.+) selectvalue(\d)", re.I)
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    kybrd = parameters[0].replace("useless", "")
    setting = None
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        if "selectvalue" in cb_qry.data:
            setting = regex_setting_select_value.match(cb_qry.data)[1]
            new_punishment = int(regex_setting_select_value.match(cb_qry.data)[2])
            old_punishment = getattr(chat_settings, setting, None)
            error = False
            if old_punishment is not None and old_punishment != new_punishment:
                setattr(chat_settings, setting, new_punishment)
                try:
                    chat_settings.save()
                except peewee.IntegrityError as ex:
                    print(ex)
                    traceback.print_exc()
                    error = True
                    if new_punishment > old_punishment:
                        # if incrementing try everything until you find the good one
                        for i in range(new_punishment + 1, 8):
                            if (
                                not chat_settings.allow_temporary_punishments
                                and "temp" in dictionaries.PUNISHMENT_STRING[i]
                            ):
                                continue
                            try:
                                setattr(chat_settings, setting, i)
                                chat_settings.save()
                            except peewee.IntegrityError as ex:
                                print(ex)
                                traceback.print_exc()
                                continue
                            else:
                                utils.Log(
                                    client=client,
                                    chat_id=chat_id,
                                    executer=cb_qry.from_user.id,
                                    action=f"tried {cb_qry.data} got {dictionaries.PUNISHMENT_STRING[i]} instead, no problem",
                                    target=chat_id,
                                )
                            break
                    else:
                        # if decrementing just disable it
                        try:
                            setattr(chat_settings, setting, 0)
                            chat_settings.save()
                        except peewee.IntegrityError as ex:
                            print(ex)
                            traceback.print_exc()
                        else:
                            utils.Log(
                                client=client,
                                chat_id=chat_id,
                                executer=cb_qry.from_user.id,
                                action=f"tried {cb_qry.data} got {dictionaries.PUNISHMENT_STRING[0]} instead, no problem",
                                target=chat_id,
                            )
                else:
                    utils.Log(
                        client=client,
                        chat_id=chat_id,
                        executer=cb_qry.from_user.id,
                        action=f"{cb_qry.data} {dictionaries.PUNISHMENT_STRING[new_punishment]}",
                        target=chat_id,
                    )
            if error:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(
                        cb_qry.from_user.settings.language,
                        "punishment_changed_X_because_Y_not_valid",
                    ).format(
                        _(
                            chat_settings.language,
                            dictionaries.PUNISHMENT_STRING.get(
                                int(getattr(chat_settings, setting, 0))
                            ),
                        ),
                        _(
                            chat_settings.language,
                            dictionaries.PUNISHMENT_STRING.get(new_punishment),
                        ),
                    ),
                    show_alert=True,
                )
            else:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(
                        cb_qry.from_user.settings.language, "punishment_changed_X"
                    ).format(
                        _(
                            chat_settings.language,
                            dictionaries.PUNISHMENT_STRING.get(
                                int(getattr(chat_settings, setting, 0))
                            ),
                        )
                    ),
                    show_alert=False,
                )
            setting = None
        else:
            setting = regex_setting_submenu.match(cb_qry.data)[1]
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "select_value"),
                show_alert=False,
            )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings,
                    current_keyboard=kybrd,
                    selected_setting=setting,
                )
            ),
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["settings"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group
)
def CmdSettings(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsJuniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        if msg.command[0].lower().endswith("pvt"):
            methods.SendMessage(
                client=client,
                chat_id=msg.from_user.id,
                text=_(msg.from_user.settings.language, "settings")
                + f" {utils.PrintChat(chat=msg.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildGroupSettingsMenu(
                        chat_settings=msg.chat.settings,
                        current_keyboard="mainsettings",
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
                text=_(msg.chat.settings.language, "settings")
                + f" {utils.PrintChat(chat=msg.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildGroupSettingsMenu(
                        chat_settings=msg.chat.settings,
                        current_keyboard="mainsettings",
                    )
                ),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["settings"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdSettingsChat(client: pyrogram.Client, msg: pyrogram.Message):
    chat_id = None
    if len(msg.command) == 2:
        chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get_or_none(
        chat_id=chat_id
    )
    if chat_settings:
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(chat_settings.language, "settings")
            + f" {utils.PrintChat(chat=chat_settings.chat)}",
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupSettingsMenu(
                    chat_settings=chat_settings, current_keyboard="mainsettings",
                )
            ),
        )
    else:
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.from_user.settings.language, "no_chat_settings"),
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["getstaff", "staff"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group
)
def CmdStaff(client: pyrogram.Client, msg: pyrogram.Message):
    query: peewee.ModelSelect = db_management.RUserChat.select().where(
        (db_management.RUserChat.chat_id == msg.chat.id)
        & (db_management.RUserChat.rank > 1)
    ).order_by(db_management.RUserChat.rank.desc())
    already_listed = list()
    text = (
        _(msg.chat.settings.language, "staff").upper()
        + f" {utils.PrintChat(chat=msg.chat)}\n\n\n"
    )

    text += f"{_(msg.chat.settings.language, dictionaries.RANKS[4]).upper()}\n"
    subquery: peewee.ModelSelect = query.select().where(
        db_management.RUserChat.rank == 4
    )
    # useless loop as there's always one and only one owner
    for r_user_chat in subquery:
        if r_user_chat.user_id not in already_listed:
            text += f"{utils.PrintUser(user=r_user_chat.user, tag=False)}\n\n"
            already_listed.append(r_user_chat.user_id)
    # senior and junior mods
    for i in range(3, 1, -1):
        label_written = False
        subquery: peewee.ModelSelect = query.select().where(
            db_management.RUserChat.rank == i
        )
        for r_user_chat in subquery:
            if r_user_chat.user_id not in already_listed:
                if not label_written:
                    label_written = True
                    text += f"\n{_(msg.chat.settings.language, dictionaries.RANKS[i]).upper()}\n"
                text += (
                    "  "
                    + (pyrogram.Emoji.MAN_GUARD if r_user_chat.is_admin else "")
                    + f"{utils.PrintUser(user=r_user_chat.user, tag=False)}\n"
                )
                already_listed.append(r_user_chat.user_id)
    # tg admins
    label_written = False
    subquery: peewee.ModelSelect = query.select().where(
        db_management.RUserChat.is_admin
    )
    for r_user_chat in subquery:
        if r_user_chat.user_id not in already_listed:
            if not label_written:
                label_written = True
                text += (
                    _(
                        msg.chat.settings.language, dictionaries.RANKS["administrator"]
                    ).upper()
                    + f" {pyrogram.Emoji.MAN_GUARD}\n"
                )
            text += f"  {utils.PrintUser(user=r_user_chat.user, tag=False)}\n"
            already_listed.append(r_user_chat.user_id)

    methods.ReplyText(client=client, msg=msg, text=text, parse_mode="html")


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=["getstaff", "staff"], prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.private
)
def CmdStaffChat(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get_or_none(
            chat_id=chat_id
        )
        if chat_settings:
            query: peewee.ModelSelect = db_management.RUserChat.select().where(
                (db_management.RUserChat.chat_id == chat_id)
                & (db_management.RUserChat.rank > 1)
            ).order_by(db_management.RUserChat.rank.desc())
            already_listed = list()
            text = (
                _(chat_settings.language, "staff").upper()
                + f" {utils.PrintChat(chat=chat_settings.chat)}\n\n\n"
            )

            text += f"{_(chat_settings.language, dictionaries.RANKS[4]).upper()}\n"
            subquery: peewee.ModelSelect = query.select().where(
                db_management.RUserChat.rank == 4
            )
            # useless loop as there's always one and only one owner
            for r_user_chat in subquery:
                if r_user_chat.user_id not in already_listed:
                    text += f"  {utils.PrintUser(user=r_user_chat.user, tag=False)}\n\n"
                    already_listed.append(r_user_chat.user_id)
            # senior and junior mods
            for i in range(3, 1, -1):
                label_written = False
                subquery: peewee.ModelSelect = query.select().where(
                    db_management.RUserChat.rank == i
                )
                for r_user_chat in subquery:
                    if r_user_chat.user_id not in already_listed:
                        if not label_written:
                            label_written = True
                            text += f"\n{_(chat_settings.language, dictionaries.RANKS[i]).upper()}\n"
                        text += (
                            "  "
                            + (pyrogram.Emoji.MAN_GUARD if r_user_chat.is_admin else "")
                            + f"{utils.PrintUser(user=r_user_chat.user, tag=False)}\n"
                        )
                        already_listed.append(r_user_chat.user_id)
            # tg admins
            label_written = False
            subquery: peewee.ModelSelect = query.select().where(
                db_management.RUserChat.is_admin
            )
            for r_user_chat in subquery:
                if r_user_chat.user_id not in already_listed:
                    if not label_written:
                        label_written = True
                        text += (
                            _(
                                chat_settings.language,
                                dictionaries.RANKS["administrator"],
                            ).upper()
                            + f" {pyrogram.Emoji.MAN_GUARD}\n"
                        )
                    text += f"  {utils.PrintUser(user=r_user_chat.user, tag=False)}\n\n"
                    already_listed.append(r_user_chat.user_id)

            methods.ReplyText(client=client, msg=msg, text=text, parse_mode="html")
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["syncadmins"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group
)
def CmdSyncAdmins(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsJuniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        if msg.chat.id not in utils.tmp_dicts["staffUpdated"]:
            utils.tmp_dicts["staffUpdated"].add(msg.chat.id)
            try:
                db_management.DBChatAdmins(
                    client=client, chat_id=msg.chat.id, clean_up=True
                )
            except pyrogram.errors.FloodWait as ex:
                print(ex)
                traceback.print_exc()
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(msg.chat.settings.language, "tg_flood_wait_X").format(ex.x),
                )
            except pyrogram.errors.RPCError as ex:
                print(ex)
                traceback.print_exc()
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(msg.chat.settings.language, "tg_error_X").format(ex),
                )
            else:
                utils.Log(
                    client=client,
                    chat_id=msg.chat.id,
                    executer=msg.from_user.id,
                    action=f"{msg.command[0]}",
                    target=msg.chat.id,
                )
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(msg.chat.settings.language, "admins_updated"),
                )
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "command_cooldown"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["syncadmins"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdSyncAdminsChat(client: pyrogram.Client, msg: pyrogram.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get_or_none(
            chat_id=chat_id
        )
        if chat_settings:
            if utils.IsJuniorModOrHigher(user_id=msg.from_user.id, chat_id=chat_id):
                if chat_id not in utils.tmp_dicts["staffUpdated"]:
                    utils.tmp_dicts["staffUpdated"].add(chat_id)
                    try:
                        db_management.DBChatAdmins(
                            client=client, chat_id=chat_id, clean_up=True
                        )
                    except pyrogram.errors.FloodWait as ex:
                        print(ex)
                        traceback.print_exc()
                        methods.ReplyText(
                            client=client,
                            msg=msg,
                            text=_(chat_settings.language, "tg_flood_wait_X").format(
                                ex.x
                            ),
                        )
                    except pyrogram.errors.RPCError as ex:
                        print(ex)
                        traceback.print_exc()
                        methods.ReplyText(
                            client=client,
                            msg=msg,
                            text=_(chat_settings.language, "tg_error_X").format(ex),
                        )
                    else:
                        utils.Log(
                            client=client,
                            chat_id=chat_id,
                            executer=msg.from_user.id,
                            action=f"{msg.command[0]}",
                            target=chat_id,
                        )
                        methods.ReplyText(
                            client=client,
                            msg=msg,
                            text=_(chat_settings.language, "admins_updated"),
                        )
                else:
                    methods.ReplyText(
                        client=client,
                        msg=msg,
                        text=_(msg.chat.settings.language, "command_cooldown"),
                    )
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=["admins", "admin"], prefixes=["@", "/", "!", "#", "."],
    )
    & pyrogram.Filters.group
)
def CmdAdmins(client: pyrogram.Client, msg: pyrogram.Message):
    if msg.chat.id not in utils.tmp_dicts["staffContacted"]:
        utils.tmp_dicts["staffContacted"].add(msg.chat.id)
        query: peewee.ModelSelect = db_management.RUserChat.select().where(
            (db_management.RUserChat.chat_id == msg.chat.id)
            & (db_management.RUserChat.rank > 1)
        ).order_by(db_management.RUserChat.rank.desc())

        admins = list()
        cant_contact = list()
        text = (
            _(msg.chat.settings.language, "chat")
            + f": {utils.PrintChat(chat=msg.chat)}\n"
            + _(msg.chat.settings.language, "sender")
            + f": {utils.PrintUser(user=msg.from_user)}\n"
            + _(msg.chat.settings.language, "message")
            + ": {0}\n".format(
                msg.text if msg.text else (msg.caption if msg.caption else "/")
            )
            + _(msg.chat.settings.language, "hashtags")
            + f": #admins{abs(msg.chat.id)} #messageid{msg.message_id}"
        )

        # owner
        subquery: peewee.ModelSelect = query.select().where(
            db_management.RUserChat.rank == 4
        )
        # useless loop as there's always one and only one owner
        for r_user_chat in subquery:
            if r_user_chat.user_id not in admins:
                admins.append(r_user_chat.user_id)
        # senior and junior mods
        for i in range(3, 1, -1):
            subquery: peewee.ModelSelect = query.select().where(
                db_management.RUserChat.rank == i
            )
            for r_user_chat in subquery:
                if r_user_chat.user_id not in admins:
                    admins.append(r_user_chat.user_id)
        # tg admins
        subquery: peewee.ModelSelect = query.select().where(
            db_management.RUserChat.is_admin
        )
        for r_user_chat in subquery:
            if r_user_chat.user_id not in admins:
                admins.append(r_user_chat.user_id)

        for user_id in admins:
            if user_id == client.ME.id:
                continue
            try:
                methods.SendMessage(
                    client=client,
                    chat_id=user_id,
                    text=text,
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildTagKeyboard(
                            chat=msg.chat,
                            message_id=msg.message_id,
                            chat_settings=msg.chat.settings,
                            is_member=True,
                        )
                    ),
                )
            except pyrogram.errors.FloodWait as ex:
                print(ex)
                traceback.print_exc()
                cant_contact.append(
                    (
                        user_id,
                        _(msg.chat.settings.language, "tg_flood_wait_X").format(ex.x),
                    )
                )
            except pyrogram.errors.RPCError as ex:
                print(ex)
                traceback.print_exc()
                cant_contact.append(
                    (user_id, _(msg.chat.settings.language, "tg_error_X").format(ex))
                )

        cant_contact = [f"{x} {y}" for x, y in cant_contact]
        methods.ReplyText(
            client=client,
            msg=msg,
            text=f"#admins{abs(msg.chat.id)} #messageid{msg.message_id}\n"
            + (
                (
                    _(msg.chat.settings.language, "cant_contact")
                    + ":\n"
                    + "\n".join(cant_contact)
                )
                if cant_contact
                else ""
            ),
        )
        utils.Log(
            client=client,
            chat_id=msg.chat.id,
            executer=msg.from_user.id,
            action=f"{msg.command[0]}",
            target=msg.chat.id,
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["rules", "getrules"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group
)
def CmdRules(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsJuniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        rules = msg.chat.settings.extras.where(
            (db_management.ChatExtras.key == "rules")
            & (db_management.ChatExtras.is_group_data)
        ).get()
        if rules.value:
            methods.ReplyText(client=client, msg=msg, text=rules.value)
        else:
            methods.ReplyText(
                client=client, msg=msg, text=_(msg.chat.settings.language, "no_rules")
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(
            commands=["welcome", "getwelcome"], del_=True
        ),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group
)
def CmdWelcome(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsJuniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        welcome = (
            msg.chat.settings.extras.where(
                (db_management.ChatExtras.key == "welcome")
                & (db_management.ChatExtras.is_group_data)
            )
            .get()
            .value
        )
        if welcome:
            welcome_buttons = (
                msg.chat.settings.extras.where(
                    (db_management.ChatExtras.key == "welcome_buttons")
                    & (db_management.ChatExtras.is_group_data)
                )
                .get()
                .value
            )
            if welcome.startswith("###"):
                welcome = welcome.split("$")
                media_id = welcome[0][3:]  # skip ###
                caption = ""
                if len(welcome) > 1:
                    # join over $ because they could have been removed with the previous split
                    caption = "$".join(welcome[1:])
                    caption = utils.AdjustMarkers(value=caption, msg=msg, welcome=True)
                msg.reply_cached_media(
                    file_id=media_id,
                    caption=caption,
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildWelcomeButtonsKeyboard(
                            welcome_buttons=welcome_buttons
                        )
                    )
                    if welcome_buttons
                    else None,
                    parse_mode="html",
                )
            else:
                text = utils.AdjustMarkers(value=welcome, msg=msg, welcome=True)
                if text is not None:
                    methods.ReplyText(
                        client=client,
                        msg=msg,
                        text=text,
                        reply_markup=pyrogram.InlineKeyboardMarkup(
                            keyboards.BuildWelcomeButtonsKeyboard(
                                welcome_buttons=welcome_buttons
                            )
                        )
                        if welcome_buttons
                        else None,
                        parse_mode="html",
                    )
        else:
            methods.ReplyText(
                client=client, msg=msg, text=_(msg.chat.settings.language, "no_welcome")
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["newlink"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group
)
def CmdNewLink(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsSeniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        try:
            msg.chat.settings.link = client.export_chat_invite_link(chat_id=msg.chat.id)
        except pyrogram.errors.FloodWait as ex:
            print(ex)
            traceback.print_exc()
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "tg_flood_wait_X").format(ex.x),
            )
        except pyrogram.errors.RPCError as ex:
            print(ex)
            traceback.print_exc()
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "tg_error_X").format(ex),
            )
        else:
            msg.chat.settings.save()
            utils.Log(
                client=client,
                chat_id=msg.chat.id,
                executer=msg.from_user.id,
                action=f"{msg.command[0]}",
                target=msg.chat.id,
            )
            if not msg.text.startswith("del", 1):
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(msg.chat.settings.language, "new_chat_link_created"),
                )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["link"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group
)
def CmdLink(client: pyrogram.Client, msg: pyrogram.Message):
    if (
        utils.IsJuniorModOrHigher(
            user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
        )
        or msg.chat.settings.is_link_public >= 1
    ):
        if not msg.chat.settings.is_link_public:
            methods.SendMessage(
                client=client,
                chat_id=msg.from_user.id,
                text=_(
                    msg.from_user.settings.language,
                    "chat_link" if msg.chat.settings.link else "no_chat_link",
                ).format(
                    msg.chat.settings.link, html.escape(msg.chat.settings.chat.title)
                ),
                parse_mode="html",
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
                text=_(
                    msg.chat.settings.language,
                    "chat_link" if msg.chat.settings.link else "no_chat_link",
                ).format(
                    msg.chat.settings.link, html.escape(msg.chat.settings.chat.title)
                ),
                parse_mode="html",
            )
        utils.Log(
            client=client,
            chat_id=msg.chat.id,
            executer=msg.from_user.id,
            action=f"{msg.command[0]}",
            target=msg.chat.id,
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["link"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdLinkChat(client: pyrogram.Client, msg: pyrogram.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get_or_none(
            chat_id=chat_id
        )
        if chat_settings:
            if chat_settings.is_link_public == 1 and not utils.IsJuniorModOrHigher(
                user_id=msg.from_user.id, chat_id=chat_id
            ):
                try:
                    member = client.get_chat_member(
                        chat_id=chat_id, user_id=msg.from_user.id
                    )
                except pyrogram.errors.FloodWait as ex:
                    print(ex)
                    traceback.print_exc()
                except pyrogram.errors.RPCError as ex:
                    print(ex)
                    traceback.print_exc()
                else:
                    if (
                        member.status == "creator"
                        or member.status == "administrator"
                        or member.status == "member"
                        or (member.status == "restricted" and member.is_member)
                    ):
                        methods.ReplyText(
                            client=client,
                            msg=msg,
                            text=_(
                                chat_settings.language,
                                "chat_link" if chat_settings.link else "no_chat_link",
                            ).format(
                                chat_settings.link,
                                html.escape(chat_settings.chat.title),
                            ),
                            parse_mode="html",
                        )
                        utils.Log(
                            client=client,
                            chat_id=msg.chat.id,
                            executer=msg.from_user.id,
                            action=f"{msg.command[0]}",
                            target=msg.chat.id,
                        )
            elif (
                utils.IsJuniorModOrHigher(user_id=msg.from_user.id, chat_id=chat_id)
                or chat_settings.is_link_public >= 1
            ):
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(
                        chat_settings.language,
                        "chat_link" if chat_settings.link else "no_chat_link",
                    ).format(chat_settings.link, html.escape(chat_settings.chat.title)),
                    parse_mode="html",
                )
                utils.Log(
                    client=client,
                    chat_id=msg.chat.id,
                    executer=msg.from_user.id,
                    action=f"{msg.command[0]}",
                    target=msg.chat.id,
                )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^\(i\)censorships", flags=re.I)
)
def CbQryCensorshipsInfo(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    text = ""

    query: peewee.ModelSelect = db_management.ChatCensorships.select().where(
        db_management.ChatCensorships.chat == chat_id
    ).order_by(peewee.fn.LOWER(db_management.ChatCensorships.value))
    if utils.IsInt(cb_qry.data.replace("(i)censorships ", "")):
        if int(cb_qry.data.replace("(i)censorships ", "")) < len(query):
            text = _(cb_qry.from_user.settings.language, "(i)censorships").format(
                query[int(cb_qry.data.replace("(i)censorships ", ""))].value
            )
        else:
            text = _(cb_qry.from_user.settings.language, "error_try_again")
    else:
        text = _(cb_qry.from_user.settings.language, cb_qry.data)

    methods.CallbackQueryAnswer(
        cb_qry=cb_qry, text=text, show_alert=True,
    )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^censorships get (\d+)", flags=re.I)
)
def CbQryCensorshipsGet(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsJuniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        index = int(cb_qry.data.replace("censorships get ", ""))
        query: peewee.ModelSelect = chat_settings.censorships.order_by(
            peewee.fn.LOWER(db_management.ChatCensorships.value),
        )
        element = query[index] if index < len(query) else None
        if element:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "ok"),
                show_alert=False,
            )
            if element.is_media:
                try:
                    client.send_chat_action(
                        chat_id=cb_qry.message.chat.id, action="upload_document",
                    )
                except pyrogram.errors.ChatWriteForbidden as ex:
                    print(ex)
                    traceback.print_exc()
                    chat_settings.forbidden_writing_counter += 1
                    chat_settings.save()
                    if (
                        chat_settings.forbidden_writing_counter
                        >= utils.config["max_forbidden_writing_counter"]
                    ):
                        client.leave_chat(chat_id=cb_qry.message.chat.id)
                    methods.SendMessage(
                        client=client,
                        chat_id=utils.config["log_chat"],
                        text=_("en", "tg_error_X").format(ex),
                    )
                except pyrogram.errors.RPCError as ex:
                    print(ex)
                    traceback.print_exc()
                    methods.ReplyText(
                        client=client,
                        msg=cb_qry.message,
                        text=_(
                            cb_qry.message.chat.settings.language, "tg_error_X"
                        ).format(ex),
                    )
                else:
                    try:
                        cb_qry.message.reply_cached_media(file_id=element.value)
                    except pyrogram.errors.FilerefUpgradeNeeded:
                        try:
                            original_media_message: pyrogram.Message = client.get_messages(
                                chat_id=element.original_chat_id,
                                message_id=element.original_message_id,
                            )
                            type_, media = utils.ExtractMedia(
                                msg=original_media_message
                            )
                            if media and hasattr(media, "file_ref"):
                                cb_qry.message.reply_cached_media(
                                    file_id=element.value, file_ref=media.file_ref
                                )
                            else:
                                element.delete_instance()
                                methods.ReplyText(
                                    client=client,
                                    msg=cb_qry.message,
                                    text=_(
                                        cb_qry.message.chat.settings.language,
                                        "original_censorship_deleted",
                                    ),
                                )
                        except pyrogram.errors.FloodWait as ex:
                            print(ex)
                            traceback.print_exc()
                        except pyrogram.errors.RPCError as ex:
                            print(ex)
                            traceback.print_exc()
                            methods.ReplyText(
                                client=client,
                                msg=cb_qry.message,
                                text=_(
                                    cb_qry.message.chat.settings.language, "tg_error_X",
                                ).format(ex),
                            )
                    except pyrogram.errors.FloodWait as ex:
                        print(ex)
                        traceback.print_exc()
                    except pyrogram.errors.RPCError as ex:
                        print(ex)
                        traceback.print_exc()
                        methods.ReplyText(
                            client=client,
                            msg=cb_qry.message,
                            text=_(
                                cb_qry.message.chat.settings.language, "tg_error_X"
                            ).format(ex),
                        )
            else:
                if element.value is not None:
                    methods.ReplyText(
                        client=client, msg=cb_qry.message, text=element.value
                    )
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "error_try_again"),
                show_alert=True,
            )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^censorships PAGES[<<|\-|\+|>>]", flags=re.I)
)
def CbQryCensorshipsPages(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
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
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildCensorshipsList(chat_settings=chat_settings, page=0)
                )
            )
        elif cb_qry.data.endswith("-"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildCensorshipsList(
                        chat_settings=chat_settings, page=page - 1
                    )
                )
            )
        elif cb_qry.data.endswith("+"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildCensorshipsList(
                        chat_settings=chat_settings, page=page + 1
                    )
                )
            )
        elif cb_qry.data.endswith(">>"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildCensorshipsList(
                        chat_settings=chat_settings, page=-1,
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
    my_filters.callback_regex(pattern=r"^censorships add", flags=re.I)
)
def CbQryCensorshipsAdd(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "ok"),
            show_alert=False,
        )
        text = ""
        if cb_qry.data == "censorships add":
            cb_qry.message.edit_text(
                text=_(cb_qry.from_user.settings.language, "select_type_of_censorship"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildCensorshipsList(
                        chat_settings=chat_settings, selected_setting="add"
                    )
                ),
                parse_mode="html",
            )
            return
        elif cb_qry.data == "censorships add text":
            utils.tmp_steps[cb_qry.message.chat.id] = (cb_qry, cb_qry.data)
            text = _(cb_qry.from_user.settings.language, "send_text_censorship")
        elif cb_qry.data == "censorships add media":
            utils.tmp_steps[cb_qry.message.chat.id] = (cb_qry, cb_qry.data)
            text = _(cb_qry.from_user.settings.language, "send_media_censorship")
        elif cb_qry.data == "censorships add regex":
            utils.tmp_steps[cb_qry.message.chat.id] = (cb_qry, cb_qry.data)
            text = _(cb_qry.from_user.settings.language, "send_regex_censorship")
        cb_qry.message.edit_text(
            text=text,
            reply_markup=pyrogram.InlineKeyboardMarkup(
                [
                    [
                        pyrogram.InlineKeyboardButton(
                            text=_(cb_qry.from_user.settings.language, "cancel"),
                            callback_data=f"cancel censorships {chat_id}",
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
    my_filters.callback_regex(pattern=r"^censorships remove", flags=re.I)
)
def CbQryCensorshipsRemove(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    page = int(parameters[2])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        index = int(cb_qry.data.replace("censorships remove ", ""))
        query: peewee.ModelSelect = chat_settings.censorships.order_by(
            peewee.fn.LOWER(db_management.ChatCensorships.value)
        )
        element = query[index] if index < len(query) else None
        if element:
            censorship = element.value
            element.delete_instance()
            utils.Log(
                client=client,
                chat_id=chat_id,
                executer=cb_qry.from_user.id,
                action=f"{cb_qry.data} {censorship}",
                target=chat_id,
            )
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "success"),
                show_alert=False,
            )
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildCensorshipsList(
                        chat_settings=chat_settings, page=page
                    )
                )
            )
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "error_try_again"),
                show_alert=True,
            )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^censorships (\-\d+) (\d+)", flags=re.I)
)
def CbQryCensorships(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.data.split(" ")
    chat_id = int(parameters[1])
    page = int(parameters[2])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsJuniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        cb_qry.message.edit_text(
            text=_(cb_qry.message.chat.settings.language, "censorships")
            + f" {utils.PrintChat(chat=chat_settings.chat)}",
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildCensorshipsList(chat_settings=chat_settings, page=page)
            ),
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^censorships (.+)", flags=re.I)
)
def CbQryCensorshipsChangePunishment(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    regex_setting_submenu = re.compile(r"^censorships (punishment)", re.I)
    regex_setting_select_value = re.compile(
        r"^censorships punishment selectvalue(\d)", re.I
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    setting = None
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        if "selectvalue" in cb_qry.data:
            new_punishment = int(regex_setting_select_value.match(cb_qry.data)[1])
            old_punishment = chat_settings.censorships_punishment
            error = False
            if old_punishment is not None and old_punishment != new_punishment:
                chat_settings.censorships_punishment = new_punishment
                try:
                    chat_settings.save()
                except peewee.IntegrityError as ex:
                    print(ex)
                    traceback.print_exc()
                    error = True
                    if new_punishment > old_punishment:
                        # if incrementing try everything until you find the good one
                        for i in range(new_punishment + 1, 8):
                            if (
                                not chat_settings.allow_temporary_punishments
                                and "temp" in dictionaries.PUNISHMENT_STRING[i]
                            ):
                                continue
                            try:
                                chat_settings.censorships_punishment = i
                                chat_settings.save()
                            except peewee.IntegrityError as ex:
                                print(ex)
                                traceback.print_exc()
                                continue
                            else:
                                utils.Log(
                                    client=client,
                                    chat_id=chat_id,
                                    executer=cb_qry.from_user.id,
                                    action=f"tried {cb_qry.data} got {dictionaries.PUNISHMENT_STRING[i]} instead, no problem",
                                    target=chat_id,
                                )
                            break
                    else:
                        # if decrementing just disable it
                        try:
                            chat_settings.censorships_punishment = 0
                            chat_settings.save()
                        except peewee.IntegrityError as ex:
                            print(ex)
                            traceback.print_exc()
                        else:
                            utils.Log(
                                client=client,
                                chat_id=chat_id,
                                executer=cb_qry.from_user.id,
                                action=f"tried {cb_qry.data} got {dictionaries.PUNISHMENT_STRING[0]} instead, no problem",
                                target=chat_id,
                            )
                else:
                    utils.Log(
                        client=client,
                        chat_id=chat_id,
                        executer=cb_qry.from_user.id,
                        action=f"{cb_qry.data} {dictionaries.PUNISHMENT_STRING[new_punishment]}",
                        target=chat_id,
                    )
            if error:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(
                        cb_qry.from_user.settings.language,
                        "punishment_changed_X_because_Y_not_valid",
                    ).format(
                        _(
                            chat_settings.language,
                            dictionaries.PUNISHMENT_STRING.get(
                                chat_settings.censorships_punishment
                            ),
                        ),
                        _(
                            chat_settings.language,
                            dictionaries.PUNISHMENT_STRING.get(new_punishment),
                        ),
                    ),
                    show_alert=True,
                )
            else:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(
                        cb_qry.from_user.settings.language, "punishment_changed_X"
                    ).format(
                        _(
                            chat_settings.language,
                            dictionaries.PUNISHMENT_STRING.get(
                                chat_settings.censorships_punishment
                            ),
                        )
                    ),
                    show_alert=False,
                )
            setting = None
        else:
            setting = regex_setting_submenu.match(cb_qry.data)[1]
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "select_value"),
                show_alert=False,
            )

        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildCensorshipsList(
                    chat_settings=chat_settings,
                    page=int(parameters[2]),
                    selected_setting=setting,
                )
            ),
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(
            commands=["censorships"], del_=True, pvt=True
        ),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group
)
def CmdCensorships(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsJuniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        if msg.command[0].lower().endswith("pvt"):
            methods.SendMessage(
                client=client,
                chat_id=msg.from_user.id,
                text=_(msg.chat.settings.language, "censorships")
                + f" {utils.PrintChat(chat=msg.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildCensorshipsList(
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
                    keyboards.BuildCensorshipsList(
                        chat_settings=msg.chat.settings, page=0
                    )
                ),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["censorships"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdCensorshipsChat(client: pyrogram.Client, msg: pyrogram.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get_or_none(
            chat_id=chat_id
        )
        if chat_settings:
            if utils.IsJuniorModOrHigher(user_id=msg.from_user.id, chat_id=chat_id):
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(chat_settings.language, "censorships")
                    + f" {utils.PrintChat(chat=chat_settings.chat)}",
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildCensorshipsList(
                            chat_settings=chat_settings, page=0
                        )
                    ),
                )
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["pin"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdPin(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsJuniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        try:
            msg.reply_to_message.pin(disable_notification=False)
        except pyrogram.errors.FloodWait as ex:
            print(ex)
            traceback.print_exc()
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "tg_flood_wait_X").format(ex.x),
            )
        except pyrogram.errors.RPCError as ex:
            print(ex)
            traceback.print_exc()
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "tg_error_X").format(ex),
            )
        else:
            if msg.chat.settings.has_pin_markers:
                methods.ReplyText(
                    client=client,
                    msg=msg.reply_to_message,
                    text=f"#pin{abs(msg.chat.id)}",
                )
            utils.Log(
                client=client,
                chat_id=msg.chat.id,
                executer=msg.from_user.id,
                action=f"{msg.command[0]}",
                target=msg.chat.id,
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["silentpin"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdSilentPin(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsJuniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        try:
            msg.reply_to_message.pin(disable_notification=True)
        except pyrogram.errors.FloodWait as ex:
            print(ex)
            traceback.print_exc()
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "tg_flood_wait_X").format(ex.x),
            )
        except pyrogram.errors.RPCError as ex:
            print(ex)
            traceback.print_exc()
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "tg_error_X").format(ex),
            )
        else:
            if msg.chat.settings.has_pin_markers:
                methods.ReplyText(
                    client=client,
                    msg=msg.reply_to_message,
                    text=f"#pin{abs(msg.chat.id)}",
                )
            utils.Log(
                client=client,
                chat_id=msg.chat.id,
                executer=msg.from_user.id,
                action=f"{msg.command[0]}",
                target=msg.chat.id,
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["unpin"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group
)
def CmdUnpin(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsJuniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        try:
            client.unpin_chat_message(chat_id=msg.chat.id)
        except pyrogram.errors.FloodWait as ex:
            print(ex)
            traceback.print_exc()
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "tg_flood_wait_X").format(ex.x),
            )
        except pyrogram.errors.RPCError as ex:
            print(ex)
            traceback.print_exc()
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "tg_error_X").format(ex),
            )
        else:
            utils.Log(
                client=client,
                chat_id=msg.chat.id,
                executer=msg.from_user.id,
                action=f"{msg.command[0]}",
                target=msg.chat.id,
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["setlog"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.group
    & pyrogram.Filters.forwarded
)
def CmdSetlog(client: pyrogram.Client, msg: pyrogram.Message):
    if msg.forward_from_chat:
        if utils.IsSeniorModOrHigher(
            user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
        ):
            try:
                methods.SendMessage(
                    client=client,
                    chat_id=msg.forward_from_chat.id,
                    text=_(msg.chat.settings.language, "log_channel_of_X").format(
                        msg.chat.title, msg.chat.id
                    ),
                )
            except pyrogram.errors.RPCError as ex:
                print(ex)
                traceback.print_exc()
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(msg.from_user.settings.language, "tg_error_X").format(ex),
                )
            else:
                msg.chat.settings.log_channel = msg.forward_from_chat.id
                msg.chat.settings.save()
                utils.Log(
                    client=client,
                    chat_id=msg.chat.id,
                    executer=msg.from_user.id,
                    action=f"{msg.command[0]} {msg.chat.settings.log_channel}",
                    target=msg.chat.id,
                )
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(msg.chat.settings.language, "log_channel_set_X").format(
                        msg.forward_from_chat.title, msg.forward_from_chat.id
                    ),
                )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["setlog"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.group
    & ~pyrogram.Filters.forwarded
)
def CmdSetlogHelp(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsSeniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "log_channel_help"),
            parse_mode="html",
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^\(i\)whitelistedchats", flags=re.I)
)
def CbQryWhitelistedChatsInfo(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    text = ""
    if cb_qry.data == "(i)whitelistedchats":
        text = _(cb_qry.from_user.settings.language, cb_qry.data)
    else:
        weird_id = int(cb_qry.data.replace("(i)whitelistedchats ", ""))
        if weird_id > 0:
            chat = db_management.Chats.get_or_none(id=int(f"-100{weird_id}"))
            chat = chat or db_management.Chats.get_or_none(id=int(f"-{weird_id}"))
        else:
            chat = db_management.Chats.get_or_none(id=weird_id)
        if chat:
            text = utils.PrintChat(chat=chat)
        else:
            text = _(
                cb_qry.from_user.settings.language, "whitelistedchat_no_correspondence"
            ).format(f"-100{weird_id}", f"-{weird_id}")
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry, text=text, show_alert=True,
    )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(
        pattern=r"^whitelistedchats PAGES[<<|\-|\+|>>]", flags=re.I
    )
)
def CbQryWhitelistedChatsPages(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
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
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedChatsList(
                        chat_settings=chat_settings, page=0
                    )
                )
            )
        elif cb_qry.data.endswith("-"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedChatsList(
                        chat_settings=chat_settings, page=page - 1
                    )
                )
            )
        elif cb_qry.data.endswith("+"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedChatsList(
                        chat_settings=chat_settings, page=page + 1
                    )
                )
            )
        elif cb_qry.data.endswith(">>"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedChatsList(
                        chat_settings=chat_settings, page=-1,
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
    my_filters.callback_regex(pattern=r"^whitelistedchats add", flags=re.I)
)
def CbQryWhitelistedChatsAdd(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "ok"),
            show_alert=False,
        )
        utils.tmp_steps[cb_qry.message.chat.id] = (cb_qry, cb_qry.data)
        cb_qry.message.edit_text(
            text=_(cb_qry.from_user.settings.language, "send_chat_to_whitelist"),
            reply_markup=pyrogram.InlineKeyboardMarkup(
                [
                    [
                        pyrogram.InlineKeyboardButton(
                            text=_(cb_qry.from_user.settings.language, "cancel"),
                            callback_data=f"cancel whitelistedchats {chat_id}",
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
    my_filters.callback_regex(pattern=r"^whitelistedchats remove", flags=re.I)
)
def CbQryWhitelistedChatsRemove(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
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
        whitelisted_chat_id = int(cb_qry.data.replace("whitelistedchats remove ", ""))
        element = db_management.ChatWhitelistedChats.get_or_none(
            chat=chat_id, whitelisted_chat=whitelisted_chat_id
        )
        if element:
            element.delete_instance()
            utils.Log(
                client=client,
                chat_id=chat_id,
                executer=cb_qry.from_user.id,
                action=f"{cb_qry.data} {whitelisted_chat_id}",
                target=chat_id,
            )
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "success"),
                show_alert=False,
            )
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedChatsList(
                        chat_settings=chat_settings, page=page
                    )
                )
            )
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "error_try_again"),
                show_alert=True,
            )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^whitelistedchats (\-\d+) (\d+)", flags=re.I)
)
def CbQryWhitelistedChats(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.data.split(" ")
    chat_id = int(parameters[1])
    page = int(parameters[2])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsJuniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        cb_qry.message.edit_text(
            text=_(cb_qry.message.chat.settings.language, "whitelisted_chats")
            + f" {utils.PrintChat(chat=chat_settings.chat)}",
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildWhitelistedChatsList(
                    chat_settings=chat_settings, page=page
                )
            ),
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(
            commands=["whitelistedchats", "chatswhitelist"], del_=True, pvt=True
        ),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group
)
def CmdWhitelistedChats(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsJuniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        if msg.command[0].lower().endswith("pvt"):
            methods.SendMessage(
                client=client,
                chat_id=msg.from_user.id,
                text=_(msg.chat.settings.language, "whitelisted_chats")
                + f" {utils.PrintChat(chat=msg.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedChatsList(
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
                text=_(msg.chat.settings.language, "whitelisted_chats")
                + f" {utils.PrintChat(chat=msg.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedChatsList(
                        chat_settings=msg.chat.settings, page=0
                    )
                ),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=["whitelistedchats", "chatswhitelist"], prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.private
)
def CmdWhitelistedChatsChat(client: pyrogram.Client, msg: pyrogram.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get_or_none(
            chat_id=chat_id
        )
        if chat_settings:
            if utils.IsJuniorModOrHigher(user_id=msg.from_user.id, chat_id=chat_id):
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(chat_settings.language, "whitelisted_chats")
                    + f" {utils.PrintChat(chat=chat_settings.chat)}",
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildWhitelistedChatsList(
                            chat_settings=chat_settings, page=0
                        )
                    ),
                )
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^\(i\)whitelistedgbanned", flags=re.I)
)
def CbQryWhitelistedGbannedInfo(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
):
    text = ""
    if cb_qry.data == "(i)whitelistedgbanned":
        text = _(cb_qry.from_user.settings.language, cb_qry.data)
    else:
        user = db_management.Users.get_or_none(
            id=int(cb_qry.data.replace("(i)whitelistedgbanned ", ""))
        )
        if user:
            text = utils.PrintUser(user=user)
        else:
            text = int(cb_qry.data.replace("(i)whitelistedgbanned ", ""))
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry, text=text, show_alert=True,
    )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(
        pattern=r"^whitelistedgbanned PAGES[<<|\-|\+|>>]", flags=re.I
    )
)
def CbQryWhitelistedGbannedPages(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
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
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedGbannedUsersList(
                        chat_settings=chat_settings, page=0
                    )
                )
            )
        elif cb_qry.data.endswith("-"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedGbannedUsersList(
                        chat_settings=chat_settings, page=page - 1
                    )
                )
            )
        elif cb_qry.data.endswith("+"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedGbannedUsersList(
                        chat_settings=chat_settings, page=page + 1
                    )
                )
            )
        elif cb_qry.data.endswith(">>"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedGbannedUsersList(
                        chat_settings=chat_settings, page=-1,
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
    my_filters.callback_regex(pattern=r"^whitelistedgbanned add", flags=re.I)
)
def CbQryWhitelistedGbannedAdd(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "ok"),
            show_alert=False,
        )
        utils.tmp_steps[cb_qry.message.chat.id] = (cb_qry, cb_qry.data)
        cb_qry.message.edit_text(
            text=_(cb_qry.from_user.settings.language, "send_gbanned_to_whitelist"),
            reply_markup=pyrogram.InlineKeyboardMarkup(
                [
                    [
                        pyrogram.InlineKeyboardButton(
                            text=_(cb_qry.from_user.settings.language, "cancel"),
                            callback_data=f"cancel whitelistedgbanned {chat_id}",
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
    my_filters.callback_regex(pattern=r"^whitelistedgbanned remove", flags=re.I)
)
def CbQryWhitelistedGbannedRemove(
    client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery
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
        user_id = int(cb_qry.data.replace("whitelistedgbanned remove ", ""))
        user = db_management.RUserChat.get_or_none(chat_id=chat_id, user_id=user_id)
        if user:
            user.is_global_ban_whitelisted = False
            user.save()
            utils.Log(
                client=client,
                chat_id=chat_id,
                executer=cb_qry.from_user.id,
                action=f"{cb_qry.data} {user.user_id} - {user.user.first_name}",
                target=chat_id,
            )
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "success"),
                show_alert=False,
            )
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedUsersList(
                        chat_settings=chat_settings, page=page
                    )
                )
            )
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "error_try_again"),
                show_alert=True,
            )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^whitelistedgbanned (\-\d+) (\d+)", flags=re.I)
)
def CbQryWhitelistedGbanned(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.data.split(" ")
    chat_id = int(parameters[1])
    page = int(parameters[2])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsJuniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        cb_qry.message.edit_text(
            text=_(cb_qry.message.chat.settings.language, "whitelistedgbanned_users")
            + f" {utils.PrintChat(chat=chat_settings.chat)}",
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildWhitelistedGbannedUsersList(
                    chat_settings=chat_settings, page=page
                )
            ),
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(
            commands=["whitelistedgbanned", "whitelistedgban"], del_=True, pvt=True
        ),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group
)
def CmdWhitelistedGbanned(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsJuniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        if msg.command[0].lower().endswith("pvt"):
            methods.SendMessage(
                client=client,
                chat_id=msg.from_user.id,
                text=_(msg.chat.settings.language, "whitelistedgbanned_users")
                + f" {utils.PrintChat(chat=msg.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedGbannedUsersList(
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
                text=_(msg.chat.settings.language, "whitelistedgbanned_users")
                + f" {utils.PrintChat(chat=msg.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedGbannedUsersList(
                        chat_settings=msg.chat.settings, page=0
                    )
                ),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=["whitelistedgbanned", "whitelistedgban"],
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.private
)
def CmdWhitelistedGbannedChat(client: pyrogram.Client, msg: pyrogram.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get_or_none(
            chat_id=chat_id
        )
        if chat_settings:
            if utils.IsJuniorModOrHigher(user_id=msg.from_user.id, chat_id=chat_id):
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(chat_settings.language, "whitelistedgbanned_users")
                    + f" {utils.PrintChat(chat=chat_settings.chat)}",
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildWhitelistedGbannedUsersList(
                            chat_settings=chat_settings, page=0
                        )
                    ),
                )
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^\(i\)whitelisted", flags=re.I)
)
def CbQryWhitelistedInfo(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    text = ""
    if cb_qry.data == "(i)whitelisted ":
        text = _(cb_qry.from_user.settings.language, cb_qry.data)
    else:
        user = db_management.Users.get_or_none(
            id=int(cb_qry.data.replace("(i)whitelisted ", ""))
        )
        if user:
            text = utils.PrintUser(user=user)
        else:
            text = int(cb_qry.data.replace("(i)whitelisted ", ""))
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry, text=text, show_alert=True,
    )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^whitelisted PAGES[<<|\-|\+|>>]", flags=re.I)
)
def CbQryWhitelistedPages(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
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
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedUsersList(
                        chat_settings=chat_settings, page=0
                    )
                )
            )
        elif cb_qry.data.endswith("-"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedUsersList(
                        chat_settings=chat_settings, page=page - 1
                    )
                )
            )
        elif cb_qry.data.endswith("+"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedUsersList(
                        chat_settings=chat_settings, page=page + 1
                    )
                )
            )
        elif cb_qry.data.endswith(">>"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedUsersList(
                        chat_settings=chat_settings, page=-1,
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
    my_filters.callback_regex(pattern=r"^whitelisted add", flags=re.I)
)
def CbQryWhitelistedAdd(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "ok"),
            show_alert=False,
        )
        utils.tmp_steps[cb_qry.message.chat.id] = (cb_qry, cb_qry.data)
        cb_qry.message.edit_text(
            text=_(cb_qry.from_user.settings.language, "send_user_to_whitelist"),
            reply_markup=pyrogram.InlineKeyboardMarkup(
                [
                    [
                        pyrogram.InlineKeyboardButton(
                            text=_(cb_qry.from_user.settings.language, "cancel"),
                            callback_data=f"cancel whitelisted {chat_id}",
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
    my_filters.callback_regex(pattern=r"^whitelisted remove", flags=re.I)
)
def CbQryWhitelistedRemove(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    page = int(parameters[2])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        user_id = int(cb_qry.data.replace("whitelisted remove ", ""))
        user = db_management.RUserChat.get_or_none(chat_id=chat_id, user_id=user_id)
        if user:
            user.is_whitelisted = False
            user.save()
            utils.Log(
                client=client,
                chat_id=chat_id,
                executer=cb_qry.from_user.id,
                action=f"{cb_qry.data} {user.user_id} - {user.user.first_name}",
                target=chat_id,
            )
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "success"),
                show_alert=False,
            )
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedUsersList(
                        chat_settings=chat_settings, page=page
                    )
                )
            )
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "error_try_again"),
                show_alert=True,
            )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^whitelisted (\-\d+) (\d+)", flags=re.I)
)
def CbQryWhitelisted(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.data.split(" ")
    chat_id = int(parameters[1])
    page = int(parameters[2])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsJuniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        cb_qry.message.edit_text(
            text=_(cb_qry.message.chat.settings.language, "whitelisted_users")
            + f" {utils.PrintChat(chat=chat_settings.chat)}",
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildWhitelistedUsersList(
                    chat_settings=chat_settings, page=page
                )
            ),
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(
            commands=["whitelisted"], del_=True, pvt=True
        ),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group
)
def CmdWhitelisted(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsJuniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        if msg.command[0].lower().endswith("pvt"):
            methods.SendMessage(
                client=client,
                chat_id=msg.from_user.id,
                text=_(msg.chat.settings.language, "whitelisted_users")
                + f" {utils.PrintChat(chat=msg.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedUsersList(
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
                text=_(msg.chat.settings.language, "whitelisted_users")
                + f" {utils.PrintChat(chat=msg.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedUsersList(
                        chat_settings=msg.chat.settings, page=0
                    )
                ),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["whitelisted"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdWhitelistedChat(client: pyrogram.Client, msg: pyrogram.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get_or_none(
            chat_id=chat_id
        )
        if chat_settings:
            if utils.IsJuniorModOrHigher(user_id=msg.from_user.id, chat_id=chat_id):
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(chat_settings.language, "whitelisted_users")
                    + f" {utils.PrintChat(chat=chat_settings.chat)}",
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildWhitelistedUsersList(
                            chat_settings=chat_settings, page=0
                        )
                    ),
                )
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["del", "delete"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.reply
    & pyrogram.Filters.group,
)
def CmdDel(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsJuniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        if msg.reply_to_message.from_user.id == client.ME.id:
            try:
                msg.reply_to_message.delete()
            except pyrogram.errors.MessageDeleteForbidden as ex:
                print(ex)
                traceback.print_exc()
                msg.reply_to_message.edit_text(text=".")
        else:
            try:
                msg.reply_to_message.delete()
            except pyrogram.errors.MessageDeleteForbidden as ex:
                print(ex)
                traceback.print_exc()
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(msg.chat.settings.language, "cant_delete_message"),
                )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=["delfrom", "deletefrom"], prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
    & pyrogram.Filters.group,
)
def CmdDelFrom(client: pyrogram.Client, msg: pyrogram.Message):
    # continue inside pre_process_post.py
    pass


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^logs PAGES[<<|\-|\+|>>]", flags=re.I)
)
def CbQryLogsPages(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
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
        query: peewee.ModelSelect = db_management.Logs.select().where(
            db_management.Logs.chat_id == chat_id
        ).order_by(db_management.Logs.timestamp.desc())

        if cb_qry.data.endswith("<<"):
            page = 0
        elif cb_qry.data.endswith("-"):
            page -= 1
        elif cb_qry.data.endswith("+"):
            page += 1
        elif cb_qry.data.endswith(">>"):
            page = -1
        page = keyboards.AdjustPage(
            page=page,
            max_n=len(query),
            max_items_page=utils.config["max_items_keyboard"],
        )
        begin = page * utils.config["max_items_keyboard"]
        end = min(len(query), (page + 1) * utils.config["max_items_keyboard"])
        query = query[begin:end]
        text = (
            _(chat_settings.language, "logs_of_X").format(
                utils.PrintChat(chat=chat_settings.chat)
            )
            + "\n"
        )
        for record in query:
            text += (
                f"\n<b>UTC {record.timestamp}</b> <i>#executer{record.executer}"
                + (
                    (
                        f" #targetchat{abs(record.target)}"
                        if record.target < 0
                        else f" #targetuser{abs(record.target)}"
                    )
                    if utils.IsInt(record.target)
                    else ""
                )
                + f"</i>: <code>{html.escape(record.action)}</code>"
            )
        cb_qry.message.edit_text(
            text=text,
            parse_mode="html",
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildLogMenu(chat_settings=chat_settings, page=page)
            ),
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(
            commands=["logs", "log"], del_=True, pvt=True
        ),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group,
)
def CmdLog(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsJuniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        utils.Log(
            client=client,
            chat_id=msg.chat.id,
            executer=msg.from_user.id,
            action=f"{msg.command[0]}",
            target=msg.chat.id,
        )
        query: peewee.ModelSelect = db_management.Logs.select().where(
            db_management.Logs.chat_id == msg.chat.id
        ).order_by(db_management.Logs.timestamp.desc())
        query = query[0 : utils.config["max_items_keyboard"]]
        text = (
            _(msg.chat.settings.language, "logs_of_X").format(
                html.escape(utils.PrintChat(chat=msg.chat))
            )
            + "\n"
        )
        for record in query:
            text += (
                f"\n<b>UTC {record.timestamp}</b> <i>#executer{record.executer}"
                + (
                    (
                        f" #targetchat{abs(record.target)}"
                        if record.target < 0
                        else f" #targetuser{abs(record.target)}"
                    )
                    if utils.IsInt(record.target)
                    else ""
                )
                + f"</i>: <code>{html.escape(record.action)}</code>"
            )
        if msg.command[0].lower().endswith("pvt"):
            methods.SendMessage(
                client=client,
                chat_id=msg.from_user.id,
                text=text,
                parse_mode="html",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildLogMenu(chat_settings=msg.chat.settings)
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
                text=text,
                parse_mode="html",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildLogMenu(chat_settings=msg.chat.settings)
                ),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["logs", "log"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private,
)
def CmdLogChat(client: pyrogram.Client, msg: pyrogram.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get_or_none(
            chat_id=chat_id
        )
        if chat_settings:
            if utils.IsJuniorModOrHigher(user_id=msg.from_user.id, chat_id=chat_id):
                utils.Log(
                    client=client,
                    chat_id=chat_id,
                    executer=msg.from_user.id,
                    action=f"{msg.command[0]}",
                    target=chat_id,
                )
                query: peewee.ModelSelect = db_management.Logs.select().where(
                    db_management.Logs.chat_id == chat_id
                ).order_by(db_management.Logs.timestamp.desc())
                query = query[0 : utils.config["max_items_keyboard"]]
                text = (
                    _(chat_settings.language, "logs_of_X").format(
                        html.escape(utils.PrintChat(chat=chat_settings.chat))
                    )
                    + "\n"
                )
                for record in query:
                    text += (
                        f"\n<b>UTC {record.timestamp}</b> <i>#executer{record.executer}"
                        + (
                            (
                                f" #targetchat{abs(record.target)}"
                                if record.target < 0
                                else f" #targetuser{abs(record.target)}"
                            )
                            if utils.IsInt(record.target)
                            else ""
                        )
                        + f"</i>: <code>{html.escape(record.action)}</code>"
                    )
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=text,
                    parse_mode="html",
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildLogMenu(chat_settings=chat_settings)
                    ),
                )
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(
            commands=["sendlogs", "sendlog"], del_=True, pvt=True
        ),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group,
)
def CmdSendLog(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsJuniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        utils.Log(
            client=client,
            chat_id=msg.chat.id,
            executer=msg.from_user.id,
            action=msg.text or msg.caption,
            target=msg.chat.id,
        )
        lower_bound = datetime.date.min
        higher_bound = datetime.date.max
        if len(msg.command) == 2:
            # specific date(s)
            # timestamp is a datetime, so between dayX at 00:00:00 and dayY + 1 at 00:00:00
            if ":" in msg.command[1]:
                # /sendlogs 2001-09-10:2001-09-12
                interval = msg.command[1].split(":")
                lower_bound = datetime.datetime.strptime(interval[0], "%Y-%m-%d")
                higher_bound = datetime.datetime.strptime(
                    interval[1], "%Y-%m-%d"
                ) + datetime.timedelta(days=1)
            else:
                # /sendlogs 2001-09-11
                lower_bound = datetime.datetime.strptime(msg.command[1], "%Y-%m-%d")
                higher_bound = lower_bound + datetime.timedelta(days=1)

        query: peewee.ModelSelect = (
            db_management.Logs.select()
            .where(
                (db_management.Logs.chat_id == msg.chat.id)
                & (db_management.Logs.timestamp.between(lower_bound, higher_bound))
            )
            .order_by(db_management.Logs.timestamp.desc())
        )

        text = (
            _(msg.chat.settings.language, "logs_of_X").format(
                html.escape(utils.PrintChat(chat=msg.chat))
            )
            + "\n</br>"
        )
        for record in query:
            text += (
                f"\n</br><b>UTC {record.timestamp}</b> <i>#executer{record.executer}"
                + (
                    (
                        f" #targetchat{abs(record.target)}"
                        if record.target < 0
                        else f" #targetuser{abs(record.target)}"
                    )
                    if utils.IsInt(record.target)
                    else ""
                )
                + f"</i>: <code>{html.escape(record.action)}</code>"
            )

        file_name = f"./downloads/logs_{msg.chat.id}_{lower_bound.date()}_{higher_bound.date()}.html"
        with open(file_name, "w", encoding="utf-8") as f:
            f.write('<meta charset="UTF-8">\n</br>')
            f.write(text)
        if msg.command[0].lower().endswith("pvt"):
            methods.SendDocument(
                client=client, chat_id=msg.from_user.id, document=file_name
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
            methods.ReplyDocument(client=client, msg=msg, document=file_name)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=["sendlogs", "sendlog"], prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.private,
)
def CmdSendLogChat(client: pyrogram.Client, msg: pyrogram.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get_or_none(
            chat_id=chat_id
        )
        if chat_settings:
            if utils.IsJuniorModOrHigher(user_id=msg.from_user.id, chat_id=chat_id):
                utils.Log(
                    client=client,
                    chat_id=chat_id,
                    executer=msg.from_user.id,
                    action=msg.text or msg.caption,
                    target=chat_id,
                )
                lower_bound = datetime.date.min
                higher_bound = datetime.date.max
                if len(msg.command) == 3:
                    # specific date(s)
                    # timestamp is a datetime, so between dayX at 00:00:00 and dayY + 1 at 00:00:00
                    if ":" in msg.command[2]:
                        # /sendlogs 2001-09-10:2001-09-12
                        interval = msg.command[2].split(":")
                        lower_bound = datetime.datetime.strptime(
                            interval[0], "%Y-%m-%d"
                        )
                        higher_bound = datetime.datetime.strptime(
                            interval[1], "%Y-%m-%d"
                        ) + datetime.timedelta(days=1)
                    else:
                        # /sendlogs 2001-09-11
                        lower_bound = datetime.datetime.strptime(
                            msg.command[2], "%Y-%m-%d"
                        )
                        higher_bound = lower_bound + datetime.timedelta(days=1)

                query: peewee.ModelSelect = (
                    db_management.Logs.select()
                    .where(
                        (db_management.Logs.chat_id == chat_id)
                        & (
                            db_management.Logs.timestamp.between(
                                lower_bound, higher_bound
                            )
                        )
                    )
                    .order_by(db_management.Logs.timestamp.desc())
                )

                text = (
                    _(chat_settings.language, "logs_of_X").format(
                        html.escape(utils.PrintChat(chat=chat_settings.chat))
                    )
                    + "\n</br>"
                )
                for record in query:
                    text += (
                        f"\n</br><b>UTC {record.timestamp}</b> <i>#executer{record.executer}"
                        + (
                            (
                                f" #targetchat{abs(record.target)}"
                                if record.target < 0
                                else f" #targetuser{abs(record.target)}"
                            )
                            if utils.IsInt(record.target)
                            else ""
                        )
                        + f"</i>: <code>{html.escape(record.action)}</code>"
                    )

                file_name = f"./downloads/logs_{msg.chat.id}_{lower_bound.date()}_{higher_bound.date()}.html"
                with open(file_name, "w", encoding="utf-8") as f:
                    f.write('<meta charset="UTF-8">\n</br>')
                    f.write(text)
                methods.ReplyDocument(client=client, msg=msg, document=file_name)
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )
