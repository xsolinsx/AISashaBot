import datetime
import html
import time
import traceback
import typing

import peewee
import pyrogram
from apscheduler.triggers.date import DateTrigger

import db_management
import dictionaries
import utils

_ = utils.GetLocalizedString


def Info(
    client: pyrogram.Client,
    target: typing.Union[int, str],
    chat_id: typing.Union[int, str],
    chat_settings: db_management.ChatSettings,
    r_target_chat: db_management.RUserChat = None,
) -> str:
    if target < 0:
        # chat
        chat_info = GetObjInfo(
            client=client,
            value=target,
            language=chat_settings.language if chat_settings else "en",
        )
        return (
            _(chat_settings.language, "info_of_X").format(
                f"{utils.PrintChat(chat=chat_settings.chat)}",
            )
            + chat_info
        )
    else:
        if chat_id < 0:
            # info of target in chat_id
            chat_settings: db_management.ChatSettings = chat_settings if chat_settings else db_management.ChatSettings.get_or_none(
                chat_id=chat_id
            )
            r_target_chat = r_target_chat or db_management.RUserChat.get_or_none(
                user_id=target, chat_id=chat_id
            )
            if not r_target_chat:
                r_target_chat = db_management.RUserChat.create(
                    user_id=target, chat_id=chat_id
                )
            user_info = GetObjInfo(
                client=client,
                value=target,
                language=chat_settings.language if chat_settings else "en",
            )
            user_info += (
                "\n"
                + _(chat_settings.language, "info_rank")
                + _(
                    chat_settings.language,
                    str(
                        dictionaries.RANKS[
                            utils.GetRank(
                                user_id=target,
                                chat_id=chat_id,
                                r_user_chat=r_target_chat,
                            )
                        ]
                    ),
                )
                + "\n"
                + _(chat_settings.language, "info_total_messages")
                + f"{r_target_chat.message_counter}\n"
            )
            other_info = []
            if r_target_chat.is_admin:
                other_info.append(_(chat_settings.language, "administrator").upper())
            if r_target_chat.user.is_bot:
                other_info.append(_(chat_settings.language, "bot").upper())
            user_info += _(chat_settings.language, "info_other") + ",".join(other_info)
            chat_info = GetObjInfo(
                client=client,
                value=chat_id,
                language=chat_settings.language if chat_settings else "en",
            )

            return (
                _(chat_settings.language, "info_of_X_in_Y").format(
                    f"{utils.PrintUser(r_target_chat.user)}",
                    f"{utils.PrintChat(chat=chat_settings.chat)}",
                )
                + f"{user_info}\n\n{chat_info}"
            )
        else:
            # user
            user_info = GetObjInfo(
                client=client,
                value=target,
                language=chat_settings.language if chat_settings else "en",
            )
            return (
                _(chat_settings.language, "info_of_X").format(f"(#user{target})")
                + user_info
            )


def GetObjInfo(
    client: pyrogram.Client, value: typing.Union[int, str], language: str
) -> str:
    if utils.IsInt(value):
        value = int(value)
    else:
        value = utils.CleanUsername(username=value)
        value = f"@{value}" if not value.startswith("@") else value
        query: peewee.ModelSelect = db_management.ResolvedObjects.select().where(
            db_management.ResolvedObjects.username == value[1:].lower()
        ).order_by(db_management.ResolvedObjects.timestamp.desc())
        try:
            resolved_obj = query.get()
            # if already resolved object return saved id
            value = resolved_obj.id
        except db_management.ResolvedObjects.DoesNotExist:
            # else try to resolve the username with Telegram
            # if success return id, else return error
            try:
                tmp = client.get_chat(chat_id=value)
                tmp = db_management.DBObject(obj=tmp, client=client)
                value = tmp.id
            except pyrogram.errors.RPCError as ex:
                print(ex)
                traceback.print_exc()
                value = None

    if value:
        if value < 0:
            # chat
            chat_settings: db_management.ChatSettings = db_management.ChatSettings.get_or_none(
                chat_id=value
            )
            if chat_settings:
                chat = chat_settings.chat
                return (
                    _(language, "info_id")
                    + f"<code>{chat.id}</code>\n"
                    + _(language, "info_title")
                    + f"{html.escape(chat.title)}\n"
                    + _(language, "info_username")
                    + (f"@{chat.username}" if chat.username else "/")
                    + "\n"
                )
            else:
                return _(language, "X_not_in_database")
        else:
            # user
            user_settings: db_management.UserSettings = db_management.UserSettings.get_or_none(
                user_id=value
            )
            if user_settings:
                user = user_settings.user
                return (
                    _(language, "info_id")
                    + f"<code>{user.id}</code>\n"
                    + _(language, "info_first_name")
                    + f"{html.escape(user.first_name)}\n"
                    + _(language, "info_last_name")
                    + (user.last_name if user.last_name else "/")
                    + "\n"
                    + _(language, "info_username")
                    + (f"@{user.username}" if user.username else "/")
                    + "\n"
                    + _(language, "info_nickname")
                    + (user_settings.nickname if user_settings.nickname else "/")
                )
            else:
                return _(language, "X_not_in_database")
    else:
        return _(language, "X_not_in_database")


def Invite(
    client: pyrogram.Client,
    executer: typing.Union[int, str],
    target: typing.Union[int, str],
    chat_id: typing.Union[int, str],
    r_executer_chat: db_management.RUserChat = None,
    r_target_chat: db_management.RUserChat = None,
    chat_settings: db_management.ChatSettings = None,
) -> str:
    r_executer_chat = r_executer_chat or db_management.RUserChat.get_or_none(
        user_id=executer, chat_id=chat_id
    )
    if not r_executer_chat:
        r_executer_chat = db_management.RUserChat.create(
            user_id=executer, chat_id=chat_id
        )
    r_target_chat = r_target_chat or db_management.RUserChat.get_or_none(
        user_id=target, chat_id=chat_id
    )
    if not r_target_chat:
        r_target_chat = db_management.RUserChat.create(user_id=target, chat_id=chat_id)
    chat_settings = chat_settings or db_management.ChatSettings.get_or_none(
        chat_id=chat_id
    )

    if utils.IsJuniorModOrHigher(user_id=executer, chat_id=chat_id):
        if chat_settings.link or chat_settings.chat.username:
            utils.InstantiateInvitedPeopleDictionary(chat_id=chat_id)
            if target not in utils.tmp_dicts["invitedPeople"][chat_id]:
                utils.tmp_dicts["invitedPeople"][chat_id].add(target)
                text = ""
                try:
                    SendMessage(
                        client=client,
                        chat_id=target,
                        text=_(chat_settings.language, "you_have_been_invited"),
                        reply_markup=pyrogram.InlineKeyboardMarkup(
                            [
                                [
                                    pyrogram.InlineKeyboardButton(
                                        text=chat_settings.chat.title,
                                        url=f"t.me/{chat_settings.chat.username}"
                                        if chat_settings.chat.username
                                        else chat_settings.link,
                                    )
                                ]
                            ]
                        ),
                    )
                except pyrogram.errors.FloodWait as ex:
                    print(ex)
                    traceback.print_exc()
                    run_date = datetime.datetime.utcnow() + datetime.timedelta(
                        seconds=ex.x
                    )
                    utils.scheduler.add_job(
                        func=Invite,
                        kwargs=dict(
                            client=client,
                            executer=executer,
                            target=target,
                            chat_id=chat_id,
                            r_executer_chat=r_executer_chat,
                            r_target_chat=r_target_chat,
                            chat_settings=chat_settings,
                        ),
                        trigger=DateTrigger(run_date=run_date),
                    )
                    text = _(
                        chat_settings.language, "tg_flood_wait_X_scheduled_Y"
                    ).format(ex.x, f"UTC {run_date}")
                except pyrogram.errors.RPCError as ex:
                    print(ex)
                    traceback.print_exc()
                    text = _(chat_settings.language, "tg_error_X").format(ex)
                else:
                    text = _(chat_settings.language, "action_on_user").format(
                        "#invite", target, "", executer, abs(chat_id)
                    )
                    utils.Log(
                        client=client,
                        chat_id=chat_id,
                        executer=executer,
                        action=text,
                        target=target,
                    )

                return text


