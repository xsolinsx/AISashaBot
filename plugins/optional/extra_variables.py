# getsetunset
import re

import peewee
import pyrogram

import db_management
import keyboards
import methods
import utils

_ = utils.GetLocalizedString


@pyrogram.Client.on_message(
    (pyrogram.filters.text | pyrogram.filters.caption) & pyrogram.filters.group,
    group=-3,
)
def SendExtra(client: pyrogram.Client, msg: pyrogram.types.Message):
    r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
        plugin="extra_variables", chat=msg.chat.id
    )
    if (
        r_chat_plugin.min_rank <= msg.r_user_chat.rank
        and r_chat_plugin.is_enabled_on_chat
    ):
        if msg.chat.settings.extras:
            text_to_use = ""
            if msg.text:
                text_to_use += f" {msg.text}"
            if msg.caption:
                text_to_use += f" {msg.caption}"
            text_to_use = text_to_use.strip()
            for element in msg.chat.settings.extras.order_by(
                peewee.fn.LOWER(db_management.ChatExtras.key)
            ).where(~db_management.ChatExtras.is_group_data):
                found = False
                if element.is_regex:
                    regex_check_item = re.compile(element.key, re.I | re.M)
                    found = regex_check_item.search(text_to_use)
                else:
                    found = element.key.lower() in text_to_use.lower()

                if found:
                    if element.is_media:
                        value = element.value.split("$")
                        media_id = value[0][3:]  # skip ###
                        caption = ""
                        if len(value) > 1:
                            # join over $ because they could have been removed with the previous split
                            caption = "$".join(value[1:])
                            caption = utils.AdjustMarkers(value=caption, msg=msg)
                        try:
                            msg.reply_cached_media(
                                file_id=media_id, caption=caption, parse_mode="html",
                            )
                        except pyrogram.errors.FilerefUpgradeNeeded:
                            original_media_message: pyrogram.types.Message = client.get_messages(
                                chat_id=element.original_chat_id,
                                message_id=element.original_message_id,
                            )
                            type_, media = utils.ExtractMedia(
                                msg=original_media_message
                            )
                            if media:
                                msg.reply_cached_media(
                                    file_id=media_id,
                                    caption=caption,
                                    parse_mode="html",
                                )
                            else:
                                element.delete_instance()
                                methods.ReplyText(
                                    client=client,
                                    msg=msg,
                                    text=_(
                                        msg.chat.settings.language,
                                        "original_extra_deleted",
                                    ),
                                )
                    else:
                        text = utils.AdjustMarkers(value=element.value, msg=msg)
                        if text is not None:
                            methods.ReplyText(
                                client=client,
                                msg=msg,
                                text=utils.AdjustMarkers(value=element.value, msg=msg),
                                parse_mode="html",
                            )
                    break
    msg.continue_propagation()


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^\(i\)extras", flags=re.I)
)
def CbQryExtrasInfo(client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    text = ""

    query: peewee.ModelSelect = db_management.ChatExtras.select().where(
        (db_management.ChatExtras.chat == chat_id)
        & (~db_management.ChatExtras.is_group_data)
    ).order_by(peewee.fn.LOWER(db_management.ChatExtras.key))
    if utils.IsInt(cb_qry.data.replace("(i)extras ", "")) and int(
        cb_qry.data.replace("(i)extras ", "")
    ) < len(query):
        text = _(cb_qry.from_user.settings.language, "(i)extras").format(
            query[int(cb_qry.data.replace("(i)extras ", ""))].key
        )
    else:
        text = _(cb_qry.from_user.settings.language, "error_try_again")

    methods.CallbackQueryAnswer(
        cb_qry=cb_qry, text=text, show_alert=True,
    )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^extras replace (\d+)", flags=re.I)
)
def CbQryExtrasReplace(client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    if chat_id < 0:
        r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
            plugin="extra_variables", chat=chat_id
        )
    if (
        r_chat_plugin.min_rank
        <= utils.GetRank(user_id=cb_qry.from_user.id, chat_id=chat_id)
        and r_chat_plugin.is_enabled_on_chat
    ):
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
            chat_id=chat_id
        )
        if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
            index = int(cb_qry.data.replace("extras replace ", ""))
            query: peewee.ModelSelect = chat_settings.extras.order_by(
                peewee.fn.LOWER(db_management.ChatExtras.key)
            ).where(~db_management.ChatExtras.is_group_data)
            element = query[index] if index < len(query) else None
            if element:
                utils.tmp_steps[cb_qry.message.chat.id] = (
                    cb_qry,
                    "extras set "
                    + ("regex" if element.is_regex else "text")
                    + " "
                    + ("media" if element.is_media else "text")
                    + f" {element.key}",
                )
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "send_extra_value"),
                    show_alert=False,
                )

                cb_qry.message.edit_text(
                    text=_(cb_qry.from_user.settings.language, "send_extra_value"),
                    reply_markup=pyrogram.types.InlineKeyboardMarkup(
                        [
                            [
                                pyrogram.types.InlineKeyboardButton(
                                    text=_(
                                        cb_qry.from_user.settings.language, "cancel"
                                    ),
                                    callback_data=f"cancel extras {chat_id}",
                                )
                            ]
                        ]
                    ),
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
    pyrogram.filters.regex(pattern=r"^extras get (\d+)", flags=re.I)
)
def CbQryExtrasGet(client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    if chat_id < 0:
        r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
            plugin="extra_variables", chat=chat_id
        )
    if (
        r_chat_plugin.min_rank
        <= utils.GetRank(user_id=cb_qry.from_user.id, chat_id=chat_id)
        and r_chat_plugin.is_enabled_on_chat
    ):
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
            chat_id=chat_id
        )
        if utils.IsJuniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
            index = int(cb_qry.data.replace("extras get ", ""))
            query: peewee.ModelSelect = chat_settings.extras.order_by(
                peewee.fn.LOWER(db_management.ChatExtras.key)
            ).where(~db_management.ChatExtras.is_group_data)
            element = query[index] if index < len(query) else None
            if element:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "ok"),
                    show_alert=False,
                )
                if element.is_media:
                    value = element.value.split("$")
                    media_id = value[0][3:]  # skip ###
                    caption = ""
                    if len(value) > 1:
                        # join over $ because they could have been removed with the previous split
                        caption = "$".join(value[1:])

                    try:
                        cb_qry.message.reply_cached_media(
                            file_id=media_id, caption=caption, parse_mode="html",
                        )
                    except pyrogram.errors.FilerefUpgradeNeeded:
                        original_media_message: pyrogram.types.Message = client.get_messages(
                            chat_id=element.original_chat_id,
                            message_id=element.original_message_id,
                        )
                        type_, media = utils.ExtractMedia(msg=original_media_message)
                        if media:
                            cb_qry.message.reply_cached_media(
                                file_id=media_id, caption=caption, parse_mode="html",
                            )
                        else:
                            element.delete_instance()
                            methods.ReplyText(
                                client=client,
                                msg=cb_qry.message,
                                text=_(
                                    cb_qry.message.chat.settings.language,
                                    "original_extra_deleted",
                                ),
                            )
                else:
                    if element.value is not None:
                        methods.ReplyText(
                            client=client,
                            msg=cb_qry.message,
                            text=element.value,
                            parse_mode="html",
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
    pyrogram.filters.regex(pattern=r"^extras PAGES[<<|\-|\+|>>]", flags=re.I)
)
def CbQryExtrasPages(client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    if chat_id < 0:
        r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
            plugin="extra_variables", chat=chat_id
        )
    if (
        r_chat_plugin.min_rank
        <= utils.GetRank(user_id=cb_qry.from_user.id, chat_id=chat_id)
        and r_chat_plugin.is_enabled_on_chat
    ):
        page = int(parameters[2])
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
            chat_id=chat_id
        )
        if utils.IsJuniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "turning_page"),
            )
            if cb_qry.data.endswith("<<"):
                cb_qry.message.edit_reply_markup(
                    reply_markup=pyrogram.types.InlineKeyboardMarkup(
                        keyboards.BuildExtraList(chat_settings=chat_settings, page=0)
                    )
                )
            elif cb_qry.data.endswith("-"):
                cb_qry.message.edit_reply_markup(
                    reply_markup=pyrogram.types.InlineKeyboardMarkup(
                        keyboards.BuildExtraList(
                            chat_settings=chat_settings, page=page - 1
                        )
                    )
                )
            elif cb_qry.data.endswith("+"):
                cb_qry.message.edit_reply_markup(
                    reply_markup=pyrogram.types.InlineKeyboardMarkup(
                        keyboards.BuildExtraList(
                            chat_settings=chat_settings, page=page + 1
                        )
                    )
                )
            elif cb_qry.data.endswith(">>"):
                cb_qry.message.edit_reply_markup(
                    reply_markup=pyrogram.types.InlineKeyboardMarkup(
                        keyboards.BuildExtraList(chat_settings=chat_settings, page=-1)
                    )
                )
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
                show_alert=True,
            )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^extras set", flags=re.I)
)
def CbQryExtrasSet(client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    if chat_id < 0:
        r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
            plugin="extra_variables", chat=chat_id
        )
    if (
        r_chat_plugin.min_rank
        <= utils.GetRank(user_id=cb_qry.from_user.id, chat_id=chat_id)
        and r_chat_plugin.is_enabled_on_chat
    ):
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
            chat_id=chat_id
        )
        if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "ok"),
                show_alert=False,
            )
            if cb_qry.data == "extras set":
                cb_qry.message.edit_text(
                    text=_(cb_qry.from_user.settings.language, "select_type_of_extra"),
                    reply_markup=pyrogram.types.InlineKeyboardMarkup(
                        keyboards.BuildExtraList(
                            chat_settings=chat_settings, selected_setting="set"
                        )
                    ),
                    parse_mode="html",
                )
                return
            elif cb_qry.data.startswith("extras set text") or cb_qry.data.startswith(
                "extras set regex"
            ):
                utils.tmp_steps[cb_qry.message.chat.id] = (cb_qry, cb_qry.data)
                cb_qry.message.edit_text(
                    text=_(cb_qry.from_user.settings.language, "send_extra_key"),
                    reply_markup=pyrogram.types.InlineKeyboardMarkup(
                        [
                            [
                                pyrogram.types.InlineKeyboardButton(
                                    text=_(
                                        cb_qry.from_user.settings.language, "cancel"
                                    ),
                                    callback_data=f"cancel extras {chat_id}",
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
    pyrogram.filters.regex(pattern=r"^extras unset", flags=re.I)
)
def CbQryExtrasUnset(client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    if chat_id < 0:
        r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
            plugin="extra_variables", chat=chat_id
        )
    if (
        r_chat_plugin.min_rank
        <= utils.GetRank(user_id=cb_qry.from_user.id, chat_id=chat_id)
        and r_chat_plugin.is_enabled_on_chat
    ):
        page = int(parameters[2])
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
            chat_id=chat_id
        )
        if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
            index = int(cb_qry.data.replace("extras unset ", ""))
            query: peewee.ModelSelect = chat_settings.extras.order_by(
                peewee.fn.LOWER(db_management.ChatExtras.key)
            ).where(~db_management.ChatExtras.is_group_data)
            element = query[index] if index < len(query) else None
            if element:
                extra = element.key
                element.delete_instance()
                utils.Log(
                    client=client,
                    chat_id=chat_id,
                    executer=cb_qry.from_user.id,
                    action=f"{cb_qry.data} {extra}",
                    target=chat_id,
                )
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "success"),
                    show_alert=False,
                )
                cb_qry.message.edit_reply_markup(
                    reply_markup=pyrogram.types.InlineKeyboardMarkup(
                        keyboards.BuildExtraList(chat_settings=chat_settings, page=page)
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


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["extras"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
def CmdExtras(client: pyrogram.Client, msg: pyrogram.types.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
            plugin="extra_variables", chat=msg.chat.id
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    if allowed:
        if utils.IsJuniorModOrHigher(
            user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
        ):
            if msg.command[0].lower().endswith("pvt"):
                methods.SendMessage(
                    client=client,
                    chat_id=msg.from_user.id,
                    text=_(msg.chat.settings.language, "extras")
                    + f" {utils.PrintChat(chat=msg.chat)}",
                    reply_markup=pyrogram.types.InlineKeyboardMarkup(
                        keyboards.BuildExtraList(
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
                    text=_(msg.chat.settings.language, "extras")
                    + f" {utils.PrintChat(chat=msg.chat)}",
                    reply_markup=pyrogram.types.InlineKeyboardMarkup(
                        keyboards.BuildExtraList(
                            chat_settings=msg.chat.settings, page=0
                        )
                    ),
                )


@pyrogram.Client.on_message(
    pyrogram.filters.command(commands=["extras"], prefixes=["/", "!", "#", "."],)
    & pyrogram.filters.private
)
def CmdExtrasChat(client: pyrogram.Client, msg: pyrogram.types.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get_or_none(
            chat_id=chat_id
        )
        if chat_settings:
            r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
                plugin="extra_variables", chat=chat_id
            )
            if (
                r_chat_plugin.min_rank <= msg.r_user_chat.rank
                and r_chat_plugin.is_enabled_on_chat
            ):
                if utils.IsJuniorModOrHigher(user_id=msg.from_user.id, chat_id=chat_id):
                    methods.ReplyText(
                        client=client,
                        msg=msg,
                        text=_(chat_settings.language, "extras")
                        + f" {utils.PrintChat(chat=chat_settings.chat)}",
                        reply_markup=pyrogram.types.InlineKeyboardMarkup(
                            keyboards.BuildExtraList(
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
