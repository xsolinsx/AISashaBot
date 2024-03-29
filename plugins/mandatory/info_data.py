import datetime
import re
import traceback

import db_management
import dictionaries
import keyboards
import methods
import my_filters
import peewee
import pyrogram
import utils
from pyrogram import errors as pyrogram_errors

_ = utils.GetLocalizedString


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^\(i\)info (.+)", flags=re.I)
)
def CbQryInfoInfo(client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery):
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
    pyrogram.filters.regex(pattern=r"^maininfo (.+)", flags=re.I)
)
def CbQryInfoMenu(client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery):
    parameters = list()
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

    if (
        cb_qry.message.chat.type != pyrogram.enums.chat_type.ChatType.PRIVATE
        and not utils.IsJuniorModOrHigher(
            user_id=cb_qry.from_user.id, chat_id=chat_id, r_user_chat=r_executer_chat
        )
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
            reply_markup=keyboards.BuildInfoMenu(
                target=target_id,
                chat_id=chat_id,
                current_keyboard="maininfo",
                chat_settings=chat_settings,
                r_target_chat=r_target_chat,
            ),
            parse_mode=pyrogram.enums.parse_mode.ParseMode.HTML,
        )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^info (.+)", flags=re.I)
)
def CbQryInfoChange(client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery):
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
            min_rank=dictionaries.RANK_STRING["senior_mod"],
        ):
            r_target_chat.rank = (
                dictionaries.RANK_STRING["privileged_user"]
                if r_target_chat.rank != dictionaries.RANK_STRING["privileged_user"]
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
                    show_alert=True,
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
            min_rank=dictionaries.RANK_STRING["senior_mod"],
        ):
            r_target_chat.rank = (
                dictionaries.RANK_STRING["junior_mod"]
                if r_target_chat.rank != dictionaries.RANK_STRING["junior_mod"]
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
                    show_alert=True,
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
            min_rank=dictionaries.RANK_STRING["owner"],
        ):
            r_target_chat.rank = (
                dictionaries.RANK_STRING["senior_mod"]
                if r_target_chat.rank != dictionaries.RANK_STRING["senior_mod"]
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
                    show_alert=True,
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
            < dictionaries.RANK_STRING["junior_mod"]
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
                    show_alert=True,
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
                    show_alert=True,
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
            min_rank=dictionaries.RANK_STRING["junior_mod"],
        ):
            text = None
            if "--" in cb_qry.data:
                text = methods.Unwarn(
                    client=client,
                    executer=cb_qry.from_user.id,
                    target=target_id,
                    chat_id=chat_id,
                    r_executer_chat=r_executer_chat,
                    r_target_chat=r_target_chat,
                    chat_settings=chat_settings,
                )
            elif "++" in cb_qry.data:
                text = methods.Warn(
                    client=client,
                    executer=cb_qry.from_user.id,
                    target=target_id,
                    chat_id=chat_id,
                    r_executer_chat=r_executer_chat,
                    r_target_chat=r_target_chat,
                    chat_settings=chat_settings,
                )

            if text:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=text,
                    show_alert=True,
                )
                methods.SendMessage(client=client, chat_id=chat_id, text=text)
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
    elif "punishments" in cb_qry.data:
        if utils.CompareRanks(
            executer=cb_qry.from_user.id,
            target=target_id,
            chat_id=chat_id,
            r_executer_chat=r_executer_chat,
            r_target_chat=r_target_chat,
            min_rank=dictionaries.RANK_STRING["junior_mod"],
        ):
            if "selectvalue" in cb_qry.data:
                text = None
                punishment = int(regex_info_select_value.match(cb_qry.data)[2])
                until_date = None
                if punishment == dictionaries.PUNISHMENT_STRING["kick"]:
                    text = methods.Kick(
                        client=client,
                        executer=cb_qry.from_user.id,
                        target=target_id,
                        chat_id=chat_id,
                    )
                elif punishment == dictionaries.PUNISHMENT_STRING["temprestrict"]:
                    until_date = datetime.datetime.utcnow() + datetime.timedelta(
                        seconds=chat_settings.max_temp_restrict
                    )
                    text = methods.Restrict(
                        client=client,
                        executer=cb_qry.from_user.id,
                        target=target_id,
                        chat_id=chat_id,
                        until_date=until_date,
                    )
                elif punishment == dictionaries.PUNISHMENT_STRING["restrict"]:
                    text = methods.Restrict(
                        client=client,
                        executer=cb_qry.from_user.id,
                        target=target_id,
                        chat_id=chat_id,
                    )
                elif punishment == dictionaries.PUNISHMENT_STRING["tempban"]:
                    until_date = datetime.datetime.utcnow() + datetime.timedelta(
                        seconds=chat_settings.max_temp_ban
                    )
                    text = methods.Ban(
                        client=client,
                        executer=cb_qry.from_user.id,
                        target=target_id,
                        chat_id=chat_id,
                        until_date=until_date,
                    )
                elif punishment == dictionaries.PUNISHMENT_STRING["ban"]:
                    text = methods.Ban(
                        client=client,
                        executer=cb_qry.from_user.id,
                        target=target_id,
                        chat_id=chat_id,
                    )
                else:
                    punishment = 0

                if punishment and text:
                    methods.CallbackQueryAnswer(
                        cb_qry=cb_qry,
                        text=text,
                        show_alert=True,
                    )
                    methods.SendMessage(client=client, chat_id=chat_id, text=text)
                else:
                    methods.CallbackQueryAnswer(
                        cb_qry=cb_qry,
                        text=_(cb_qry.from_user.settings.language, "error_try_again"),
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
        reply_markup=keyboards.BuildInfoMenu(
            target=target_id,
            chat_id=chat_id,
            current_keyboard="maininfo",
            chat_settings=chat_settings,
            r_target_chat=r_target_chat,
            selected_setting=setting,
        ),
        parse_mode=pyrogram.enums.parse_mode.ParseMode.HTML,
    )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(
            commands=["info", "promote", "demote"], del_=True, pvt=True
        ),
        prefixes=["/", "!", "#", "."],
    )
)
@pyrogram.Client.on_edited_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(
            commands=["info", "promote", "demote"], del_=True, pvt=True
        ),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdInfo(client: pyrogram.Client, msg: pyrogram.types.Message):
    chat_id = None
    target_id = None
    if (
        len(msg.command) == 3
        and msg.chat.type == pyrogram.enums.chat_type.ChatType.PRIVATE
    ):
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
        chat_settings: db_management.ChatSettings = (
            db_management.ChatSettings.get_or_none(chat_id=chat_id)
        )
    else:
        # user
        chat_settings: db_management.UserSettings = (
            db_management.UserSettings.get_or_none(user_id=chat_id)
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
                        except pyrogram_errors.FloodWait as ex:
                            print(ex)
                            traceback.print_exc()
                            text = _(chat_settings.language, "tg_flood_wait_X").format(
                                ex.value
                            )
                        except pyrogram_errors.RPCError as ex:
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
                            reply_markup=keyboards.BuildInfoMenu(
                                target=target_id,
                                chat_id=chat_id,
                                current_keyboard="maininfo",
                                chat_settings=chat_settings,
                            )
                            if not text
                            else None,
                            parse_mode=pyrogram.enums.parse_mode.ParseMode.HTML,
                        )
                        methods.ReplyText(
                            client=client,
                            msg=msg,
                            text=_(
                                msg.from_user.settings.language, "sent_to_pvt"
                            ).format(client.ME.id),
                            parse_mode=pyrogram.enums.parse_mode.ParseMode.HTML,
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
                            reply_markup=keyboards.BuildInfoMenu(
                                target=target_id,
                                chat_id=chat_id,
                                current_keyboard="maininfo",
                                chat_settings=chat_settings,
                            )
                            if not text
                            else None,
                            parse_mode=pyrogram.enums.parse_mode.ParseMode.HTML,
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
                        except pyrogram_errors.FloodWait as ex:
                            print(ex)
                            traceback.print_exc()
                            text = _(chat_settings.language, "tg_flood_wait_X").format(
                                ex.value
                            )
                        except pyrogram_errors.RPCError as ex:
                            print(ex)
                            traceback.print_exc()
                            text = _(chat_settings.language, "tg_error_X").format(ex)

                        r_target_chat: db_management.RUserChat = (
                            db_management.RUserChat.get_or_none(
                                user_id=target_id, chat_id=chat_id
                            )
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
                                    reply_markup=keyboards.BuildInfoMenu(
                                        target=target_id,
                                        chat_id=chat_id,
                                        current_keyboard="maininfo",
                                        chat_settings=chat_settings,
                                        r_target_chat=r_target_chat,
                                    )
                                    if not text
                                    else None,
                                    parse_mode=pyrogram.enums.parse_mode.ParseMode.HTML,
                                )
                                methods.ReplyText(
                                    client=client,
                                    msg=msg,
                                    text=_(
                                        msg.from_user.settings.language, "sent_to_pvt"
                                    ).format(client.ME.id),
                                    parse_mode=pyrogram.enums.parse_mode.ParseMode.HTML,
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
                                    reply_markup=keyboards.BuildInfoMenu(
                                        target=target_id,
                                        chat_id=chat_id,
                                        current_keyboard="maininfo",
                                        chat_settings=chat_settings,
                                        r_target_chat=r_target_chat,
                                    )
                                    if not text
                                    else None,
                                    parse_mode=pyrogram.enums.parse_mode.ParseMode.HTML,
                                )
                    else:
                        # user
                        text = None
                        if not db_management.Users.get_or_none(id=target_id):
                            try:
                                chat = client.get_chat(chat_id=target_id)
                                chat = db_management.DBObject(obj=chat, client=client)
                            except pyrogram_errors.FloodWait as ex:
                                print(ex)
                                traceback.print_exc()
                                text = _(
                                    chat_settings.language, "tg_flood_wait_X"
                                ).format(ex.value)
                            except pyrogram_errors.RPCError as ex:
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
                                reply_markup=keyboards.BuildInfoMenu(
                                    target=target_id,
                                    chat_id=chat_id,
                                    current_keyboard="maininfo",
                                    chat_settings=chat_settings,
                                )
                                if not text
                                else None,
                                parse_mode=pyrogram.enums.parse_mode.ParseMode.HTML,
                            )
                            methods.ReplyText(
                                client=client,
                                msg=msg,
                                text=_(
                                    msg.from_user.settings.language, "sent_to_pvt"
                                ).format(client.ME.id),
                                parse_mode=pyrogram.enums.parse_mode.ParseMode.HTML,
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
                                reply_markup=keyboards.BuildInfoMenu(
                                    target=target_id,
                                    chat_id=chat_id,
                                    current_keyboard="maininfo",
                                    chat_settings=chat_settings,
                                )
                                if not text
                                else None,
                                parse_mode=pyrogram.enums.parse_mode.ParseMode.HTML,
                            )
    else:
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(
                msg.chat.settings.language
                if msg.chat.type != pyrogram.enums.chat_type.ChatType.PRIVATE
                else msg.from_user.settings.language,
                "no_chat_settings",
            ),
        )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^\(i\)messages (\d+)", flags=re.I)
)
def CbQryMessagesInfoUser(
    client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery
):
    text = ""
    if cb_qry.data == "(i)messages ":
        text = _(cb_qry.from_user.settings.language, cb_qry.data)
    else:
        user = db_management.Users.get_or_none(
            id=int(cb_qry.data.replace("(i)messages ", ""))
        )
        if user:
            text = utils.PrintUser(user=user)
        else:
            text = int(cb_qry.data.replace("(i)messages ", ""))
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry,
        text=text,
        show_alert=True,
    )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^\(i\)messages members_only", flags=re.I)
)
def CbQryMessagesInfoOnlyMembers(
    client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery
):
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry,
        text=_(cb_qry.from_user.settings.language, cb_qry.data),
        show_alert=True,
    )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^messages members_only", flags=re.I)
)
def CbQryMessagesOnlyMembers(
    client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery
):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    members_only = not bool(int(parameters[2]))
    page = int(parameters[3])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry,
        text=_(cb_qry.from_user.settings.language, "updating"),
        show_alert=False,
    )
    if chat_id not in utils.tmp_dicts["membersUpdated"]:
        utils.tmp_dicts["membersUpdated"].add(chat_id)
        try:
            db_management.DBChatMembers(client=client, chat_id=chat_id, clean_up=True)
        except pyrogram_errors.FloodWait as ex:
            print(ex)
            traceback.print_exc()
            methods.ReplyText(
                client=client,
                msg=cb_qry.message,
                text=_(chat_settings.language, "tg_flood_wait_X").format(ex.value),
            )
        except pyrogram_errors.RPCError as ex:
            print(ex)
            traceback.print_exc()
            methods.ReplyText(
                client=client,
                msg=cb_qry.message,
                text=_(chat_settings.language, "tg_error_X").format(ex),
            )
        else:
            utils.Log(
                client=client,
                chat_id=chat_id,
                executer=cb_qry.from_user.id,
                action="members updated",
                target=chat_id,
            )
    cb_qry.message.edit_reply_markup(
        reply_markup=keyboards.BuildMessagesList(
            chat_settings=chat_settings, members_only=members_only, page=page
        )
    )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^messages PAGES (\d+)$", flags=re.I)
)
def CbQryMessagesPages(client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery):
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )
    chat_id = int(parameters[1])
    members_only = bool(int(parameters[2]))
    page = int(cb_qry.data.split(" ")[2]) - 1
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsJuniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry, text=_(cb_qry.from_user.settings.language, "turning_page")
        )
        cb_qry.message.edit_reply_markup(
            reply_markup=keyboards.BuildMessagesList(
                chat_settings=chat_settings, members_only=members_only, page=page
            )
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^messages (\-\d+) (\d+)", flags=re.I)
)
def CbQryMessages(client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery):
    parameters = cb_qry.data.split(" ")
    chat_id = int(parameters[1])
    members_only = bool(int(parameters[2]))
    page = int(parameters[3])
    chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    if utils.IsJuniorModOrHigher(user_id=cb_qry.from_user.id, chat_id=chat_id):
        cb_qry.message.edit_text(
            text=_(cb_qry.message.chat.settings.language, "messages")
            + f" {utils.PrintChat(chat=chat_settings.chat)}",
            reply_markup=keyboards.BuildMessagesList(
                chat_settings=chat_settings, members_only=members_only, page=page
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
        commands=utils.GetCommandsVariants(commands=["messages"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
@pyrogram.Client.on_edited_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["messages"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
def CmdMessages(client: pyrogram.Client, msg: pyrogram.types.Message):
    if utils.IsJuniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        if msg.chat.id not in utils.tmp_dicts["membersUpdated"]:
            utils.tmp_dicts["membersUpdated"].add(msg.chat.id)
            try:
                db_management.DBChatMembers(
                    client=client, chat_id=msg.chat.id, clean_up=True
                )
            except pyrogram_errors.FloodWait as ex:
                print(ex)
                traceback.print_exc()
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(msg.chat.settings.language, "tg_flood_wait_X").format(
                        ex.value
                    ),
                )
            except pyrogram_errors.RPCError as ex:
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
                    action="members updated",
                    target=msg.chat.id,
                )
        utils.Log(
            client=client,
            chat_id=msg.chat.id,
            executer=msg.from_user.id,
            action=f"{msg.command[0]}",
            target=msg.chat.id,
        )
        if msg.command[0].lower().endswith("pvt"):
            methods.SendMessage(
                client=client,
                chat_id=msg.from_user.id,
                text=_(msg.chat.settings.language, "messages")
                + f" {utils.PrintChat(chat=msg.chat)}",
                reply_markup=keyboards.BuildMessagesList(
                    chat_settings=msg.chat.settings, members_only=True, page=0
                ),
            )
            if not msg.text.startswith("del", 1):
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(msg.from_user.settings.language, "sent_to_pvt").format(
                        client.ME.id
                    ),
                    parse_mode=pyrogram.enums.parse_mode.ParseMode.HTML,
                )
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "messages")
                + f" {utils.PrintChat(chat=msg.chat)}",
                reply_markup=keyboards.BuildMessagesList(
                    chat_settings=msg.chat.settings, members_only=True, page=0
                ),
            )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=["messages"],
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
@pyrogram.Client.on_edited_message(
    pyrogram.filters.command(
        commands=["messages"],
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
def CmdMessagesChat(client: pyrogram.Client, msg: pyrogram.types.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = (
            db_management.ChatSettings.get_or_none(chat_id=chat_id)
        )
        if chat_settings:
            if utils.IsJuniorModOrHigher(user_id=msg.from_user.id, chat_id=chat_id):
                if chat_id not in utils.tmp_dicts["membersUpdated"]:
                    utils.tmp_dicts["membersUpdated"].add(chat_id)
                    try:
                        db_management.DBChatMembers(
                            client=client, chat_id=chat_id, clean_up=True
                        )
                    except pyrogram_errors.FloodWait as ex:
                        print(ex)
                        traceback.print_exc()
                        methods.ReplyText(
                            client=client,
                            msg=msg,
                            text=_(chat_settings.language, "tg_flood_wait_X").format(
                                ex.value
                            ),
                        )
                    except pyrogram_errors.RPCError as ex:
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
                            action="members updated",
                            target=chat_id,
                        )
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
                    text=_(chat_settings.language, "messages")
                    + f" {utils.PrintChat(chat=chat_settings.chat)}",
                    reply_markup=keyboards.BuildMessagesList(
                        chat_settings=chat_settings, members_only=True, page=0
                    ),
                )
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["id"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
)
@pyrogram.Client.on_edited_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["id"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdId(client: pyrogram.Client, msg: pyrogram.types.Message):
    if (
        utils.IsPrivilegedOrHigher(user_id=msg.from_user.id, chat_id=msg.chat.id)
        or msg.chat.type == pyrogram.enums.chat_type.ChatType.PRIVATE
    ):
        if len(msg.command) == 1 and not msg.reply_to_message:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=f"<code>{msg.chat.id}</code>\n<code>{msg.from_user.id}</code>",
                parse_mode=pyrogram.enums.parse_mode.ParseMode.HTML,
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
                        parse_mode=pyrogram.enums.parse_mode.ParseMode.HTML,
                    )
                else:
                    methods.ReplyText(
                        client=client,
                        msg=msg,
                        text=f"<code>{value}</code>",
                        parse_mode=pyrogram.enums.parse_mode.ParseMode.HTML,
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
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["username"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
)
@pyrogram.Client.on_edited_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["username"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdUsername(client: pyrogram.Client, msg: pyrogram.types.Message):
    if (
        utils.IsPrivilegedOrHigher(user_id=msg.from_user.id, chat_id=msg.chat.id)
        or msg.chat.type == pyrogram.enums.chat_type.ChatType.PRIVATE
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
                    query: peewee.ModelSelect = (
                        db_management.ResolvedObjects.select()
                        .where(db_management.ResolvedObjects.id == int(msg.command[1]))
                        .order_by(db_management.ResolvedObjects.timestamp.desc())
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
                        except pyrogram_errors.FloodWait as ex:
                            print(ex)
                            traceback.print_exc()
                            text = _(
                                msg.chat.settings.language, "tg_flood_wait_X"
                            ).format(ex.value)
                        except pyrogram_errors.RPCError as ex:
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
                            if (
                                entity.type
                                == pyrogram.enums.message_entity_type.MessageEntityType.TEXT_MENTION
                            ):
                                text = (
                                    f"@{entity.user.username}"
                                    if entity.user.username
                                    else None
                                )
                                break

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
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(
            commands=["ishere", "ismember"], del_=True, pvt=True
        ),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
@pyrogram.Client.on_edited_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(
            commands=["ishere", "ismember"], del_=True, pvt=True
        ),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
def CmdIsMember(client: pyrogram.Client, msg: pyrogram.types.Message):
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
                        if (
                            entity.type
                            == pyrogram.enums.message_entity_type.MessageEntityType.TEXT_MENTION
                        ):
                            member = client.get_chat_member(
                                chat_id=msg.chat.id, user_id=entity.user.id
                            )
                            break
                if not member:
                    if utils.IsInt(msg.command[1]):
                        query: peewee.ModelSelect = (
                            db_management.ResolvedObjects.select()
                            .where(
                                db_management.ResolvedObjects.id == int(msg.command[1])
                            )
                            .order_by(db_management.ResolvedObjects.timestamp.desc())
                        )
                    else:
                        query: peewee.ModelSelect = (
                            db_management.ResolvedObjects.select()
                            .where(
                                db_management.ResolvedObjects.username == msg.command[1]
                            )
                            .order_by(db_management.ResolvedObjects.timestamp.desc())
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
                    except pyrogram_errors.FloodWait as ex:
                        print(ex)
                        traceback.print_exc()
                        raise ex
                    except pyrogram_errors.RPCError as ex:
                        print(ex)
                        traceback.print_exc()
                        raise ex
        except pyrogram_errors.FloodWait as ex:
            print(ex)
            traceback.print_exc()
        except pyrogram_errors.RPCError as ex:
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
                            member.status
                            == pyrogram.enums.chat_member_status.ChatMemberStatus.OWNER
                            or member.status
                            == pyrogram.enums.chat_member_status.ChatMemberStatus.ADMINISTRATOR
                            or member.status
                            == pyrogram.enums.chat_member_status.ChatMemberStatus.MEMBER
                            or (
                                member.status
                                == pyrogram.enums.chat_member_status.ChatMemberStatus.RESTRICTED
                                and member.is_member
                            )
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
                            member.status
                            == pyrogram.enums.chat_member_status.ChatMemberStatus.OWNER
                            or member.status
                            == pyrogram.enums.chat_member_status.ChatMemberStatus.ADMINISTRATOR
                            or member.status
                            == pyrogram.enums.chat_member_status.ChatMemberStatus.MEMBER
                            or (
                                member.status
                                == pyrogram.enums.chat_member_status.ChatMemberStatus.RESTRICTED
                                and member.is_member
                            )
                        ).lower(),
                    ),
                )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["ishere", "ismember"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
@pyrogram.Client.on_edited_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["ishere", "ismember"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
def CmdIsMemberChat(client: pyrogram.Client, msg: pyrogram.types.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[2], msg=msg)
    if isinstance(chat_id, str) or isinstance(user_id, str):
        if isinstance(chat_id, str):
            methods.ReplyText(client=client, msg=msg, text=chat_id)
        if isinstance(user_id, str):
            methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        chat_settings: db_management.ChatSettings = (
            db_management.ChatSettings.get_or_none(chat_id=chat_id)
        )
        if chat_settings:
            if utils.IsPrivilegedOrHigher(
                user_id=msg.from_user.id, chat_id=msg.chat.id
            ):
                try:
                    member = client.get_chat_member(chat_id=chat_id, user_id=user_id)
                except pyrogram_errors.FloodWait as ex:
                    print(ex)
                    traceback.print_exc()
                except pyrogram_errors.RPCError as ex:
                    print(ex)
                    traceback.print_exc()
                else:
                    methods.ReplyText(
                        client=client,
                        msg=msg,
                        text=_(
                            msg.chat.settings.language,
                            str(
                                member.status
                                == pyrogram.enums.chat_member_status.ChatMemberStatus.OWNER
                                or member.status
                                == pyrogram.enums.chat_member_status.ChatMemberStatus.ADMINISTRATOR
                                or member.status
                                == pyrogram.enums.chat_member_status.ChatMemberStatus.MEMBER
                                or (
                                    member.status
                                    == pyrogram.enums.chat_member_status.ChatMemberStatus.RESTRICTED
                                    and member.is_member
                                )
                            ).lower(),
                        ),
                    )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["me"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
@pyrogram.Client.on_edited_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["me"], del_=True, pvt=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
def CmdMe(client: pyrogram.Client, msg: pyrogram.types.Message):
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
    pyrogram.filters.regex(pattern=r"^groups PAGES (\d+)$", flags=re.I)
    & my_filters.callback_private
)
def CbQryGroupsPages(client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery):
    page = int(cb_qry.data.split(" ")[2]) - 1
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry, text=_(cb_qry.from_user.settings.language, "turning_page")
    )
    cb_qry.message.edit_reply_markup(
        reply_markup=keyboards.BuildGroupsMenu(
            chat_settings=cb_qry.from_user.settings, page=page
        )
    )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=["links", "groups"],
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
@pyrogram.Client.on_edited_message(
    pyrogram.filters.command(
        commands=["links", "groups"],
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
def CmdGroups(client: pyrogram.Client, msg: pyrogram.types.Message):
    methods.ReplyText(
        client=client,
        msg=msg,
        text=_(msg.from_user.settings.language, "public_groups_notice"),
        reply_markup=keyboards.BuildGroupsMenu(
            chat_settings=msg.from_user.settings, page=-1
        ),
    )