def Warn(
    client: pyrogram.Client,
    executer: typing.Union[int, str],
    target: typing.Union[int, str],
    chat_id: typing.Union[int, str],
    reasons: str = "",
    r_executer_chat: db_management.RUserChat = None,
    r_target_chat: db_management.RUserChat = None,
    chat_settings: db_management.ChatSettings = None,
) -> str:
    r_executer_chat = r_executer_chat or db_management.RUserChat.get_or_none(
        user_id=executer, chat_id=chat_id
    )
    if not r_executer_chat:
        r_executer_chat = db_management.RUserChat.create(
            user_id=executer, chat_id=chat_id
        )
    r_target_chat = r_target_chat or db_management.RUserChat.get_or_none(
        user_id=target, chat_id=chat_id
    )
    if not r_target_chat:
        r_target_chat = db_management.RUserChat.create(user_id=target, chat_id=chat_id)
    chat_settings = chat_settings or db_management.ChatSettings.get_or_none(
        chat_id=chat_id
    )

    if not r_target_chat.is_whitelisted:
        if utils.CompareRanks(
            executer=executer,
            target=target,
            chat_id=chat_id,
            r_executer_chat=r_executer_chat,
            r_target_chat=r_target_chat,
            min_rank=dictionaries.RANKS["junior_mod"],
        ):
            if chat_settings.max_warns_punishment:
                r_target_chat.warns += 1
                r_target_chat.save()
                text = (
                    _(chat_settings.language, "action_on_user").format(
                        f"#warn {r_target_chat.warns}/{chat_settings.max_warns}",
                        target,
                        reasons,
                        executer,
                        abs(chat_id),
                    )
                    + "\n"
                )
                if r_target_chat.warns >= chat_settings.max_warns:
                    if chat_settings.max_warns_punishment == 4:
                        text += Restrict(
                            client=client,
                            executer=executer,
                            target=target,
                            chat_id=chat_id,
                            until_date=chat_settings.max_temp_restrict,
                            reasons=f"{reasons}\n"
                            + _(chat_settings.language, "max_warns_reached"),
                            r_executer_chat=r_executer_chat,
                            r_target_chat=r_target_chat,
                            chat_settings=chat_settings,
                        )
                    elif chat_settings.max_warns_punishment == 5:
                        text += Restrict(
                            client=client,
                            executer=executer,
                            target=target,
                            chat_id=chat_id,
                            reasons=f"{reasons}\n"
                            + _(chat_settings.language, "max_warns_reached"),
                            r_executer_chat=r_executer_chat,
                            r_target_chat=r_target_chat,
                            chat_settings=chat_settings,
                        )
                    elif chat_settings.max_warns_punishment == 6:
                        text += Ban(
                            client=client,
                            executer=executer,
                            target=target,
                            chat_id=chat_id,
                            until_date=chat_settings.max_temp_ban,
                            reasons=f"{reasons}\n"
                            + _(chat_settings.language, "max_warns_reached"),
                            r_executer_chat=r_executer_chat,
                            r_target_chat=r_target_chat,
                            chat_settings=chat_settings,
                        )
                    elif chat_settings.max_warns_punishment == 7:
                        text += Ban(
                            client=client,
                            executer=executer,
                            target=target,
                            chat_id=chat_id,
                            reasons=f"{reasons}\n"
                            + _(chat_settings.language, "max_warns_reached"),
                            r_executer_chat=r_executer_chat,
                            r_target_chat=r_target_chat,
                            chat_settings=chat_settings,
                        )
                    r_target_chat.warns = 0
                    r_target_chat.save()
                else:
                    utils.Log(
                        client=client,
                        chat_id=chat_id,
                        executer=executer,
                        action=text,
                        target=target,
                    )
                return text


def Unwarn(
    client: pyrogram.Client,
    executer: typing.Union[int, str],
    target: typing.Union[int, str],
    chat_id: typing.Union[int, str],
    reasons: str = "",
    r_executer_chat: db_management.RUserChat = None,
    r_target_chat: db_management.RUserChat = None,
    chat_settings: db_management.ChatSettings = None,
) -> str:
    r_executer_chat = r_executer_chat or db_management.RUserChat.get_or_none(
        user_id=executer, chat_id=chat_id
    )
    if not r_executer_chat:
        r_executer_chat = db_management.RUserChat.create(
            user_id=executer, chat_id=chat_id
        )
    r_target_chat = r_target_chat or db_management.RUserChat.get_or_none(
        user_id=target, chat_id=chat_id
    )
    if not r_target_chat:
        r_target_chat = db_management.RUserChat.create(user_id=target, chat_id=chat_id)
    chat_settings = chat_settings or db_management.ChatSettings.get_or_none(
        chat_id=chat_id
    )

    if not r_target_chat.is_whitelisted:
        if utils.CompareRanks(
            executer=executer,
            target=target,
            chat_id=chat_id,
            r_executer_chat=r_executer_chat,
            r_target_chat=r_target_chat,
            min_rank=dictionaries.RANKS["junior_mod"],
        ):
            if r_target_chat.warns > 0:
                r_target_chat.warns -= 1
                r_target_chat.save()
            text = _(chat_settings.language, "action_on_user").format(
                f"#unwarn {r_target_chat.warns}/{chat_settings.max_warns}",
                target,
                reasons,
                executer,
                abs(chat_id),
            )

            utils.Log(
                client=client,
                chat_id=chat_id,
                executer=executer,
                action=text,
                target=target,
            )
            return text


def UnwarnAll(
    client: pyrogram.Client,
    executer: typing.Union[int, str],
    target: typing.Union[int, str],
    chat_id: typing.Union[int, str],
    reasons: str = "",
    r_executer_chat: db_management.RUserChat = None,
    r_target_chat: db_management.RUserChat = None,
    chat_settings: db_management.ChatSettings = None,
) -> str:
    r_executer_chat = r_executer_chat or db_management.RUserChat.get_or_none(
        user_id=executer, chat_id=chat_id
    )
    if not r_executer_chat:
        r_executer_chat = db_management.RUserChat.create(
            user_id=executer, chat_id=chat_id
        )
    r_target_chat = r_target_chat or db_management.RUserChat.get_or_none(
        user_id=target, chat_id=chat_id
    )
    if not r_target_chat:
        r_target_chat = db_management.RUserChat.create(user_id=target, chat_id=chat_id)
    chat_settings = chat_settings or db_management.ChatSettings.get_or_none(
        chat_id=chat_id
    )

    if not r_target_chat.is_whitelisted:
        if utils.CompareRanks(
            executer=executer,
            target=target,
            chat_id=chat_id,
            r_executer_chat=r_executer_chat,
            r_target_chat=r_target_chat,
            min_rank=dictionaries.RANKS["junior_mod"],
        ):
            r_target_chat.warns = 0
            r_target_chat.save()
            text = _(chat_settings.language, "action_on_user").format(
                f"#unwarnall", target, reasons, executer, abs(chat_id)
            )

            utils.Log(
                client=client,
                chat_id=chat_id,
                executer=executer,
                action=text,
                target=target,
            )
            return text


