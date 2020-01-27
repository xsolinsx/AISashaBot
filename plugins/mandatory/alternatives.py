import re
import traceback

import peewee
import pyrogram

import db_management
import keyboards
import methods
import my_filters
import utils

_ = utils.GetLocalizedString


@pyrogram.Client.on_message(
    (pyrogram.Filters.text | pyrogram.Filters.media) & pyrogram.Filters.group, group=-6,
)
def TranslateAlternativeIntoCommand(client: pyrogram.Client, msg: pyrogram.Message):
    for element in msg.chat.settings.alternative_commands:
        if msg.media and element.is_media:
            media, type_ = utils.ExtractMedia(msg=msg)
            if media and hasattr(media, "file_id") and media.file_id:
                if element.alternative == media.file_id:
                    msg.text = f"/{element.original}"
                    if msg.caption:
                        msg.text += f"{msg.caption}"
        elif msg.text and not element.is_media:
            if element.alternative.lower() in msg.text.lower():
                msg.text = re.sub(
                    pattern=f"^{element.alternative}",
                    repl=f"/{element.original}",
                    string=msg.text,
                    count=1,
                    flags=re.I,
                )
    msg.continue_propagation()


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^\(i\)alternatives", flags=re.I)
)
def CbQryAlternativesInfo(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    text = ""

    query: peewee.ModelSelect = db_management.ChatAlternatives.select().where(
        db_management.ChatAlternatives.chat == chat_id
    ).order_by(
        peewee.fn.LOWER(db_management.ChatAlternatives.original),
        peewee.fn.LOWER(db_management.ChatAlternatives.alternative),
    )
    if utils.IsInt(cb_qry.data.replace("(i)alternatives ", "")) and int(
        cb_qry.data.replace("(i)alternatives ", "")
    ) < len(query):
        text = _(cb_qry.from_user.settings.language, "(i)alternatives").format(
            "/" + query[int(cb_qry.data.replace("(i)alternatives ", ""))].original
        )
    else:
        text = _(cb_qry.from_user.settings.language, "error_try_again")

    methods.CallbackQueryAnswer(
        cb_qry=cb_qry, text=text, show_alert=True,
    )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^alternatives get (\d+)", flags=re.I)
)
def CbQryAlternativesGet(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsJuniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        index = int(cb_qry.data.replace("alternatives get ", ""))
        query: peewee.ModelSelect = chat_settings.alternative_commands.order_by(
            peewee.fn.LOWER(db_management.ChatAlternatives.original),
            peewee.fn.LOWER(db_management.ChatAlternatives.alternative),
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
                        cb_qry.message.reply_cached_media(file_id=element.alternative)
                    except pyrogram.errors.FilerefUpgradeNeeded:
                        try:
                            original_media_message: pyrogram.Message = client.get_messages(
                                chat_id=element.original_chat_id,
                                message_id=element.original_message_id,
                            )
                            type_, media = utils.ExtractMedia(
                                msg=original_media_message
                            )
                            if media and hasattr(media, "file_ref") and media.file_ref:
                                cb_qry.message.reply_cached_media(
                                    file_id=element.alternative, file_ref=media.file_ref
                                )
                            else:
                                element.delete_instance()
                                methods.ReplyText(
                                    client=client,
                                    msg=cb_qry.message,
                                    text=_(
                                        cb_qry.message.chat.settings.language,
                                        "original_alternative_deleted",
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
                if element.alternative is not None:
                    methods.ReplyText(
                        client=client, msg=cb_qry.message, text=element.alternative
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
    my_filters.callback_regex(pattern=r"^alternatives PAGES[<<|\-|\+|>>]", flags=re.I)
)
def CbQryAlternativesPages(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
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
                    keyboards.BuildAlternativeCommandsList(
                        chat_settings=chat_settings, page=0
                    )
                )
            )
        elif cb_qry.data.endswith("-"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildAlternativeCommandsList(
                        chat_settings=chat_settings, page=page - 1
                    )
                )
            )
        elif cb_qry.data.endswith("+"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildAlternativeCommandsList(
                        chat_settings=chat_settings, page=page + 1
                    )
                )
            )
        elif cb_qry.data.endswith(">>"):
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildAlternativeCommandsList(
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
    my_filters.callback_regex(pattern=r"^alternatives set", flags=re.I)
)
def CbQryAlternativesSet(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
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
        text = ""
        if cb_qry.data == "alternatives set":
            utils.tmp_steps[cb_qry.message.chat.id] = (cb_qry, cb_qry.data)
            text = _(cb_qry.from_user.settings.language, "send_original_command")

        cb_qry.message.edit_text(
            text=f"{utils.PrintChat(chat=db_management.Chats.get(id=chat_id))}\n"
            + text,
            reply_markup=pyrogram.InlineKeyboardMarkup(
                [
                    [
                        pyrogram.InlineKeyboardButton(
                            text=_(cb_qry.from_user.settings.language, "cancel"),
                            callback_data=f"cancel alternatives {chat_id}",
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
    my_filters.callback_regex(pattern=r"^alternatives unset", flags=re.I)
)
def CbQryAlternativesUnset(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    page = int(parameters[2])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsSeniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        index = int(cb_qry.data.replace("alternatives unset ", ""))
        query: peewee.ModelSelect = chat_settings.alternative_commands.order_by(
            peewee.fn.LOWER(db_management.ChatAlternatives.original),
            peewee.fn.LOWER(db_management.ChatAlternatives.alternative),
        )
        element = query[index] if index < len(query) else None
        if element:
            element.delete_instance()
            utils.Log(
                client=client,
                chat_id=chat_id,
                executer=cb_qry.from_user.id,
                action=f"{cb_qry.data} {element.original} {element.alternative}",
                target=chat_id,
            )
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "success"),
                show_alert=False,
            )
            cb_qry.message.edit_reply_markup(
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildAlternativeCommandsList(
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
    my_filters.callback_regex(pattern=r"^alternatives (\-\d+) (\d+)", flags=re.I)
)
def CbQryAlternatives(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = cb_qry.data.split(" ")
    chat_id = int(parameters[1])
    page = int(parameters[2])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsJuniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        cb_qry.message.edit_text(
            text=_(cb_qry.message.chat.settings.language, "alternatives")
            + f" {utils.PrintChat(chat=chat_settings.chat)}",
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildAlternativeCommandsList(
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
        commands=utils.GetCommandsVariants(commands=["alternatives"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group
)
def CmdAlternatives(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsJuniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "alternatives")
            + f" {utils.PrintChat(chat=msg.chat)}",
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildAlternativeCommandsList(
                    chat_settings=msg.chat.settings, page=0
                )
            ),
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["alternatives"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdAlternativesChat(client: pyrogram.Client, msg: pyrogram.Message):
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
                    text=_(chat_settings.language, "alternatives")
                    + f" {utils.PrintChat(chat=chat_settings.chat)}",
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildAlternativeCommandsList(
                            chat_settings=chat_settings, page=0
                        )
                    ),
                )
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "no_chat_settings"),
            )
