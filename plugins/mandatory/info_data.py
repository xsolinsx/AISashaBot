import datetime
import re
import time
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


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^\(i\)info (.+)", flags=re.I)
)
def CbQryInfoInfo(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    regex_setting_time_punishment_keyboard = re.compile(
        r"^\(i\)info (max_temp_restrict|max_temp_ban) (weeks|days|hours|minutes|seconds)",
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
    my_filters.callback_regex(pattern=r"^maininfo (.+)", flags=re.I)
)
def CbQryInfoMenu(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    parameters = []
    if len(cb_qry.data.split(" ")) > 1 and utils.IsInt(cb_qry.data.split(" ")[1]):
        parameters = cb_qry.data.split(" ")
    else:
        parameters = cb_qry.message.reply_markup.inline_keyboard[0][
            0
        ].callback_data.split(" ")
    chat_id = int(parameters[1])
    target_id = int(parameters[2]) if len(parameters) > 2 else chat_id
    chat_settings = None
    r_target_chat = None
    r_executer_chat = None
    if chat_id < 0:
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
            chat_id=chat_id
        )
        r_target_chat: db_management.RUserChat = db_management.RUserChat.get_or_none(
            user_id=target_id, chat_id=chat_id
        )
        r_executer_chat = db_management.RUserChat.get_or_none(
            user_id=cb_qry.from_user.id, chat_id=chat_id
        )
        if not r_executer_chat:
            r_executer_chat = db_management.RUserChat.create(
                user_id=cb_qry.from_user.id, chat_id=chat_id
            )
    else:
        chat_settings: db_management.UserSettings = db_management.UserSettings.get(
            user_id=chat_id
        )

    if cb_qry.message.chat.type != "private" and not utils.IsJuniorModOrHigher(
        user_id=cb_qry.from_user.id, chat_id=chat_id, r_user_chat=r_executer_chat
    ):
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "updating"),
            show_alert=False,
        )

        cb_qry.message.edit_text(
            text=methods.Info(
                client=client,
                target=target_id,
                chat_id=chat_id,
                chat_settings=chat_settings,
                r_target_chat=r_target_chat,
            ),
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildInfoMenu(
                    target=target_id,
                    chat_id=chat_id,
                    current_keyboard="maininfo",
                    chat_settings=chat_settings,
                    r_target_chat=r_target_chat,
                )
            ),
            parse_mode="html",
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^info (.+)", flags=re.I)
)
def CbQryInfoChange(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    regex_info_select_value = re.compile(r"^info (.+) selectvalue(\d)", re.I)
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )

    target_id = int(parameters[1])
    chat_id = int(parameters[2]) if len(parameters) > 2 else target_id

    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get_or_none(
        chat_id=chat_id
    )

    r_executer_chat = db_management.RUserChat.get_or_none(
        user_id=cb_qry.from_user.id, chat_id=chat_id
    )
    if not r_executer_chat:
        r_executer_chat = db_management.RUserChat.create(
            user_id=cb_qry.from_user.id, chat_id=chat_id
        )
    r_target_chat: db_management.RUserChat = db_management.RUserChat.get_or_none(
        user_id=target_id, chat_id=chat_id
    )
    setting = None
    text = ""

    if cb_qry.data == "info privileged_user":
        if utils.CompareRanks(
            executer=cb_qry.from_user.id,
            target=target_id,
            chat_id=chat_id,
            r_executer_chat=r_executer_chat,
            r_target_chat=r_target_chat,
            min_rank=dictionaries.RANKS["senior_mod"],
        ):
            r_target_chat.rank = (
                dictionaries.RANKS["privileged_user"]
                if r_target_chat.rank != dictionaries.RANKS["privileged_user"]
                else 0
            )
            try:
                r_target_chat.save()
            except Exception as ex:
                print(ex)
                traceback.print_exc()
                text += f"\n{ex}"
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "error_try_again"),
                )
            else:
                utils.Log(
                    client=client,
                    chat_id=chat_id,
                    executer=cb_qry.from_user.id,
                    action=f"{cb_qry.data} = {r_target_chat.rank}",
                    target=target_id,
                )
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry, text=_(cb_qry.from_user.settings.language, "ok")
                )
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
                show_alert=True,
            )
    elif cb_qry.data == "info junior_mod":
        if utils.CompareRanks(
            executer=cb_qry.from_user.id,
            target=target_id,
            chat_id=chat_id,
            r_executer_chat=r_executer_chat,
            r_target_chat=r_target_chat,
            min_rank=dictionaries.RANKS["senior_mod"],
        ):
            r_target_chat.rank = (
                dictionaries.RANKS["junior_mod"]
                if r_target_chat.rank != dictionaries.RANKS["junior_mod"]
                else 0
            )
            try:
                r_target_chat.save()
            except Exception as ex:
                print(ex)
                traceback.print_exc()
                text += f"\n{ex}"
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "error_try_again"),
                )
            else:
                utils.Log(
                    client=client,
                    chat_id=chat_id,
                    executer=cb_qry.from_user.id,
                    action=f"{cb_qry.data} = {r_target_chat.rank}",
                    target=target_id,
                )
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry, text=_(cb_qry.from_user.settings.language, "ok")
                )
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
                show_alert=True,
            )
    elif cb_qry.data == "info senior_mod":
        if utils.CompareRanks(
            executer=cb_qry.from_user.id,
            target=target_id,
            chat_id=chat_id,
            r_executer_chat=r_executer_chat,
            r_target_chat=r_target_chat,
            min_rank=dictionaries.RANKS["owner"],
        ):
            r_target_chat.rank = (
                dictionaries.RANKS["senior_mod"]
                if r_target_chat.rank != dictionaries.RANKS["senior_mod"]
                else 0
            )
            try:
                r_target_chat.save()
            except Exception as ex:
                print(ex)
                traceback.print_exc()
                text += f"\n{ex}"
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "error_try_again"),
                )
            else:
                utils.Log(
                    client=client,
                    chat_id=chat_id,
                    executer=cb_qry.from_user.id,
                    action=f"{cb_qry.data} = {r_target_chat.rank}",
                    target=target_id,
                )
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry, text=_(cb_qry.from_user.settings.language, "ok")
                )
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
                show_alert=True,
            )
    elif cb_qry.data == "info whitelisted":
        if (
            utils.IsSeniorModOrHigher(
                user_id=cb_qry.from_user.id,
                chat_id=chat_id,
                r_user_chat=r_executer_chat,
            )
            and utils.GetRank(
                user_id=target_id, chat_id=chat_id, r_user_chat=r_target_chat
            )
            < dictionaries.RANKS["junior_mod"]
        ):
            r_target_chat.is_whitelisted = not r_target_chat.is_whitelisted
            try:
                r_target_chat.save()
            except Exception as ex:
                print(ex)
                traceback.print_exc()
                text += f"\n{ex}"
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "error_try_again"),
                )
            else:
                utils.Log(
                    client=client,
                    chat_id=chat_id,
                    executer=cb_qry.from_user.id,
                    action=f"{cb_qry.data} = {r_target_chat.is_whitelisted}",
                    target=target_id,
                )
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry, text=_(cb_qry.from_user.settings.language, "ok")
                )
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
                show_alert=True,
            )
    elif cb_qry.data == "info global_ban_whitelisted":
        if utils.IsSeniorModOrHigher(
            user_id=cb_qry.from_user.id, chat_id=chat_id, r_user_chat=r_executer_chat
        ):
            r_target_chat.is_global_ban_whitelisted = (
                not r_target_chat.is_global_ban_whitelisted
            )
            try:
                r_target_chat.save()
            except Exception as ex:
                print(ex)
                traceback.print_exc()
                text += f"\n{ex}"
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "error_try_again"),
                )
            else:
                utils.Log(
                    client=client,
                    chat_id=chat_id,
                    executer=cb_qry.from_user.id,
                    action=f"{cb_qry.data} = {r_target_chat.is_global_ban_whitelisted}",
                    target=target_id,
                )
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry, text=_(cb_qry.from_user.settings.language, "ok")
                )
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
                show_alert=True,
            )
    elif "warns" in cb_qry.data:
        if utils.CompareRanks(
            executer=cb_qry.from_user.id,
            target=target_id,
            chat_id=chat_id,
            r_executer_chat=r_executer_chat,
            r_target_chat=r_target_chat,
            min_rank=dictionaries.RANKS["junior_mod"],
        ):
            if "--" in cb_qry.data:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=methods.Unwarn(
                        client=client,
                        executer=cb_qry.from_user.id,
                        target=target_id,
                        chat_id=chat_id,
                        r_executer_chat=r_executer_chat,
                        r_target_chat=r_target_chat,
                        chat_settings=chat_settings,
                    ),
                    show_alert=True,
                )
            elif "++" in cb_qry.data:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=methods.Warn(
                        client=client,
                        executer=cb_qry.from_user.id,
                        target=target_id,
                        chat_id=chat_id,
                        r_executer_chat=r_executer_chat,
                        r_target_chat=r_target_chat,
                        chat_settings=chat_settings,
                    ),
                    show_alert=True,
                )
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
                show_alert=True,
            )
    elif "punishments" in cb_qry.data:
        if utils.CompareRanks(
            executer=cb_qry.from_user.id,
            target=target_id,
            chat_id=chat_id,
            r_executer_chat=r_executer_chat,
            r_target_chat=r_target_chat,
            min_rank=dictionaries.RANKS["junior_mod"],
        ):
            if "selectvalue" in cb_qry.data:
                punishment = int(regex_info_select_value.match(cb_qry.data)[2])
                hashtag = dictionaries.PUNISHMENT_STRING.get(punishment, "")
                until_date = None
                if punishment == 3:
                    methods.Kick(
                        client=client,
                        executer=cb_qry.from_user.id,
                        target=target_id,
                        chat_id=chat_id,
                    )
                elif punishment == 4:
                    until_date = int(time.time() + chat_settings.max_temp_restrict)
                    methods.Restrict(
                        client=client,
                        executer=cb_qry.from_user.id,
                        target=target_id,
                        chat_id=chat_id,
                        until_date=until_date,
                    )
                elif punishment == 5:
                    methods.Restrict(
                        client=client,
                        executer=cb_qry.from_user.id,
                        target=target_id,
                        chat_id=chat_id,
                    )
                elif punishment == 6:
                    until_date = int(time.time() + chat_settings.max_temp_ban)
                    methods.Ban(
                        client=client,
                        executer=cb_qry.from_user.id,
                        target=target_id,
                        chat_id=chat_id,
                        until_date=until_date,
                    )
                elif punishment == 7:
                    methods.Ban(
                        client=client,
                        executer=cb_qry.from_user.id,
                        target=target_id,
                        chat_id=chat_id,
                    )
                else:
                    punishment = None

                if punishment is None:
                    methods.CallbackQueryAnswer(
                        cb_qry=cb_qry,
                        text=_(cb_qry.from_user.settings.language, "error_try_again"),
                        show_alert=True,
                    )
                else:
                    if until_date:
                        hashtag += (
                            " "
                            + _(chat_settings.language, "until")
                            + f" UTC {datetime.datetime.utcfromtimestamp(until_date)}"
                        )

                    methods.CallbackQueryAnswer(
                        cb_qry=cb_qry,
                        text=_(
                            cb_qry.from_user.settings.language, "action_on_user"
                        ).format(
                            f"#{hashtag}",
                            target_id,
                            "",
                            cb_qry.from_user.id,
                            abs(chat_id),
                        ),
                        show_alert=True,
                    )
            else:
                setting = "punishments"
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "select_value"),
                    show_alert=False,
                )
        else:
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry,
                text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
                show_alert=True,
            )

    text = (
        methods.Info(
            client=client,
            target=target_id,
            chat_id=chat_id,
            chat_settings=chat_settings,
            r_target_chat=r_target_chat,
        )
        + text
    )

    cb_qry.message.edit_text(
        text=text,
        reply_markup=pyrogram.InlineKeyboardMarkup(
            keyboards.BuildInfoMenu(
                target=target_id,
                chat_id=chat_id,
                current_keyboard="maininfo",
                chat_settings=chat_settings,
                r_target_chat=r_target_chat,
                selected_setting=setting,
            )
        ),
        parse_mode="html",
    )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(
            commands=["info", "promote", "demote"], del_=True, pvt=True
        ),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdInfo(client: pyrogram.Client, msg: pyrogram.Message):
    chat_id = None
    target_id = None
    if len(msg.command) == 3 and msg.chat.type == "private":
        chat_id = utils.ResolveCommandToId(client=client, msg=msg, value=msg.command[1])
        target_id = utils.ResolveCommandToId(
            client=client, msg=msg, value=msg.command[2]
        )
    elif len(msg.command) == 2:
        chat_id = msg.chat.id
        target_id = utils.ResolveCommandToId(
            client=client, msg=msg, value=msg.command[1]
        )
    elif len(msg.command) == 1:
        chat_id = msg.chat.id
        if msg.reply_to_message:
            target_id = msg.reply_to_message.from_user.id
        else:
            target_id = chat_id

    if chat_id < 0:
        # chat
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get_or_none(
            chat_id=chat_id
        )
    else:
        # user
        chat_settings: db_management.UserSettings = db_management.UserSettings.get_or_none(
            user_id=chat_id
        )
    if chat_settings:
        if utils.IsJuniorModOrHigher(user_id=msg.from_user.id, chat_id=chat_id):
            if isinstance(chat_id, str) or isinstance(target_id, str):
                if isinstance(chat_id, str):
                    methods.ReplyText(client=client, msg=msg, text=chat_id)
                if isinstance(target_id, str):
                    methods.ReplyText(client=client, msg=msg, text=target_id)
            else:
                if target_id < 0:
                    # chat
                    text = None
                    if not db_management.Chats.get_or_none(id=target_id):
                        try:
                            chat = client.get_chat(chat_id=target_id)
                            chat = db_management.DBObject(obj=chat, client=client)
                        except pyrogram.errors.FloodWait as ex:
                            print(ex)
                            traceback.print_exc()
                            text = _(chat_settings.language, "tg_flood_wait_X").format(
                                ex.x
                            )
                        except pyrogram.errors.RPCError as ex:
                            print(ex)
                            traceback.print_exc()
                            text = _(chat_settings.language, "tg_error_X").format(ex)

                    if msg.command[0].lower().endswith("pvt"):
                        methods.SendMessage(
                            client=client,
                            chat_id=msg.from_user.id,
                            text=text
                            or methods.Info(
                                client=client,
                                target=target_id,
                                chat_id=chat_id,
                                chat_settings=chat_settings,
                            ),
                            reply_markup=pyrogram.InlineKeyboardMarkup(
                                keyboards.BuildInfoMenu(
                                    target=target_id,
                                    chat_id=chat_id,
                                    current_keyboard="maininfo",
                                    chat_settings=chat_settings,
                                )
                            )
                            if not text
                            else None,
                            parse_mode="html",
                        )
                        methods.ReplyText(
                            client=client,
                            msg=msg,
                            text=_(
                                msg.from_user.settings.language, "sent_to_pvt"
                            ).format(client.ME.id),
                            parse_mode="html",
                        )
                    else:
                        methods.ReplyText(
                            client=client,
                            msg=msg,
                            text=text
                            or methods.Info(
                                client=client,
                                target=target_id,
                                chat_id=chat_id,
                                chat_settings=chat_settings,
                            ),
                            reply_markup=pyrogram.InlineKeyboardMarkup(
                                keyboards.BuildInfoMenu(
                                    target=target_id,
                                    chat_id=chat_id,
                                    current_keyboard="maininfo",
                                    chat_settings=chat_settings,
                                )
                            )
                            if not text
                            else None,
                            parse_mode="html",
                        )
                else:
                    if chat_id < 0:
                        # info of target in chat_id
                        text = None
                        try:
                            if not db_management.Users.get_or_none(id=target_id):
                                chat = client.get_chat(chat_id=target_id)
                                chat = db_management.DBObject(obj=chat, client=client)
                            if not db_management.Chats.get_or_none(id=chat_id):
                                chat = client.get_chat(chat_id=chat_id)
                                chat = db_management.DBObject(obj=chat, client=client)
                        except pyrogram.errors.FloodWait as ex:
                            print(ex)
                            traceback.print_exc()
                            text = _(chat_settings.language, "tg_flood_wait_X").format(
                                ex.x
                            )
                        except pyrogram.errors.RPCError as ex:
                            print(ex)
                            traceback.print_exc()
                            text = _(chat_settings.language, "tg_error_X").format(ex)

                        r_target_chat: db_management.RUserChat = db_management.RUserChat.get_or_none(
                            user_id=target_id, chat_id=chat_id
                        )
                        if not r_target_chat:
                            r_target_chat = db_management.RUserChat.create(
                                user_id=target_id, chat_id=chat_id
                            )
                        if r_target_chat:
                            if msg.command[0].lower().endswith("pvt"):
                                methods.SendMessage(
                                    client=client,
                                    chat_id=msg.from_user.id,
                                    text=text
                                    or methods.Info(
                                        client=client,
                                        target=target_id,
                                        chat_id=chat_id,
                                        chat_settings=chat_settings,
                                        r_target_chat=r_target_chat,
                                    ),
                                    reply_markup=pyrogram.InlineKeyboardMarkup(
                                        keyboards.BuildInfoMenu(
                                            target=target_id,
                                            chat_id=chat_id,
                                            current_keyboard="maininfo",
                                            chat_settings=chat_settings,
                                            r_target_chat=r_target_chat,
                                        )
                                    )
                                    if not text
                                    else None,
                                    parse_mode="html",
                                )
                                methods.ReplyText(
                                    client=client,
                                    msg=msg,
                                    text=_(
                                        msg.from_user.settings.language, "sent_to_pvt"
                                    ).format(client.ME.id),
                                    parse_mode="html",
                                )
                            else:
                                methods.ReplyText(
                                    client=client,
                                    msg=msg,
                                    text=text
                                    or methods.Info(
                                        client=client,
                                        target=target_id,
                                        chat_id=chat_id,
                                        chat_settings=chat_settings,
                                        r_target_chat=r_target_chat,
                                    ),
                                    reply_markup=pyrogram.InlineKeyboardMarkup(
                                        keyboards.BuildInfoMenu(
                                            target=target_id,
                                            chat_id=chat_id,
                                            current_keyboard="maininfo",
                                            chat_settings=chat_settings,
                                            r_target_chat=r_target_chat,
                                        )
                                    )
                                    if not text
                                    else None,
                                    parse_mode="html",
                                )
                    else:
                        # user
                        text = None
                        if not db_management.Users.get_or_none(id=target_id):
                            try:
                                chat = client.get_chat(chat_id=target_id)
                                chat = db_management.DBObject(obj=chat, client=client)
                            except pyrogram.errors.FloodWait as ex:
                                print(ex)
                                traceback.print_exc()
                                text = _(
                                    chat_settings.language, "tg_flood_wait_X"
                                ).format(ex.x)
                            except pyrogram.errors.RPCError as ex:
                                print(ex)
                                traceback.print_exc()
                                text = _(chat_settings.language, "tg_error_X").format(
                                    ex
                                )

                        if msg.command[0].lower().endswith("pvt"):
                            methods.SendMessage(
                                client=client,
                                chat_id=msg.from_user.id,
                                text=text
                                or methods.Info(
                                    client=client,
                                    target=target_id,
                                    chat_id=chat_id,
                                    chat_settings=chat_settings,
                                ),
                                reply_markup=pyrogram.InlineKeyboardMarkup(
                                    keyboards.BuildInfoMenu(
                                        target=target_id,
                                        chat_id=chat_id,
                                        current_keyboard="maininfo",
                                        chat_settings=chat_settings,
                                    )
                                )
                                if not text
                                else None,
                                parse_mode="html",
                            )
                            methods.ReplyText(
                                client=client,
                                msg=msg,
                                text=_(
                                    msg.from_user.settings.language, "sent_to_pvt"
                                ).format(client.ME.id),
                                parse_mode="html",
                            )
                        else:
                            methods.ReplyText(
                                client=client,
                                msg=msg,
                                text=text
                                or methods.Info(
                                    client=client,
                                    target=target_id,
                                    chat_id=chat_id,
                                    chat_settings=chat_settings,
                                ),
                                reply_markup=pyrogram.InlineKeyboardMarkup(
                                    keyboards.BuildInfoMenu(
                                        target=target_id,
                                        chat_id=chat_id,
                                        current_keyboard="maininfo",
                                        chat_settings=chat_settings,
                                    )
                                )
                                if not text
                                else None,
                                parse_mode="html",
                            )
    else:
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(
                msg.chat.settings.language
                if msg.chat.type != "private"
                else msg.from_user.settings.language,
                "no_chat_settings",
            ),
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["id"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdId(client: pyrogram.Client, msg: pyrogram.Message):
    if (
        utils.IsPrivilegedOrHigher(user_id=msg.from_user.id, chat_id=msg.chat.id)
        or msg.chat.type == "private"
    ):
        if len(msg.command) == 1 and not msg.reply_to_message:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=f"<code>{msg.chat.id}</code>\n<code>{msg.from_user.id}</code>",
                parse_mode="html",
            )
        else:
            value = utils.ResolveCommandToId(
                client=client,
                value=msg.command[1] if len(msg.command) == 2 else None,
                msg=msg,
            )
            if utils.IsInt(value):
                if msg.command[0].lower().endswith("pvt"):
                    methods.SendMessage(
                        client=client,
                        chat_id=msg.from_user.id,
                        text=f"<code>{value}</code>",
                        parse_mode="html",
                    )
                else:
                    methods.ReplyText(
                        client=client,
                        msg=msg,
                        text=f"<code>{value}</code>",
                        parse_mode="html",
                    )
            else:
                if msg.command[0].lower().endswith("pvt"):
                    methods.SendMessage(
                        client=client,
                        chat_id=msg.from_user.id,
                        text=value
                        if value
                        else _(msg.from_user.settings.language, "unknown_user_chat"),
                    )
                else:
                    methods.ReplyText(
                        client=client,
                        msg=msg,
                        text=value
                        if value
                        else _(msg.from_user.settings.language, "unknown_user_chat"),
                    )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["username"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdUsername(client: pyrogram.Client, msg: pyrogram.Message):
    if (
        utils.IsPrivilegedOrHigher(user_id=msg.from_user.id, chat_id=msg.chat.id)
        or msg.chat.type == "private"
    ):
        text = None
        if len(msg.command) == 1 and not msg.reply_to_message:
            text = "{0}\n{1}".format(
                f"@{msg.chat.username}"
                if msg.chat.username
                else _(msg.chat.settings.language, "no_username"),
                f"@{msg.from_user.username}"
                if msg.from_user.username
                else _(msg.chat.settings.language, "no_username"),
            )
        else:
            if msg.reply_to_message and len(msg.command) == 1:
                text = (
                    f"@{msg.reply_to_message.from_user.username}"
                    if msg.reply_to_message.from_user.username
                    else None
                )
            elif len(msg.command) == 2:
                if utils.IsInt(msg.command[1]):
                    query: peewee.ModelSelect = db_management.ResolvedObjects.select().where(
                        db_management.ResolvedObjects.id == int(msg.command[1])
                    ).order_by(
                        db_management.ResolvedObjects.timestamp.desc()
                    )
                    try:
                        resolved_obj = query.get()
                    except db_management.ResolvedObjects.DoesNotExist:
                        resolved_obj = None
                    if not resolved_obj:
                        try:
                            tmp = client.get_chat(chat_id=msg.command[1])
                            tmp = db_management.DBObject(obj=tmp, client=client)
                            text = f"@{tmp.username}"
                        except pyrogram.errors.FloodWait as ex:
                            print(ex)
                            traceback.print_exc()
                            text = _(
                                msg.chat.settings.language, "tg_flood_wait_X"
                            ).format(ex.x)
                        except pyrogram.errors.RPCError as ex:
                            print(ex)
                            traceback.print_exc()
                            text = _(msg.chat.settings.language, "tg_error_X").format(
                                ex
                            )
                    else:
                        text = f"@{resolved_obj.username}"
                else:
                    if msg.entities:
                        for entity in msg.entities:
                            if entity.type == "text_mention":
                                text = (
                                    f"@{entity.user.username}"
                                    if entity.user.username
                                    else None
                                )

        if msg.command[0].lower().endswith("pvt"):
            methods.SendMessage(
                client=client,
                chat_id=msg.from_user.id,
                text=text
                if text
                else _(msg.from_user.settings.language, "unknown_user_chat"),
            )
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=text
                if text
                else _(msg.chat.settings.language, "unknown_user_chat"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(
            commands=["ishere", "ismember"], del_=True, pvt=True
        ),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group
)
def CmdIsMember(client: pyrogram.Client, msg: pyrogram.Message):
    if utils.IsPrivilegedOrHigher(user_id=msg.from_user.id, chat_id=msg.chat.id):
        member = None
        try:
            if msg.reply_to_message and len(msg.command) == 1:
                member = client.get_chat_member(
                    chat_id=msg.chat.id, user_id=msg.reply_to_message.from_user.id
                )
            elif len(msg.command) == 2:
                if msg.entities:
                    for entity in msg.entities:
                        if entity.type == "text_mention":
                            member = client.get_chat_member(
                                chat_id=msg.chat.id, user_id=entity.user.id
                            )
                if not member:
                    if utils.IsInt(msg.command[1]):
                        query: peewee.ModelSelect = db_management.ResolvedObjects.select().where(
                            db_management.ResolvedObjects.id == int(msg.command[1])
                        ).order_by(
                            db_management.ResolvedObjects.timestamp.desc()
                        )
                    else:
                        query: peewee.ModelSelect = db_management.ResolvedObjects.select().where(
                            db_management.ResolvedObjects.username == msg.command[1]
                        ).order_by(
                            db_management.ResolvedObjects.timestamp.desc()
                        )

                    try:
                        resolved_obj = query.get()
                    except db_management.ResolvedObjects.DoesNotExist:
                        resolved_obj = None

                    tmp_id = None
                    if resolved_obj:
                        tmp_id = resolved_obj.id
                    else:
                        tmp_id = msg.command[1]

                    try:
                        tmp = client.get_chat(chat_id=tmp_id)
                        tmp = db_management.DBObject(obj=tmp, client=client)
                        member = client.get_chat_member(
                            chat_id=msg.chat.id, user_id=tmp.id
                        )
                    except pyrogram.errors.FloodWait as ex:
                        print(ex)
                        traceback.print_exc()
                        raise ex
                    except pyrogram.errors.RPCError as ex:
                        print(ex)
                        traceback.print_exc()
                        raise ex
        except pyrogram.errors.FloodWait as ex:
            print(ex)
            traceback.print_exc()
        except pyrogram.errors.RPCError as ex:
            print(ex)
            traceback.print_exc()
        else:
            if msg.command[0].lower().endswith("pvt"):
                methods.SendMessage(
                    client=client,
                    chat_id=msg.from_user.id,
                    text=_(
                        msg.from_user.settings.language,
                        str(
                            member.status == "creator"
                            or member.status == "administrator"
                            or member.status == "member"
                            or (member.status == "restricted" and member.is_member)
                        ).lower(),
                    ),
                )
            else:
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(
                        msg.chat.settings.language,
                        str(
                            member.status == "creator"
                            or member.status == "administrator"
                            or member.status == "member"
                            or (member.status == "restricted" and member.is_member)
                        ).lower(),
                    ),
                )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["ishere", "ismember"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.private
)
def CmdIsMemberChat(client: pyrogram.Client, msg: pyrogram.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[2], msg=msg)
    if isinstance(chat_id, str) or isinstance(user_id, str):
        if isinstance(chat_id, str):
            methods.ReplyText(client=client, msg=msg, text=chat_id)
        if isinstance(user_id, str):
            methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        chat_settings: db_management.ChatSettings = db_management.ChatSettings.get_or_none(
            chat_id=chat_id
        )
        if chat_settings:
            if utils.IsPrivilegedOrHigher(
                user_id=msg.from_user.id, chat_id=msg.chat.id
            ):
                try:
                    member = client.get_chat_member(chat_id=chat_id, user_id=user_id)
                except pyrogram.errors.FloodWait as ex:
                    print(ex)
                    traceback.print_exc()
                except pyrogram.errors.RPCError as ex:
                    print(ex)
                    traceback.print_exc()
                else:
                    methods.ReplyText(
                        client=client,
                        msg=msg,
                        text=_(
                            msg.chat.settings.language,
                            str(
                                member.status == "creator"
                                or member.status == "administrator"
                                or member.status == "member"
                                or (member.status == "restricted" and member.is_member)
                            ).lower(),
                        ),
                    )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["me"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group
)
def CmdMe(client: pyrogram.Client, msg: pyrogram.Message):
    total_chat_messages = (
        db_management.RUserChat.select(
            peewee.fn.SUM(db_management.RUserChat.message_counter).alias("total")
        )
        .where(db_management.RUserChat.chat == msg.chat.id)
        .group_by(db_management.RUserChat.chat)[0]
        .total
    )
    if msg.command[0].lower().endswith("pvt"):
        methods.SendMessage(
            client=client,
            chat_id=msg.from_user.id,
            text=_(msg.from_user.settings.language, "me_string").format(
                msg.r_user_chat.message_counter,
                total_chat_messages,
                msg.r_user_chat.message_counter * 100 / total_chat_messages,
            ),
        )
    else:
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "me_string").format(
                msg.r_user_chat.message_counter,
                total_chat_messages,
                msg.r_user_chat.message_counter * 100 / total_chat_messages,
            ),
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^groups PAGES[<<|\-|\+|>>]", flags=re.I)
    & my_filters.callback_private
)
def CbQryGroupsPages(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
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
                keyboards.BuildGroupsMenu(
                    chat_settings=cb_qry.from_user.settings, page=0
                )
            )
        )
    elif cb_qry.data.endswith("-"):
        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupsMenu(
                    chat_settings=cb_qry.from_user.settings, page=page - 1
                )
            )
        )
    elif cb_qry.data.endswith("+"):
        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupsMenu(
                    chat_settings=cb_qry.from_user.settings, page=page + 1
                )
            )
        )
    elif cb_qry.data.endswith(">>"):
        cb_qry.message.edit_reply_markup(
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildGroupsMenu(
                    chat_settings=cb_qry.from_user.settings, page=-1
                )
            )
        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=["links", "groups"], prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.private
)
def CmdGroups(client: pyrogram.Client, msg: pyrogram.Message):
    methods.ReplyText(
        client=client,
        msg=msg,
        text=_(msg.from_user.settings.language, "public_groups_notice"),
        reply_markup=pyrogram.InlineKeyboardMarkup(
            keyboards.BuildGroupsMenu(chat_settings=msg.from_user.settings, page=-1)
        ),
    )