def Kick(
    client: pyrogram.Client,
    executer: typing.Union[int, str],
    target: typing.Union[int, str],
    chat_id: typing.Union[int, str],
    reasons: str = "",
    r_executer_chat: db_management.RUserChat = None,
    r_target_chat: db_management.RUserChat = None,
    chat_settings: db_management.ChatSettings = None,
) -> str:
    r_executer_chat = r_executer_chat or db_management.RUserChat.get_or_none(
        user_id=executer, chat_id=chat_id
    )
    if not r_executer_chat:
        r_executer_chat = db_management.RUserChat.create(
            user_id=executer, chat_id=chat_id
        )
    r_target_chat = r_target_chat or db_management.RUserChat.get_or_none(
        user_id=target, chat_id=chat_id
    )
    if not r_target_chat:
        r_target_chat = db_management.RUserChat.create(user_id=target, chat_id=chat_id)
    chat_settings = chat_settings or db_management.ChatSettings.get_or_none(
        chat_id=chat_id
    )

    if not r_target_chat.is_whitelisted:
        if utils.CompareRanks(
            executer=executer,
            target=target,
            chat_id=chat_id,
            r_executer_chat=r_executer_chat,
            r_target_chat=r_target_chat,
            min_rank=dictionaries.RANKS["junior_mod"],
        ):
            text = ""
            try:
                client.kick_chat_member(
                    chat_id=chat_id, user_id=target, until_date=int(time.time()) + 35
                )
            except pyrogram.errors.FloodWait as ex:
                print(ex)
                traceback.print_exc()
                run_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=ex.x)
                utils.scheduler.add_job(
                    func=Kick,
                    kwargs=dict(
                        client=client,
                        executer=executer,
                        target=target,
                        chat_id=chat_id,
                        reasons=reasons,
                        r_executer_chat=r_executer_chat,
                        r_target_chat=r_target_chat,
                        chat_settings=chat_settings,
                    ),
                    trigger=DateTrigger(run_date=run_date),
                )
                text = _(chat_settings.language, "tg_flood_wait_X_scheduled_Y").format(
                    ex.x, f"UTC {run_date}"
                )
            except pyrogram.errors.RPCError as ex:
                print(ex)
                traceback.print_exc()
                text = _(chat_settings.language, "tg_error_X").format(ex)
            else:
                text = _(chat_settings.language, "action_on_user").format(
                    "#kickme" if executer == target else "#kick",
                    target,
                    reasons,
                    executer,
                    abs(chat_id),
                )

                utils.Log(
                    client=client,
                    chat_id=chat_id,
                    executer=executer,
                    action=text,
                    target=target,
                )
                if target in utils.tmp_dicts["invitedPeople"][chat_id]:
                    utils.tmp_dicts["invitedPeople"][chat_id].remove(target)
            return text


def Restrict(
    client: pyrogram.Client,
    executer: typing.Union[int, str],
    target: typing.Union[int, str],
    chat_id: typing.Union[int, str],
    until_date: int = 0,
    reasons: str = "",
    r_executer_chat: db_management.RUserChat = None,
    r_target_chat: db_management.RUserChat = None,
    chat_settings: db_management.ChatSettings = None,
) -> str:
    r_executer_chat = r_executer_chat or db_management.RUserChat.get_or_none(
        user_id=executer, chat_id=chat_id
    )
    if not r_executer_chat:
        r_executer_chat = db_management.RUserChat.create(
            user_id=executer, chat_id=chat_id
        )
    r_target_chat = r_target_chat or db_management.RUserChat.get_or_none(
        user_id=target, chat_id=chat_id
    )
    chat_settings = chat_settings or db_management.ChatSettings.get_or_none(
        chat_id=chat_id
    )

    if r_target_chat:
        if not r_target_chat.is_whitelisted:
            if utils.CompareRanks(
                executer=executer,
                target=target,
                chat_id=chat_id,
                r_executer_chat=r_executer_chat,
                r_target_chat=r_target_chat,
                min_rank=dictionaries.RANKS["junior_mod"],
            ):
                text = ""
                try:
                    client.restrict_chat_member(
                        chat_id=chat_id,
                        user_id=target,
                        permissions=pyrogram.ChatPermissions(),
                        until_date=until_date,
                    )
                except pyrogram.errors.FloodWait as ex:
                    print(ex)
                    traceback.print_exc()
                    run_date = datetime.datetime.utcnow() + datetime.timedelta(
                        seconds=ex.x
                    )
                    utils.scheduler.add_job(
                        func=Restrict,
                        kwargs=dict(
                            client=client,
                            executer=executer,
                            target=target,
                            chat_id=chat_id,
                            until_date=until_date,
                            reasons=reasons,
                            r_executer_chat=r_executer_chat,
                            r_target_chat=r_target_chat,
                            chat_settings=chat_settings,
                        ),
                        trigger=DateTrigger(run_date=run_date),
                    )
                    text = _(
                        chat_settings.language, "tg_flood_wait_X_scheduled_Y"
                    ).format(ex.x, f"UTC {run_date}")
                except pyrogram.errors.RPCError as ex:
                    print(ex)
                    traceback.print_exc()
                    text = _(chat_settings.language, "tg_error_X").format(ex)
                else:
                    text = _(chat_settings.language, "action_on_user").format(
                        (
                            "#temprestrict "
                            + _(chat_settings.language, "until")
                            + f" UTC {datetime.datetime.utcfromtimestamp(until_date)}"
                        )
                        if until_date
                        else "#restrict",
                        target,
                        reasons,
                        executer,
                        abs(chat_id),
                    )

                    utils.Log(
                        client=client,
                        chat_id=chat_id,
                        executer=executer,
                        action=text,
                        target=target,
                    )
                    if target in utils.tmp_dicts["invitedPeople"][chat_id]:
                        utils.tmp_dicts["invitedPeople"][chat_id].remove(target)
                return text
    else:
        if utils.IsJuniorModOrHigher(
            user_id=executer, chat_id=chat_id, r_user_chat=r_executer_chat
        ):
            if db_management.ChatPreActionList.get_or_none(
                chat_id=chat_id, user_id=target
            ):
                db_management.ChatPreActionList.update(
                    chat_id=chat_id, user_id=target, action="prerestrict"
                ).where(
                    (db_management.ChatPreActionList.user_id == target)
                    & (db_management.ChatPreActionList.chat_id == chat_id)
                ).execute()
            else:
                db_management.ChatPreActionList.create(
                    chat_id=chat_id, user_id=target, action="prerestrict"
                )
            text = _(chat_settings.language, "action_on_user").format(
                "#prerestrict", target, reasons, executer, abs(chat_id)
            )

            utils.Log(
                client=client,
                chat_id=chat_id,
                executer=executer,
                action=text,
                target=target,
            )
            if target in utils.tmp_dicts["invitedPeople"][chat_id]:
                utils.tmp_dicts["invitedPeople"][chat_id].remove(target)
            return text


def Unrestrict(
    client: pyrogram.Client,
    executer: typing.Union[int, str],
    target: typing.Union[int, str],
    chat_id: typing.Union[int, str],
    reasons: str = "",
    r_executer_chat: db_management.RUserChat = None,
    r_target_chat: db_management.RUserChat = None,
    chat_settings: db_management.ChatSettings = None,
) -> str:
    r_executer_chat = r_executer_chat or db_management.RUserChat.get_or_none(
        user_id=executer, chat_id=chat_id
    )
    if not r_executer_chat:
        r_executer_chat = db_management.RUserChat.create(
            user_id=executer, chat_id=chat_id
        )
    r_target_chat = r_target_chat or db_management.RUserChat.get_or_none(
        user_id=target, chat_id=chat_id
    )
    if not r_target_chat:
        r_target_chat = db_management.RUserChat.create(user_id=target, chat_id=chat_id)
    chat_settings = chat_settings or db_management.ChatSettings.get_or_none(
        chat_id=chat_id
    )

    if not r_target_chat.is_whitelisted:
        if utils.CompareRanks(
            executer=executer,
            target=target,
            chat_id=chat_id,
            r_executer_chat=r_executer_chat,
            r_target_chat=r_target_chat,
            min_rank=dictionaries.RANKS["junior_mod"],
        ):
            text = ""
            try:
                client.restrict_chat_member(
                    chat_id=chat_id,
                    user_id=target,
                    permissions=pyrogram.ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True,
                        can_send_polls=True,
                        can_change_info=True,
                        can_invite_users=True,
                        can_pin_messages=True,
                    ),
                )
            except pyrogram.errors.FloodWait as ex:
                print(ex)
                traceback.print_exc()
                run_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=ex.x)
                utils.scheduler.add_job(
                    func=Unrestrict,
                    kwargs=dict(
                        client=client,
                        executer=executer,
                        target=target,
                        chat_id=chat_id,
                        reasons=reasons,
                        r_executer_chat=r_executer_chat,
                        r_target_chat=r_target_chat,
                        chat_settings=chat_settings,
                    ),
                    trigger=DateTrigger(run_date=run_date),
                )
                text = _(chat_settings.language, "tg_flood_wait_X_scheduled_Y").format(
                    ex.x, f"UTC {run_date}"
                )
            except pyrogram.errors.RPCError as ex:
                print(ex)
                traceback.print_exc()
                text = _(chat_settings.language, "tg_error_X").format(ex)
            else:
                text = _(chat_settings.language, "action_on_user").format(
                    "#unrestrict", target, reasons, executer, abs(chat_id)
                )

                utils.Log(
                    client=client,
                    chat_id=chat_id,
                    executer=executer,
                    action=text,
                    target=target,
                )
            return text


def Ban(
    client: pyrogram.Client,
    executer: typing.Union[int, str],
    target: typing.Union[int, str],
    chat_id: typing.Union[int, str],
    until_date: int = 0,
    reasons: str = "",
    r_executer_chat: db_management.RUserChat = None,
    r_target_chat: db_management.RUserChat = None,
    chat_settings: db_management.ChatSettings = None,
) -> str:
    r_executer_chat = r_executer_chat or db_management.RUserChat.get_or_none(
        user_id=executer, chat_id=chat_id
    )
    if not r_executer_chat:
        r_executer_chat = db_management.RUserChat.create(
            user_id=executer, chat_id=chat_id
        )
    r_target_chat = r_target_chat or db_management.RUserChat.get_or_none(
        user_id=target, chat_id=chat_id
    )
    chat_settings = chat_settings or db_management.ChatSettings.get_or_none(
        chat_id=chat_id
    )

    if r_target_chat:
        if not r_target_chat.is_whitelisted:
            if utils.CompareRanks(
                executer=executer,
                target=target,
                chat_id=chat_id,
                r_executer_chat=r_executer_chat,
                r_target_chat=r_target_chat,
                min_rank=dictionaries.RANKS["junior_mod"],
            ):
                text = ""
                try:
                    client.kick_chat_member(
                        chat_id=chat_id, user_id=target, until_date=until_date
                    )
                except pyrogram.errors.FloodWait as ex:
                    print(ex)
                    traceback.print_exc()
                    run_date = datetime.datetime.utcnow() + datetime.timedelta(
                        seconds=ex.x
                    )
                    utils.scheduler.add_job(
                        func=Ban,
                        kwargs=dict(
                            client=client,
                            executer=executer,
                            target=target,
                            chat_id=chat_id,
                            until_date=until_date,
                            reasons=reasons,
                            r_executer_chat=r_executer_chat,
                            r_target_chat=r_target_chat,
                            chat_settings=chat_settings,
                        ),
                        trigger=DateTrigger(run_date=run_date),
                    )
                    text = _(
                        chat_settings.language, "tg_flood_wait_X_scheduled_Y"
                    ).format(ex.x, f"UTC {run_date}")
                except pyrogram.errors.RPCError as ex:
                    print(ex)
                    traceback.print_exc()
                    text = _(chat_settings.language, "tg_error_X").format(ex)
                else:
                    text = _(chat_settings.language, "action_on_user").format(
                        (
                            "#tempban "
                            + _(chat_settings.language, "until")
                            + f" UTC {datetime.datetime.utcfromtimestamp(until_date)}"
                        )
                        if until_date
                        else "#ban",
                        target,
                        reasons,
                        executer,
                        abs(chat_id),
                    )

                    utils.Log(
                        client=client,
                        chat_id=chat_id,
                        executer=executer,
                        action=text,
                        target=target,
                    )
                    if target in utils.tmp_dicts["invitedPeople"][chat_id]:
                        utils.tmp_dicts["invitedPeople"][chat_id].remove(target)
                return text
    else:
        if utils.IsJuniorModOrHigher(
            user_id=executer, chat_id=chat_id, r_user_chat=r_executer_chat
        ):
            if db_management.ChatPreActionList.get_or_none(
                chat_id=chat_id, user_id=target
            ):
                db_management.ChatPreActionList.update(
                    chat_id=chat_id, user_id=target, action="preban"
                ).where(
                    (db_management.ChatPreActionList.user_id == target)
                    & (db_management.ChatPreActionList.chat_id == chat_id)
                ).execute()
            else:
                db_management.ChatPreActionList.create(
                    chat_id=chat_id, user_id=target, action="preban"
                )
            text = _(chat_settings.language, "action_on_user").format(
                "#preban", target, reasons, executer, abs(chat_id)
            )

            utils.Log(
                client=client,
                chat_id=chat_id,
                executer=executer,
                action=text,
                target=target,
            )
            return text


def Unban(
    client: pyrogram.Client,
    executer: typing.Union[int, str],
    target: typing.Union[int, str],
    chat_id: typing.Union[int, str],
    reasons: str = "",
    r_executer_chat: db_management.RUserChat = None,
    r_target_chat: db_management.RUserChat = None,
    chat_settings: db_management.ChatSettings = None,
) -> str:
    r_executer_chat = r_executer_chat or db_management.RUserChat.get_or_none(
        user_id=executer, chat_id=chat_id
    )
    if not r_executer_chat:
        r_executer_chat = db_management.RUserChat.create(
            user_id=executer, chat_id=chat_id
        )
    r_target_chat = r_target_chat or db_management.RUserChat.get_or_none(
        user_id=target, chat_id=chat_id
    )
    if not r_target_chat:
        r_target_chat = db_management.RUserChat.create(user_id=target, chat_id=chat_id)
    chat_settings = chat_settings or db_management.ChatSettings.get_or_none(
        chat_id=chat_id
    )

    if not r_target_chat.is_whitelisted:
        if utils.CompareRanks(
            executer=executer,
            target=target,
            chat_id=chat_id,
            r_executer_chat=r_executer_chat,
            r_target_chat=r_target_chat,
            min_rank=dictionaries.RANKS["junior_mod"],
        ):
            text = ""
            try:
                client.unban_chat_member(chat_id=chat_id, user_id=target)
            except pyrogram.errors.FloodWait as ex:
                print(ex)
                traceback.print_exc()
                run_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=ex.x)
                utils.scheduler.add_job(
                    func=Unban,
                    kwargs=dict(
                        client=client,
                        executer=executer,
                        target=target,
                        chat_id=chat_id,
                        reasons=reasons,
                        r_executer_chat=r_executer_chat,
                        r_target_chat=r_target_chat,
                        chat_settings=chat_settings,
                    ),
                    trigger=DateTrigger(run_date=run_date),
                )
                text = _(chat_settings.language, "tg_flood_wait_X_scheduled_Y").format(
                    ex.x, f"UTC {run_date}"
                )
            except pyrogram.errors.RPCError as ex:
                print(ex)
                traceback.print_exc()
                text = _(chat_settings.language, "tg_error_X").format(ex)
            else:
                text = _(chat_settings.language, "action_on_user").format(
                    "#unban", target, reasons, executer, abs(chat_id)
                )

                utils.Log(
                    client=client,
                    chat_id=chat_id,
                    executer=executer,
                    action=text,
                    target=target,
                )
            return text


def GBan(
    client: pyrogram.Client,
    executer: typing.Union[int, str],
    target: typing.Union[int, str],
    chat_id: typing.Union[int, str],
    seconds: int = 86400,  # 1day
    reasons: str = "",
    chat_settings: typing.Union[
        db_management.ChatSettings, db_management.UserSettings
    ] = None,
    target_settings: db_management.UserSettings = None,
) -> str:
    if chat_id < 0:
        chat_settings = chat_settings or db_management.ChatSettings.get_or_none(
            chat_id=chat_id
        )
    else:
        chat_settings = chat_settings or db_management.UserSettings.get_or_none(
            user_id=chat_id
        )
        if not chat_settings:
            chat_settings = db_management.UserSettings.create(user_id=chat_id)
    target_settings = target_settings or db_management.UserSettings.get_or_none(
        user_id=target
    )
    if not target_settings:
        target_settings = db_management.UserSettings.create(user_id=target)

    if utils.CompareRanks(
        executer=executer,
        target=target,
        chat_id=chat_id,
        min_rank=dictionaries.RANKS["master"],
    ):
        today = datetime.date.today()
        expiration = today + datetime.timedelta(seconds=seconds)
        target_settings.global_ban_counter += 1
        target_settings.global_ban_date = today
        target_settings.global_ban_expiration = expiration
        target_settings.save()
        utc_timestamp_expiration = datetime.datetime.utcfromtimestamp(
            datetime.datetime.combine(expiration, datetime.time.min)
            .replace(tzinfo=datetime.timezone.utc)
            .timestamp()
        )
        text = _(chat_settings.language, "action_on_user").format(
            "#gban "
            + _(chat_settings.language, "until")
            + f" UTC {utc_timestamp_expiration}",
            target,
            reasons,
            executer,
            abs(chat_id),
        )

        utils.Log(
            client=client,
            chat_id=client.ME.id,
            executer=executer,
            action=text,
            target=target,
        )
        SendMessage(
            client=client, chat_id=utils.config["settings"]["log_chat"], text=text
        )
        return text


def Ungban(
    client: pyrogram.Client,
    executer: typing.Union[int, str],
    target: typing.Union[int, str],
    chat_id: typing.Union[int, str],
    reasons: str = "",
    chat_settings: typing.Union[
        db_management.ChatSettings, db_management.UserSettings
    ] = None,
    target_settings: db_management.UserSettings = None,
) -> str:
    if chat_id < 0:
        chat_settings = chat_settings or db_management.ChatSettings.get_or_none(
            chat_id=chat_id
        )
    else:
        chat_settings = chat_settings or db_management.UserSettings.get_or_none(
            user_id=chat_id
        )
        if not chat_settings:
            chat_settings = db_management.UserSettings.create(user_id=chat_id)
    target_settings = target_settings or db_management.UserSettings.get_or_none(
        user_id=target
    )
    if not target_settings:
        target_settings = db_management.UserSettings.create(user_id=target)

    if utils.CompareRanks(
        executer=executer,
        target=target,
        chat_id=chat_id,
        min_rank=dictionaries.RANKS["master"],
    ):
        target_settings.global_ban_counter -= 1
        target_settings.global_ban_expiration = datetime.date.today()
        target_settings.save()
        text = _(chat_settings.language, "action_on_user").format(
            "#ungban", target, reasons, executer, abs(chat_id)
        )

        utils.Log(
            client=client,
            chat_id=client.ME.id,
            executer=executer,
            action=text,
            target=target,
        )
        SendMessage(
            client=client, chat_id=utils.config["settings"]["log_chat"], text=text
        )
        return text


def Block(
    client: pyrogram.Client,
    executer: typing.Union[int, str],
    target: typing.Union[int, str],
    chat_id: typing.Union[int, str],
    seconds: int = 3600,  # 1hour
    reasons: str = "",
    chat_settings: typing.Union[
        db_management.ChatSettings, db_management.UserSettings
    ] = None,
    target_settings: db_management.UserSettings = None,
) -> str:
    if chat_id < 0:
        chat_settings = chat_settings or db_management.ChatSettings.get_or_none(
            chat_id=chat_id
        )
    else:
        chat_settings = chat_settings or db_management.UserSettings.get_or_none(
            user_id=chat_id
        )
        if not chat_settings:
            chat_settings = db_management.UserSettings.create(user_id=chat_id)
    target_settings = target_settings or db_management.UserSettings.get_or_none(
        user_id=target
    )
    if not target_settings:
        target_settings = db_management.UserSettings.create(user_id=target)

    if utils.CompareRanks(
        executer=executer,
        target=target,
        chat_id=chat_id,
        min_rank=dictionaries.RANKS["master"],
    ):
        now = datetime.datetime.utcnow()
        expiration = now + datetime.timedelta(seconds=seconds)
        target_settings.block_counter += 1
        target_settings.block_datetime = now
        target_settings.block_expiration = expiration
        target_settings.save()
        text = _(chat_settings.language, "action_on_user").format(
            "#block " + _(chat_settings.language, "until") + f" UTC {expiration}",
            target,
            reasons,
            executer,
            abs(chat_id),
        )

        utils.Log(
            client=client,
            chat_id=client.ME.id,
            executer=executer,
            action=text,
            target=target,
        )
        SendMessage(
            client=client, chat_id=utils.config["settings"]["log_chat"], text=text
        )
        return text


def Unblock(
    client: pyrogram.Client,
    executer: typing.Union[int, str],
    target: typing.Union[int, str],
    chat_id: typing.Union[int, str],
    reasons: str = "",
    chat_settings: typing.Union[
        db_management.ChatSettings, db_management.UserSettings
    ] = None,
    target_settings: db_management.UserSettings = None,
) -> str:
    if chat_id < 0:
        chat_settings = chat_settings or db_management.ChatSettings.get_or_none(
            chat_id=chat_id
        )
    else:
        chat_settings = chat_settings or db_management.UserSettings.get_or_none(
            user_id=chat_id
        )
        if not chat_settings:
            chat_settings = db_management.UserSettings.create(user_id=chat_id)
    target_settings = target_settings or db_management.UserSettings.get_or_none(
        user_id=target
    )
    if not target_settings:
        target_settings = db_management.UserSettings.create(user_id=target)

    if utils.CompareRanks(
        executer=executer,
        target=target,
        chat_id=chat_id,
        min_rank=dictionaries.RANKS["master"],
    ):
        target_settings.block_counter -= 1
        target_settings.block_expiration = datetime.datetime.utcnow()
        target_settings.save()
        text = _(chat_settings.language, "action_on_user").format(
            "#unblock", target, reasons, executer, abs(chat_id)
        )

        utils.Log(
            client=client,
            chat_id=client.ME.id,
            executer=executer,
            action=text,
            target=target,
        )
        SendMessage(
            client=client, chat_id=utils.config["settings"]["log_chat"], text=text
        )
        return text


def AutoPunish(
    client: pyrogram.Client,
    executer: typing.Union[int, str],
    target: typing.Union[int, str],
    chat_id: typing.Union[int, str],
    punishment: int,
    reasons: typing.Union[typing.List[str], str] = None,
    message_ids: typing.Union[typing.List[int], int] = None,
    until_date: int = None,
    r_executer_chat: db_management.RUserChat = None,
    r_target_chat: db_management.RUserChat = None,
    chat_settings: db_management.ChatSettings = None,
    auto_group_notice: bool = False,
) -> str:
    if punishment:
        if not reasons:
            reasons = []
        if isinstance(reasons, str):
            reasons = [reasons]
        # set is used to remove duplicates
        reasons = list(set(reasons))

        r_executer_chat = r_executer_chat or db_management.RUserChat.get_or_none(
            user_id=executer, chat_id=chat_id
        )
        if not r_executer_chat:
            r_executer_chat = db_management.RUserChat.create(
                user_id=executer, chat_id=chat_id
            )
        r_target_chat = r_target_chat or db_management.RUserChat.get_or_none(
            user_id=target, chat_id=chat_id
        )
        if not r_target_chat:
            r_target_chat = db_management.RUserChat.create(
                user_id=target, chat_id=chat_id
            )
        chat_settings = chat_settings or db_management.ChatSettings.get_or_none(
            chat_id=chat_id
        )

        if not r_target_chat.is_whitelisted:
            if utils.CompareRanks(
                executer=executer,
                target=target,
                chat_id=chat_id,
                r_executer_chat=r_executer_chat,
                r_target_chat=r_target_chat,
                min_rank=dictionaries.RANKS["junior_mod"],
            ):
                now = int(time.time())
                hashtags = []

                if punishment >= 1 and message_ids:
                    # delete
                    if isinstance(message_ids, int):
                        message_ids = [message_ids]
                    message_ids = list(set(message_ids))
                    try:
                        client.delete_messages(chat_id=chat_id, message_ids=message_ids)
                        hashtags.append("#delete")
                    except pyrogram.errors.FloodWait as ex:
                        print(ex)
                        traceback.print_exc()
                        run_date = datetime.datetime.utcnow() + datetime.timedelta(
                            seconds=ex.x
                        )
                        utils.scheduler.add_job(
                            func=client.delete_messages,
                            kwargs=dict(chat_id=chat_id, message_ids=message_ids),
                            trigger=DateTrigger(run_date=run_date),
                        )
                        hashtags.append(f"#scheduleddelete UTC {run_date}")
                    except pyrogram.errors.RPCError as ex:
                        print(ex)
                        traceback.print_exc()
                        return _(chat_settings.language, "tg_error_X").format(ex)
                if punishment >= 2:
                    # warn
                    if chat_settings.max_warns_punishment:
                        if target not in utils.tmp_dicts["kickedPeople"][chat_id]:
                            # if user has not been kicked
                            # atomic update
                            db_management.RUserChat.update(
                                {
                                    db_management.RUserChat.warns: db_management.RUserChat.warns
                                    + 1
                                }
                            ).where(
                                (db_management.RUserChat.user == target)
                                & (db_management.RUserChat.chat == chat_id)
                            ).execute()
                            r_target_chat = db_management.RUserChat.get_or_none(
                                user_id=target, chat_id=chat_id
                            )
                            if r_target_chat.warns >= chat_settings.max_warns:
                                punishment = max(
                                    punishment, chat_settings.max_warns_punishment
                                )
                                reasons.append("max_warns_reached")
                                r_target_chat.warns = 0
                                r_target_chat.save()
                            hashtags.append(
                                f"#warn {r_target_chat.warns}/{chat_settings.max_warns}"
                            )
                if punishment == 3:
                    # kick
                    if target not in utils.tmp_dicts["kickedPeople"][chat_id]:
                        # if user has not been kicked
                        try:
                            client.kick_chat_member(
                                chat_id=chat_id, user_id=target, until_date=now + 35
                            )
                            hashtags.append("#kick")
                        except pyrogram.errors.FloodWait as ex:
                            print(ex)
                            traceback.print_exc()
                            run_date = datetime.datetime.utcnow() + datetime.timedelta(
                                seconds=ex.x
                            )
                            utils.scheduler.add_job(
                                func=client.kick_chat_member,
                                kwargs=dict(
                                    chat_id=chat_id,
                                    user_id=target,
                                    until_date=run_date
                                    + datetime.timedelta(seconds=35),
                                ),
                                trigger=DateTrigger(run_date=run_date),
                            )
                            hashtags.append(f"#scheduledkick UTC {run_date}")
                        except pyrogram.errors.RPCError as ex:
                            print(ex)
                            traceback.print_exc()
                            return _(chat_settings.language, "tg_error_X").format(ex)
                elif punishment == 4:
                    # temprestrict
                    if target not in utils.tmp_dicts["kickedPeople"][chat_id]:
                        # if user has not been kicked
                        until_date = (
                            until_date
                            if until_date is not None
                            else (now + chat_settings.max_temp_restrict)
                        )
                        try:
                            client.restrict_chat_member(
                                chat_id=chat_id,
                                user_id=target,
                                permissions=pyrogram.ChatPermissions(),
                                until_date=until_date,
                            )
                            hashtags.append(
                                "#temprestrict "
                                + _(chat_settings.language, "until")
                                + f" UTC {datetime.datetime.utcfromtimestamp(until_date)}"
                            )
                        except pyrogram.errors.FloodWait as ex:
                            print(ex)
                            traceback.print_exc()
                            run_date = datetime.datetime.utcnow() + datetime.timedelta(
                                seconds=ex.x
                            )
                            until_date += ex.x
                            utils.scheduler.add_job(
                                func=client.restrict_chat_member,
                                kwargs=dict(
                                    chat_id=chat_id,
                                    user_id=target,
                                    permissions=pyrogram.ChatPermissions(),
                                    until_date=until_date,
                                ),
                                trigger=DateTrigger(run_date=run_date),
                            )
                            hashtags.append(
                                f"#scheduledtemprestrict UTC {run_date} "
                                + _(chat_settings.language, "until")
                                + f" UTC {datetime.datetime.utcfromtimestamp(until_date)}"
                            )
                        except pyrogram.errors.RPCError as ex:
                            print(ex)
                            traceback.print_exc()
                            return _(chat_settings.language, "tg_error_X").format(ex)
                elif punishment == 5:
                    # restrict
                    if target not in utils.tmp_dicts["kickedPeople"][chat_id]:
                        # if user has not been kicked
                        try:
                            client.restrict_chat_member(
                                chat_id=chat_id,
                                user_id=target,
                                permissions=pyrogram.ChatPermissions(),
                            )
                            hashtags.append("#restrict")
                        except pyrogram.errors.FloodWait as ex:
                            print(ex)
                            traceback.print_exc()
                            run_date = datetime.datetime.utcnow() + datetime.timedelta(
                                seconds=ex.x
                            )
                            utils.scheduler.add_job(
                                func=client.restrict_chat_member,
                                kwargs=dict(
                                    chat_id=chat_id,
                                    user_id=target,
                                    permissions=pyrogram.ChatPermissions(),
                                ),
                                trigger=DateTrigger(run_date=run_date),
                            )
                            hashtags.append(f"#scheduledrestrict UTC {run_date}")
                        except pyrogram.errors.RPCError as ex:
                            print(ex)
                            traceback.print_exc()
                            return _(chat_settings.language, "tg_error_X").format(ex)
                elif punishment == 6:
                    # tempban
                    if target not in utils.tmp_dicts["kickedPeople"][chat_id]:
                        # if user has not been kicked
                        until_date = (
                            until_date
                            if until_date is not None
                            else (now + chat_settings.max_temp_restrict)
                        )
                        try:
                            client.kick_chat_member(
                                chat_id=chat_id, user_id=target, until_date=until_date
                            )
                            hashtags.append(
                                "#tempban "
                                + _(chat_settings.language, "until")
                                + f" UTC {datetime.datetime.utcfromtimestamp(until_date)}"
                            )
                        except pyrogram.errors.FloodWait as ex:
                            print(ex)
                            traceback.print_exc()
                            run_date = datetime.datetime.utcnow() + datetime.timedelta(
                                seconds=ex.x
                            )
                            until_date += ex.x
                            utils.scheduler.add_job(
                                func=client.kick_chat_member,
                                kwargs=dict(
                                    chat_id=chat_id,
                                    user_id=target,
                                    until_date=until_date,
                                ),
                                trigger=DateTrigger(run_date=run_date),
                            )
                            hashtags.append(
                                f"#scheduledtempban UTC {run_date} "
                                + _(chat_settings.language, "until")
                                + f" UTC {datetime.datetime.utcfromtimestamp(until_date)}"
                            )
                        except pyrogram.errors.RPCError as ex:
                            print(ex)
                            traceback.print_exc()
                            return _(chat_settings.language, "tg_error_X").format(ex)
                elif punishment == 7:
                    # ban
                    if target not in utils.tmp_dicts["kickedPeople"][chat_id]:
                        # if user has not been kicked
                        try:
                            client.kick_chat_member(chat_id=chat_id, user_id=target)
                            hashtags.append("#ban")
                        except pyrogram.errors.FloodWait as ex:
                            print(ex)
                            traceback.print_exc()
                            run_date = datetime.datetime.utcnow() + datetime.timedelta(
                                seconds=ex.x
                            )
                            utils.scheduler.add_job(
                                func=client.kick_chat_member,
                                kwargs=dict(chat_id=chat_id, user_id=target),
                                trigger=DateTrigger(run_date=run_date),
                            )
                            hashtags.append(f"#scheduledban UTC {run_date}")
                        except pyrogram.errors.RPCError as ex:
                            print(ex)
                            traceback.print_exc()
                            return _(chat_settings.language, "tg_error_X").format(ex)

                # retrieve reasons
                reasons = [_(chat_settings.language, f"reason_{x}") for x in reasons]
                hashtags.append("#automatic")
                hashtags.reverse()
                text = _(chat_settings.language, "action_on_user").format(
                    " ".join(hashtags),
                    target,
                    "\n".join(reasons),
                    executer,
                    abs(chat_id),
                )
                utils.Log(
                    client=client,
                    chat_id=chat_id,
                    executer=client.ME.id,
                    action=text,
                    target=target,
                    # don't send messages to log_channel for deletions
                    log_channel_notice=punishment > 1,
                )
                if (
                    auto_group_notice
                    and text
                    and chat_settings.group_notices
                    and chat_settings.group_notices <= punishment
                    and target not in utils.tmp_dicts["kickedPeople"][chat_id]
                ):
                    if punishment > 2:
                        utils.tmp_dicts["kickedPeople"][chat_id].add(target)
                    SendMessage(client=client, chat_id=chat_id, text=text)
                return text


def CallbackQueryAnswer(
    cb_qry: pyrogram.CallbackQuery,
    text: str = None,
    show_alert: bool = None,
    url: str = None,
    cache_time: int = 0,
) -> bool:
    try:
        cb_qry.answer(text=text, show_alert=show_alert, url=url, cache_time=cache_time)
    except pyrogram.errors.RPCError as ex:
        print(ex)
        traceback.print_exc()
        return False
    return True


def SendLog(
    client: pyrogram.Client,
    text: str,
    parse_mode: typing.Union[str, None] = object,
    disable_web_page_preview: bool = None,
    disable_notification: bool = None,
    reply_to_message_id: int = None,
    schedule_date: int = None,
    reply_markup: typing.Union[
        "pyrogram.InlineKeyboardMarkup",
        "pyrogram.ReplyKeyboardMarkup",
        "pyrogram.ReplyKeyboardRemove",
        "pyrogram.ForceReply",
    ] = None,
) -> typing.Union[pyrogram.Message, None]:
    try:
        return client.send_message(
            chat_id=utils.config["settings"]["log_chat"],
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            schedule_date=schedule_date,
            reply_markup=reply_markup,
        )
    except pyrogram.errors.FloodWait as ex:
        print(ex)
        traceback.print_exc()
        run_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=ex.x)
        utils.scheduler.add_job(
            func=SendLog,
            kwargs=dict(
                client=client,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                schedule_date=schedule_date,
                reply_markup=reply_markup,
            ),
            trigger=DateTrigger(run_date=run_date),
        )
    except pyrogram.errors.RPCError as ex:
        print(ex)
        traceback.print_exc()

    return None


def SendMessage(
    client: pyrogram.Client,
    chat_id: str,
    text: str,
    parse_mode: typing.Union[str, None] = object,
    disable_web_page_preview: bool = None,
    disable_notification: bool = None,
    reply_to_message_id: int = None,
    schedule_date: int = None,
    reply_markup: typing.Union[
        "pyrogram.InlineKeyboardMarkup",
        "pyrogram.ReplyKeyboardMarkup",
        "pyrogram.ReplyKeyboardRemove",
        "pyrogram.ForceReply",
    ] = None,
) -> typing.Union[pyrogram.Message, None]:
    if chat_id < 0:
        chat_settings = db_management.ChatSettings.get_or_none(chat_id=chat_id)
    else:
        chat_settings = db_management.UserSettings.get_or_none(user_id=chat_id)
        if not chat_settings:
            chat_settings = db_management.UserSettings.create(user_id=chat_id)
    try:
        client.send_chat_action(
            chat_id=chat_id, action="typing",
        )
    except pyrogram.errors.ChatWriteForbidden as ex:
        print(ex)
        traceback.print_exc()
        chat_settings.forbidden_writing_counter += 1
        chat_settings.save()
        if (
            chat_settings.forbidden_writing_counter
            >= utils.config["settings"]["max_forbidden_writing_counter"]
        ):
            client.leave_chat(chat_id=chat_id)
        client.send_message(
            chat_id=utils.config["settings"]["log_chat"],
            text=_("en", "tg_error_X").format(ex),
        )
    except pyrogram.errors.UserIsBlocked as ex:
        print(ex)
        traceback.print_exc()
        chat_settings.has_blocked_bot = True
        chat_settings.save()
    except pyrogram.errors.RPCError as ex:
        print(ex)
        traceback.print_exc()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=client.ME.id,
            action="send_chat_action",
        )
        client.send_message(
            chat_id=chat_id, text=_(chat_settings.language, "tg_error_X").format(ex)
        )
    else:
        try:
            return client.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                schedule_date=schedule_date,
                reply_markup=reply_markup,
            )
        except pyrogram.errors.FloodWait as ex:
            print(ex)
            traceback.print_exc()
            utils.scheduler.add_job(
                func=SendMessage,
                kwargs=dict(
                    client=client,
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_web_page_preview,
                    disable_notification=disable_notification,
                    reply_to_message_id=reply_to_message_id,
                    schedule_date=schedule_date,
                    reply_markup=reply_markup,
                ),
                trigger=DateTrigger(
                    run_date=datetime.datetime.now() + datetime.timedelta(seconds=ex.x)
                ),
            )
        except pyrogram.errors.RPCError as ex:
            print(ex)
            traceback.print_exc()
            utils.Log(
                client=client,
                chat_id=chat_id,
                executer=client.ME.id,
                action="send_message",
            )
            client.send_message(
                chat_id=chat_id,
                text=_(chat_settings.language, "tg_error_X").format(ex),
            )

    return None


def ReplyText(
    client: pyrogram.Client,
    msg: pyrogram.Message,
    text: str,
    parse_mode: typing.Union[str, None] = object,
    disable_web_page_preview: bool = None,
    disable_notification: bool = None,
    reply_to_message_id: int = None,
    reply_markup: typing.Union[
        "pyrogram.InlineKeyboardMarkup",
        "pyrogram.ReplyKeyboardMarkup",
        "pyrogram.ReplyKeyboardRemove",
        "pyrogram.ForceReply",
    ] = None,
) -> typing.Union[pyrogram.Message, None]:

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
            >= utils.config["settings"]["max_forbidden_writing_counter"]
        ):
            client.leave_chat(chat_id=msg.chat.id)
        client.send_message(
            chat_id=utils.config["settings"]["log_chat"],
            text=_("en", "tg_error_X").format(ex),
        )
    except pyrogram.errors.RPCError as ex:
        print(ex)
        traceback.print_exc()
        utils.Log(
            client=client,
            chat_id=msg.chat.id,
            executer=client.ME.id,
            action="send_chat_action",
        )
        msg.reply_text(text=_(msg.chat.settings.language, "tg_error_X").format(ex))
    else:
        try:
            return msg.reply_text(
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup,
            )
        except pyrogram.errors.FloodWait as ex:
            print(ex)
            traceback.print_exc()
            utils.scheduler.add_job(
                func=ReplyText,
                kwargs=dict(
                    client=client,
                    msg=msg,
                    text=text,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_web_page_preview,
                    disable_notification=disable_notification,
                    reply_to_message_id=reply_to_message_id,
                    reply_markup=reply_markup,
                ),
                trigger=DateTrigger(
                    run_date=datetime.datetime.now() + datetime.timedelta(seconds=ex.x)
                ),
            )
        except pyrogram.errors.RPCError as ex:
            print(ex)
            traceback.print_exc()
            utils.Log(
                client=client,
                chat_id=msg.chat.id,
                executer=client.ME.id,
                action="reply_text",
            )
            msg.reply_text(text=_(msg.chat.settings.language, "tg_error_X").format(ex))

    return None


def ReplyPhoto(
    client: pyrogram.Client,
    msg: pyrogram.Message,
    photo: str,
    caption: str = "",
    parse_mode: typing.Union[str, None] = object,
    disable_notification: bool = None,
    reply_to_message_id: int = None,
    reply_markup: typing.Union[
        "pyrogram.InlineKeyboardMarkup",
        "pyrogram.ReplyKeyboardMarkup",
        "pyrogram.ReplyKeyboardRemove",
        "pyrogram.ForceReply",
    ] = None,
) -> typing.Union[pyrogram.Message, None]:

    try:
        client.send_chat_action(
            chat_id=msg.chat.id, action="upload_photo",
        )
    except pyrogram.errors.ChatWriteForbidden as ex:
        print(ex)
        traceback.print_exc()
        msg.chat.settings.forbidden_writing_counter += 1
        msg.chat.settings.save()
        if (
            msg.chat.settings.forbidden_writing_counter
            >= utils.config["settings"]["max_forbidden_writing_counter"]
        ):
            client.leave_chat(chat_id=msg.chat.id)
        client.send_message(
            chat_id=utils.config["settings"]["log_chat"],
            text=_("en", "tg_error_X").format(ex),
        )
    except pyrogram.errors.RPCError as ex:
        print(ex)
        traceback.print_exc()
        utils.Log(
            client=client,
            chat_id=msg.chat.id,
            executer=client.ME.id,
            action="send_chat_action",
        )
        msg.reply_text(text=_(msg.chat.settings.language, "tg_error_X").format(ex))
    else:
        try:
            return msg.reply_photo(
                photo=photo,
                caption=caption,
                parse_mode=parse_mode,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup,
            )
        except pyrogram.errors.FloodWait as ex:
            print(ex)
            traceback.print_exc()
            utils.scheduler.add_job(
                func=ReplyPhoto,
                kwargs=dict(
                    client=client,
                    msg=msg,
                    photo=photo,
                    caption=caption,
                    parse_mode=parse_mode,
                    disable_notification=disable_notification,
                    reply_to_message_id=reply_to_message_id,
                    reply_markup=reply_markup,
                ),
                trigger=DateTrigger(
                    run_date=datetime.datetime.now() + datetime.timedelta(seconds=ex.x)
                ),
            )
        except pyrogram.errors.RPCError as ex:
            print(ex)
            traceback.print_exc()
            utils.Log(
                client=client,
                chat_id=msg.chat.id,
                executer=client.ME.id,
                action="reply_photo",
            )
            msg.reply_text(text=_(msg.chat.settings.language, "tg_error_X").format(ex))

    return None


def SendDocument(
    client: pyrogram.Client,
    chat_id: str,
    document: str,
    caption: str = "",
    parse_mode: typing.Union[str, None] = object,
    disable_notification: bool = None,
    reply_to_message_id: int = None,
    schedule_date: int = None,
    reply_markup: typing.Union[
        "pyrogram.InlineKeyboardMarkup",
        "pyrogram.ReplyKeyboardMarkup",
        "pyrogram.ReplyKeyboardRemove",
        "pyrogram.ForceReply",
    ] = None,
    progress: callable = None,
    progress_args: tuple = (),
) -> typing.Union[pyrogram.Message, None]:
    if chat_id < 0:
        chat_settings = db_management.ChatSettings.get_or_none(chat_id=chat_id)
    else:
        chat_settings = db_management.UserSettings.get_or_none(user_id=chat_id)
        if not chat_settings:
            chat_settings = db_management.UserSettings.create(user_id=chat_id)
    try:
        client.send_chat_action(
            chat_id=chat_id, action="upload_document",
        )
    except pyrogram.errors.ChatWriteForbidden as ex:
        print(ex)
        traceback.print_exc()
        chat_settings.forbidden_writing_counter += 1
        chat_settings.save()
        if (
            chat_settings.forbidden_writing_counter
            >= utils.config["settings"]["max_forbidden_writing_counter"]
        ):
            client.leave_chat(chat_id=chat_id)
        client.send_message(
            chat_id=utils.config["settings"]["log_chat"],
            text=_("en", "tg_error_X").format(ex),
        )
    except pyrogram.errors.RPCError as ex:
        print(ex)
        traceback.print_exc()
        utils.Log(
            client=client,
            chat_id=chat_id,
            executer=client.ME.id,
            action="send_chat_action",
        )
        client.send_message(
            chat_id=chat_id, text=_(chat_settings.language, "tg_error_X").format(ex)
        )
    else:
        try:
            return client.send_document(
                chat_id=chat_id,
                document=document,
                caption=caption,
                parse_mode=parse_mode,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                schedule_date=schedule_date,
                reply_markup=reply_markup,
                progress=progress,
                progress_args=progress_args,
            )
        except pyrogram.errors.FloodWait as ex:
            print(ex)
            traceback.print_exc()
            utils.scheduler.add_job(
                func=SendDocument,
                kwargs=dict(
                    client=client,
                    chat_id=chat_id,
                    document=document,
                    caption=caption,
                    parse_mode=parse_mode,
                    disable_notification=disable_notification,
                    reply_to_message_id=reply_to_message_id,
                    schedule_date=schedule_date,
                    reply_markup=reply_markup,
                    progress=progress,
                    progress_args=progress_args,
                ),
                trigger=DateTrigger(
                    run_date=datetime.datetime.now() + datetime.timedelta(seconds=ex.x)
                ),
            )
        except pyrogram.errors.RPCError as ex:
            print(ex)
            traceback.print_exc()
            utils.Log(
                client=client,
                chat_id=chat_id,
                executer=client.ME.id,
                action="send_document",
            )
            client.send_message(
                chat_id=chat_id,
                text=_(chat_settings.language, "tg_error_X").format(ex),
            )

    return None


def ReplyDocument(
    client: pyrogram.Client,
    msg: pyrogram.Message,
    document: str,
    caption: str = "",
    parse_mode: typing.Union[str, None] = object,
    disable_notification: bool = None,
    reply_to_message_id: int = None,
    reply_markup: typing.Union[
        "pyrogram.InlineKeyboardMarkup",
        "pyrogram.ReplyKeyboardMarkup",
        "pyrogram.ReplyKeyboardRemove",
        "pyrogram.ForceReply",
    ] = None,
    progress: callable = None,
    progress_args: tuple = (),
) -> typing.Union[pyrogram.Message, None]:

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
            >= utils.config["settings"]["max_forbidden_writing_counter"]
        ):
            client.leave_chat(chat_id=msg.chat.id)
        client.send_message(
            chat_id=utils.config["settings"]["log_chat"],
            text=_("en", "tg_error_X").format(ex),
        )
    except pyrogram.errors.RPCError as ex:
        print(ex)
        traceback.print_exc()
        utils.Log(
            client=client,
            chat_id=msg.chat.id,
            executer=client.ME.id,
            action="send_chat_action",
        )
        msg.reply_text(text=_(msg.chat.settings.language, "tg_error_X").format(ex))
    else:
        try:
            return msg.reply_document(
                document=document,
                caption=caption,
                parse_mode=parse_mode,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup,
                progress=progress,
                progress_args=progress_args,
            )
        except pyrogram.errors.FloodWait as ex:
            print(ex)
            traceback.print_exc()
            utils.scheduler.add_job(
                func=ReplyDocument,
                kwargs=dict(
                    client=client,
                    msg=msg,
                    document=document,
                    caption=caption,
                    parse_mode=parse_mode,
                    disable_notification=disable_notification,
                    reply_to_message_id=reply_to_message_id,
                    reply_markup=reply_markup,
                    progress=progress,
                    progress_args=progress_args,
                ),
                trigger=DateTrigger(
                    run_date=datetime.datetime.now() + datetime.timedelta(seconds=ex.x)
                ),
            )
        except pyrogram.errors.RPCError as ex:
            print(ex)
            traceback.print_exc()
            utils.Log(
                client=client,
                chat_id=msg.chat.id,
                executer=client.ME.id,
                action="reply_document",
            )
            msg.reply_text(text=_(msg.chat.settings.language, "tg_error_X").format(ex))

    return None


def SendBackup(client: pyrogram.Client):
    tmp_msgs = {}
    for id_ in utils.config["masters"]:
        try:
            tmp_msgs[id_] = client.send_message(
                chat_id=id_, text=_("en", "automatic_backup"), disable_notification=True
            )
        except pyrogram.errors.RPCError as ex:
            print(ex)
            traceback.print_exc()

    backup_name = utils.Backup()

    for id_ in tmp_msgs.keys():
        SendDocument(
            client=client,
            chat_id=id_,
            document=backup_name,
            disable_notification=True,
            progress=utils.DFromUToTelegramProgress,
            progress_args=(tmp_msgs[id_], _("en", "sending_backup"), time.time(),),
        )
