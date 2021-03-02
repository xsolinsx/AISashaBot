import datetime

import db_management
import methods
import pyrogram
import utils
from apscheduler.triggers.date import DateTrigger
from pytz import utc

_ = utils.GetLocalizedString


def MultipleFunctionExecution(
    msg: pyrogram.types.Message,
    value: str,
    func: callable,
    func_kwargs: dict,
):
    user_id = utils.ResolveCommandToId(
        client=func_kwargs["client"], value=value, msg=msg
    )
    if isinstance(user_id, str):
        utils.Log(
            client=func_kwargs["client"],
            chat_id=func_kwargs["chat_id"],
            executer=msg.from_user.id,
            action=f"{msg.command[0]} on {value} resulted in {user_id}",
            target=value,
        )
    else:
        func(target=user_id, **func_kwargs)


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["multipleinvite"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
def CmdMultipleInviteUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    if utils.IsSeniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        run_date = None
        for i, user in enumerate(msg.command[1:]):
            # execute at intervals of 5 seconds (max 12 users per minute)
            run_date = datetime.datetime.utcnow() + datetime.timedelta(
                seconds=(i + 1) * 5
            )
            utils.scheduler.add_job(
                func=MultipleFunctionExecution,
                trigger=DateTrigger(run_date=run_date, timezone=utc),
                kwargs=dict(
                    msg=msg,
                    value=user,
                    func=methods.Invite,
                    func_kwargs=dict(
                        client=client,
                        executer=msg.from_user.id,
                        chat_id=msg.chat.id,
                        r_executer_chat=msg.r_user_chat,
                        chat_settings=msg.chat.settings,
                    ),
                ),
            )
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "processing_multiple_command")
            + "\n"
            + _(msg.chat.settings.language, "estimated_completion_time_X").format(
                run_date
            ),
        )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["multipleinvite"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
def CmdMultipleInviteChatUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = (
            db_management.ChatSettings.get_or_none(chat_id=chat_id)
        )
        if chat_settings:
            r_executer_chat = db_management.RUserChat.get_or_none(
                user_id=msg.from_user.id, chat_id=chat_id
            )
            if not r_executer_chat:
                r_executer_chat = db_management.RUserChat.create(
                    user_id=msg.from_user.id, chat_id=chat_id
                )
            if utils.IsSeniorModOrHigher(
                user_id=msg.from_user.id, chat_id=chat_id, r_user_chat=r_executer_chat
            ):
                run_date = None
                for i, user in enumerate(msg.command[2:]):
                    # execute at intervals of 5 seconds (max 12 users per minute)
                    run_date = datetime.datetime.utcnow() + datetime.timedelta(
                        seconds=(i + 1) * 5
                    )
                    utils.scheduler.add_job(
                        func=MultipleFunctionExecution,
                        trigger=DateTrigger(run_date=run_date, timezone=utc),
                        kwargs=dict(
                            msg=msg,
                            value=user,
                            func=methods.Invite,
                            func_kwargs=dict(
                                client=client,
                                executer=msg.from_user.id,
                                chat_id=chat_id,
                                r_executer_chat=r_executer_chat,
                                chat_settings=chat_settings,
                            ),
                        ),
                    )
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(chat_settings.language, "processing_multiple_command")
                    + "\n"
                    + _(chat_settings.language, "estimated_completion_time_X").format(
                        run_date
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
        commands=utils.GetCommandsVariants(commands=["multiplewarn"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
def CmdMultipleWarnUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    if utils.IsSeniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        run_date = None
        for i, user in enumerate(msg.command[1:]):
            # execute at intervals of 5 seconds (max 12 users per minute)
            run_date = datetime.datetime.utcnow() + datetime.timedelta(
                seconds=(i + 1) * 5
            )
            utils.scheduler.add_job(
                func=MultipleFunctionExecution,
                trigger=DateTrigger(run_date=run_date, timezone=utc),
                kwargs=dict(
                    msg=msg,
                    value=user,
                    func=methods.Warn,
                    func_kwargs=dict(
                        client=client,
                        executer=msg.from_user.id,
                        chat_id=msg.chat.id,
                        r_executer_chat=msg.r_user_chat,
                        chat_settings=msg.chat.settings,
                    ),
                ),
            )
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "processing_multiple_command")
            + "\n"
            + _(msg.chat.settings.language, "estimated_completion_time_X").format(
                run_date
            ),
        )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["multiplewarn"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
def CmdMultipleWarnChatUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = (
            db_management.ChatSettings.get_or_none(chat_id=chat_id)
        )
        if chat_settings:
            r_executer_chat = db_management.RUserChat.get_or_none(
                user_id=msg.from_user.id, chat_id=chat_id
            )
            if not r_executer_chat:
                r_executer_chat = db_management.RUserChat.create(
                    user_id=msg.from_user.id, chat_id=chat_id
                )
            if utils.IsSeniorModOrHigher(
                user_id=msg.from_user.id, chat_id=chat_id, r_user_chat=r_executer_chat
            ):
                run_date = None
                for i, user in enumerate(msg.command[2:]):
                    # execute at intervals of 5 seconds (max 12 users per minute)
                    run_date = datetime.datetime.utcnow() + datetime.timedelta(
                        seconds=(i + 1) * 5
                    )
                    utils.scheduler.add_job(
                        func=MultipleFunctionExecution,
                        trigger=DateTrigger(run_date=run_date, timezone=utc),
                        kwargs=dict(
                            msg=msg,
                            value=user,
                            func=methods.Warn,
                            func_kwargs=dict(
                                client=client,
                                executer=msg.from_user.id,
                                chat_id=chat_id,
                                r_executer_chat=r_executer_chat,
                                chat_settings=chat_settings,
                            ),
                        ),
                    )
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(chat_settings.language, "processing_multiple_command")
                    + "\n"
                    + _(chat_settings.language, "estimated_completion_time_X").format(
                        run_date
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
        commands=utils.GetCommandsVariants(commands=["multipleunwarn"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
def CmdMultipleUnwarnUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    if utils.IsSeniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        run_date = None
        for i, user in enumerate(msg.command[1:]):
            # execute at intervals of 5 seconds (max 12 users per minute)
            run_date = datetime.datetime.utcnow() + datetime.timedelta(
                seconds=(i + 1) * 5
            )
            utils.scheduler.add_job(
                func=MultipleFunctionExecution,
                trigger=DateTrigger(run_date=run_date, timezone=utc),
                kwargs=dict(
                    msg=msg,
                    value=user,
                    func=methods.Unwarn,
                    func_kwargs=dict(
                        client=client,
                        executer=msg.from_user.id,
                        chat_id=msg.chat.id,
                        r_executer_chat=msg.r_user_chat,
                        chat_settings=msg.chat.settings,
                    ),
                ),
            )
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "processing_multiple_command")
            + "\n"
            + _(msg.chat.settings.language, "estimated_completion_time_X").format(
                run_date
            ),
        )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["multipleunwarn"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
def CmdMultipleUnwarnChatUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = (
            db_management.ChatSettings.get_or_none(chat_id=chat_id)
        )
        if chat_settings:
            r_executer_chat = db_management.RUserChat.get_or_none(
                user_id=msg.from_user.id, chat_id=chat_id
            )
            if not r_executer_chat:
                r_executer_chat = db_management.RUserChat.create(
                    user_id=msg.from_user.id, chat_id=chat_id
                )
            if utils.IsSeniorModOrHigher(
                user_id=msg.from_user.id, chat_id=chat_id, r_user_chat=r_executer_chat
            ):
                run_date = None
                for i, user in enumerate(msg.command[2:]):
                    # execute at intervals of 5 seconds (max 12 users per minute)
                    run_date = datetime.datetime.utcnow() + datetime.timedelta(
                        seconds=(i + 1) * 5
                    )
                    utils.scheduler.add_job(
                        func=MultipleFunctionExecution,
                        trigger=DateTrigger(run_date=run_date, timezone=utc),
                        kwargs=dict(
                            msg=msg,
                            value=user,
                            func=methods.Unwarn,
                            func_kwargs=dict(
                                client=client,
                                executer=msg.from_user.id,
                                chat_id=chat_id,
                                r_executer_chat=r_executer_chat,
                                chat_settings=chat_settings,
                            ),
                        ),
                    )
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(chat_settings.language, "processing_multiple_command")
                    + "\n"
                    + _(chat_settings.language, "estimated_completion_time_X").format(
                        run_date
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
        commands=utils.GetCommandsVariants(commands=["multipleunwarnall"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
def CmdMultipleUnwarnAllUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    if utils.IsSeniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        run_date = None
        for i, user in enumerate(msg.command[1:]):
            # execute at intervals of 5 seconds (max 12 users per minute)
            run_date = datetime.datetime.utcnow() + datetime.timedelta(
                seconds=(i + 1) * 5
            )
            utils.scheduler.add_job(
                func=MultipleFunctionExecution,
                trigger=DateTrigger(run_date=run_date, timezone=utc),
                kwargs=dict(
                    msg=msg,
                    value=user,
                    func=methods.UnwarnAll,
                    func_kwargs=dict(
                        client=client,
                        executer=msg.from_user.id,
                        chat_id=msg.chat.id,
                        r_executer_chat=msg.r_user_chat,
                        chat_settings=msg.chat.settings,
                    ),
                ),
            )
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "processing_multiple_command")
            + "\n"
            + _(msg.chat.settings.language, "estimated_completion_time_X").format(
                run_date
            ),
        )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["multipleunwarnall"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
def CmdMultipleUnwarnAllChatUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = (
            db_management.ChatSettings.get_or_none(chat_id=chat_id)
        )
        if chat_settings:
            r_executer_chat = db_management.RUserChat.get_or_none(
                user_id=msg.from_user.id, chat_id=chat_id
            )
            if not r_executer_chat:
                r_executer_chat = db_management.RUserChat.create(
                    user_id=msg.from_user.id, chat_id=chat_id
                )
            if utils.IsSeniorModOrHigher(
                user_id=msg.from_user.id, chat_id=chat_id, r_user_chat=r_executer_chat
            ):
                run_date = None
                for i, user in enumerate(msg.command[2:]):
                    # execute at intervals of 5 seconds (max 12 users per minute)
                    run_date = datetime.datetime.utcnow() + datetime.timedelta(
                        seconds=(i + 1) * 5
                    )
                    utils.scheduler.add_job(
                        func=MultipleFunctionExecution,
                        trigger=DateTrigger(run_date=run_date, timezone=utc),
                        kwargs=dict(
                            msg=msg,
                            value=user,
                            func=methods.UnwarnAll,
                            func_kwargs=dict(
                                client=client,
                                executer=msg.from_user.id,
                                chat_id=chat_id,
                                r_executer_chat=r_executer_chat,
                                chat_settings=chat_settings,
                            ),
                        ),
                    )
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(chat_settings.language, "processing_multiple_command")
                    + "\n"
                    + _(chat_settings.language, "estimated_completion_time_X").format(
                        run_date
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
        commands=utils.GetCommandsVariants(commands=["multiplekick"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
def CmdMultipleKickUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    if utils.IsSeniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        run_date = None
        for i, user in enumerate(msg.command[1:]):
            # execute at intervals of 5 seconds (max 12 users per minute)
            run_date = datetime.datetime.utcnow() + datetime.timedelta(
                seconds=(i + 1) * 5
            )
            utils.scheduler.add_job(
                func=MultipleFunctionExecution,
                trigger=DateTrigger(run_date=run_date, timezone=utc),
                kwargs=dict(
                    msg=msg,
                    value=user,
                    func=methods.Kick,
                    func_kwargs=dict(
                        client=client,
                        executer=msg.from_user.id,
                        chat_id=msg.chat.id,
                        r_executer_chat=msg.r_user_chat,
                        chat_settings=msg.chat.settings,
                    ),
                ),
            )
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "processing_multiple_command")
            + "\n"
            + _(msg.chat.settings.language, "estimated_completion_time_X").format(
                run_date
            ),
        )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["multiplekick"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
def CmdMultipleKickChatUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = (
            db_management.ChatSettings.get_or_none(chat_id=chat_id)
        )
        if chat_settings:
            r_executer_chat = db_management.RUserChat.get_or_none(
                user_id=msg.from_user.id, chat_id=chat_id
            )
            if not r_executer_chat:
                r_executer_chat = db_management.RUserChat.create(
                    user_id=msg.from_user.id, chat_id=chat_id
                )
            if utils.IsSeniorModOrHigher(
                user_id=msg.from_user.id, chat_id=chat_id, r_user_chat=r_executer_chat
            ):
                run_date = None
                for i, user in enumerate(msg.command[2:]):
                    # execute at intervals of 5 seconds (max 12 users per minute)
                    run_date = datetime.datetime.utcnow() + datetime.timedelta(
                        seconds=(i + 1) * 5
                    )
                    utils.scheduler.add_job(
                        func=MultipleFunctionExecution,
                        trigger=DateTrigger(run_date=run_date, timezone=utc),
                        kwargs=dict(
                            msg=msg,
                            value=user,
                            func=methods.Kick,
                            func_kwargs=dict(
                                client=client,
                                executer=msg.from_user.id,
                                chat_id=chat_id,
                                r_executer_chat=r_executer_chat,
                                chat_settings=chat_settings,
                            ),
                        ),
                    )
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(chat_settings.language, "processing_multiple_command")
                    + "\n"
                    + _(chat_settings.language, "estimated_completion_time_X").format(
                        run_date
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
        commands=utils.GetCommandsVariants(
            commands=["multipletemprestrict"], del_=True
        ),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
def CmdMultipleTempRestrictUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    if utils.IsSeniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        run_date = None
        for i, user in enumerate(msg.command[1:]):
            # execute at intervals of 5 seconds (max 12 users per minute)
            run_date = datetime.datetime.utcnow() + datetime.timedelta(
                seconds=(i + 1) * 5
            )
            utils.scheduler.add_job(
                func=MultipleFunctionExecution,
                trigger=DateTrigger(run_date=run_date, timezone=utc),
                kwargs=dict(
                    msg=msg,
                    value=user,
                    func=methods.Restrict,
                    func_kwargs=dict(
                        client=client,
                        executer=msg.from_user.id,
                        chat_id=msg.chat.id,
                        until_date=int(run_date.timestamp())
                        + msg.chat.settings.max_temp_restrict,
                        r_executer_chat=msg.r_user_chat,
                        chat_settings=msg.chat.settings,
                    ),
                ),
            )
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "processing_multiple_command")
            + "\n"
            + _(msg.chat.settings.language, "estimated_completion_time_X").format(
                run_date
            ),
        )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(
            commands=["multipletemprestrict"], del_=True
        ),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
def CmdMultipleTempRestrictChatUser(
    client: pyrogram.Client, msg: pyrogram.types.Message
):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = (
            db_management.ChatSettings.get_or_none(chat_id=chat_id)
        )
        if chat_settings:
            r_executer_chat = db_management.RUserChat.get_or_none(
                user_id=msg.from_user.id, chat_id=chat_id
            )
            if not r_executer_chat:
                r_executer_chat = db_management.RUserChat.create(
                    user_id=msg.from_user.id, chat_id=chat_id
                )
            if utils.IsSeniorModOrHigher(
                user_id=msg.from_user.id, chat_id=chat_id, r_user_chat=r_executer_chat
            ):
                run_date = None
                for i, user in enumerate(msg.command[2:]):
                    # execute at intervals of 5 seconds (max 12 users per minute)
                    run_date = datetime.datetime.utcnow() + datetime.timedelta(
                        seconds=(i + 1) * 5
                    )
                    utils.scheduler.add_job(
                        func=MultipleFunctionExecution,
                        trigger=DateTrigger(run_date=run_date, timezone=utc),
                        kwargs=dict(
                            msg=msg,
                            value=user,
                            func=methods.Restrict,
                            func_kwargs=dict(
                                client=client,
                                executer=msg.from_user.id,
                                chat_id=chat_id,
                                until_date=int(run_date.timestamp())
                                + chat_settings.max_temp_restrict,
                                r_executer_chat=r_executer_chat,
                                chat_settings=chat_settings,
                            ),
                        ),
                    )
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(chat_settings.language, "processing_multiple_command")
                    + "\n"
                    + _(chat_settings.language, "estimated_completion_time_X").format(
                        run_date
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
        commands=utils.GetCommandsVariants(commands=["multiplerestrict"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
def CmdMultipleRestrictUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    if utils.IsSeniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        run_date = None
        for i, user in enumerate(msg.command[1:]):
            # execute at intervals of 5 seconds (max 12 users per minute)
            run_date = datetime.datetime.utcnow() + datetime.timedelta(
                seconds=(i + 1) * 5
            )
            utils.scheduler.add_job(
                func=MultipleFunctionExecution,
                trigger=DateTrigger(run_date=run_date, timezone=utc),
                kwargs=dict(
                    msg=msg,
                    value=user,
                    func=methods.Restrict,
                    func_kwargs=dict(
                        client=client,
                        executer=msg.from_user.id,
                        chat_id=msg.chat.id,
                        r_executer_chat=msg.r_user_chat,
                        chat_settings=msg.chat.settings,
                    ),
                ),
            )
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "processing_multiple_command")
            + "\n"
            + _(msg.chat.settings.language, "estimated_completion_time_X").format(
                run_date
            ),
        )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["multiplerestrict"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
def CmdMultipleRestrictChatUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = (
            db_management.ChatSettings.get_or_none(chat_id=chat_id)
        )
        if chat_settings:
            r_executer_chat = db_management.RUserChat.get_or_none(
                user_id=msg.from_user.id, chat_id=chat_id
            )
            if not r_executer_chat:
                r_executer_chat = db_management.RUserChat.create(
                    user_id=msg.from_user.id, chat_id=chat_id
                )
            if utils.IsSeniorModOrHigher(
                user_id=msg.from_user.id, chat_id=chat_id, r_user_chat=r_executer_chat
            ):
                run_date = None
                for i, user in enumerate(msg.command[2:]):
                    # execute at intervals of 5 seconds (max 12 users per minute)
                    run_date = datetime.datetime.utcnow() + datetime.timedelta(
                        seconds=(i + 1) * 5
                    )
                    utils.scheduler.add_job(
                        func=MultipleFunctionExecution,
                        trigger=DateTrigger(run_date=run_date, timezone=utc),
                        kwargs=dict(
                            msg=msg,
                            value=user,
                            func=methods.Restrict,
                            func_kwargs=dict(
                                client=client,
                                executer=msg.from_user.id,
                                chat_id=chat_id,
                                r_executer_chat=r_executer_chat,
                                chat_settings=chat_settings,
                            ),
                        ),
                    )
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(chat_settings.language, "processing_multiple_command")
                    + "\n"
                    + _(chat_settings.language, "estimated_completion_time_X").format(
                        run_date
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
        commands=utils.GetCommandsVariants(commands=["multipleunrestrict"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
def CmdMultipleUnrestrictUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    if utils.IsSeniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        run_date = None
        for i, user in enumerate(msg.command[1:]):
            # execute at intervals of 5 seconds (max 12 users per minute)
            run_date = datetime.datetime.utcnow() + datetime.timedelta(
                seconds=(i + 1) * 5
            )
            utils.scheduler.add_job(
                func=MultipleFunctionExecution,
                trigger=DateTrigger(run_date=run_date, timezone=utc),
                kwargs=dict(
                    msg=msg,
                    value=user,
                    func=methods.Unrestrict,
                    func_kwargs=dict(
                        client=client,
                        executer=msg.from_user.id,
                        chat_id=msg.chat.id,
                        r_executer_chat=msg.r_user_chat,
                        chat_settings=msg.chat.settings,
                    ),
                ),
            )
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "processing_multiple_command")
            + "\n"
            + _(msg.chat.settings.language, "estimated_completion_time_X").format(
                run_date
            ),
        )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["multipleunrestrict"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
def CmdMultipleUnrestrictChatUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = (
            db_management.ChatSettings.get_or_none(chat_id=chat_id)
        )
        if chat_settings:
            r_executer_chat = db_management.RUserChat.get_or_none(
                user_id=msg.from_user.id, chat_id=chat_id
            )
            if not r_executer_chat:
                r_executer_chat = db_management.RUserChat.create(
                    user_id=msg.from_user.id, chat_id=chat_id
                )
            if utils.IsSeniorModOrHigher(
                user_id=msg.from_user.id, chat_id=chat_id, r_user_chat=r_executer_chat
            ):
                run_date = None
                for i, user in enumerate(msg.command[2:]):
                    # execute at intervals of 5 seconds (max 12 users per minute)
                    run_date = datetime.datetime.utcnow() + datetime.timedelta(
                        seconds=(i + 1) * 5
                    )
                    utils.scheduler.add_job(
                        func=MultipleFunctionExecution,
                        trigger=DateTrigger(run_date=run_date, timezone=utc),
                        kwargs=dict(
                            msg=msg,
                            value=user,
                            func=methods.Unrestrict,
                            func_kwargs=dict(
                                client=client,
                                executer=msg.from_user.id,
                                chat_id=chat_id,
                                r_executer_chat=r_executer_chat,
                                chat_settings=chat_settings,
                            ),
                        ),
                    )
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(chat_settings.language, "processing_multiple_command")
                    + "\n"
                    + _(chat_settings.language, "estimated_completion_time_X").format(
                        run_date
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
        commands=utils.GetCommandsVariants(commands=["multipletempban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
def CmdMultipleTempBanUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    if utils.IsSeniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        run_date = None
        for i, user in enumerate(msg.command[1:]):
            # execute at intervals of 5 seconds (max 12 users per minute)
            run_date = datetime.datetime.utcnow() + datetime.timedelta(
                seconds=(i + 1) * 5
            )
            utils.scheduler.add_job(
                func=MultipleFunctionExecution,
                trigger=DateTrigger(run_date=run_date, timezone=utc),
                kwargs=dict(
                    msg=msg,
                    value=user,
                    func=methods.Ban,
                    func_kwargs=dict(
                        client=client,
                        executer=msg.from_user.id,
                        chat_id=msg.chat.id,
                        until_date=int(run_date.timestamp())
                        + msg.chat.settings.max_temp_ban,
                        r_executer_chat=msg.r_user_chat,
                        chat_settings=msg.chat.settings,
                    ),
                ),
            )
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "processing_multiple_command")
            + "\n"
            + _(msg.chat.settings.language, "estimated_completion_time_X").format(
                run_date
            ),
        )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["multipletempban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
def CmdMultipleTempBanChatUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = (
            db_management.ChatSettings.get_or_none(chat_id=chat_id)
        )
        if chat_settings:
            r_executer_chat = db_management.RUserChat.get_or_none(
                user_id=msg.from_user.id, chat_id=chat_id
            )
            if not r_executer_chat:
                r_executer_chat = db_management.RUserChat.create(
                    user_id=msg.from_user.id, chat_id=chat_id
                )
            if utils.IsSeniorModOrHigher(
                user_id=msg.from_user.id, chat_id=chat_id, r_user_chat=r_executer_chat
            ):
                run_date = None
                for i, user in enumerate(msg.command[2:]):
                    # execute at intervals of 5 seconds (max 12 users per minute)
                    run_date = datetime.datetime.utcnow() + datetime.timedelta(
                        seconds=(i + 1) * 5
                    )
                    utils.scheduler.add_job(
                        func=MultipleFunctionExecution,
                        trigger=DateTrigger(run_date=run_date, timezone=utc),
                        kwargs=dict(
                            msg=msg,
                            value=user,
                            func=methods.Ban,
                            func_kwargs=dict(
                                client=client,
                                executer=msg.from_user.id,
                                chat_id=chat_id,
                                until_date=int(run_date.timestamp())
                                + chat_settings.max_temp_ban,
                                r_executer_chat=r_executer_chat,
                                chat_settings=chat_settings,
                            ),
                        ),
                    )
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(chat_settings.language, "processing_multiple_command")
                    + "\n"
                    + _(chat_settings.language, "estimated_completion_time_X").format(
                        run_date
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
        commands=utils.GetCommandsVariants(commands=["multipleban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
def CmdMultipleBanUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    if utils.IsSeniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        run_date = None
        for i, user in enumerate(msg.command[1:]):
            # execute at intervals of 5 seconds (max 12 users per minute)
            run_date = datetime.datetime.utcnow() + datetime.timedelta(
                seconds=(i + 1) * 5
            )
            utils.scheduler.add_job(
                func=MultipleFunctionExecution,
                trigger=DateTrigger(run_date=run_date, timezone=utc),
                kwargs=dict(
                    msg=msg,
                    value=user,
                    func=methods.Ban,
                    func_kwargs=dict(
                        client=client,
                        executer=msg.from_user.id,
                        chat_id=msg.chat.id,
                        r_executer_chat=msg.r_user_chat,
                        chat_settings=msg.chat.settings,
                    ),
                ),
            )
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "processing_multiple_command")
            + "\n"
            + _(msg.chat.settings.language, "estimated_completion_time_X").format(
                run_date
            ),
        )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["multipleban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
def CmdMultipleBanChatUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = (
            db_management.ChatSettings.get_or_none(chat_id=chat_id)
        )
        if chat_settings:
            r_executer_chat = db_management.RUserChat.get_or_none(
                user_id=msg.from_user.id, chat_id=chat_id
            )
            if not r_executer_chat:
                r_executer_chat = db_management.RUserChat.create(
                    user_id=msg.from_user.id, chat_id=chat_id
                )
            if utils.IsSeniorModOrHigher(
                user_id=msg.from_user.id, chat_id=chat_id, r_user_chat=r_executer_chat
            ):
                run_date = None
                for i, user in enumerate(msg.command[2:]):
                    # execute at intervals of 5 seconds (max 12 users per minute)
                    run_date = datetime.datetime.utcnow() + datetime.timedelta(
                        seconds=(i + 1) * 5
                    )
                    utils.scheduler.add_job(
                        func=MultipleFunctionExecution,
                        trigger=DateTrigger(run_date=run_date, timezone=utc),
                        kwargs=dict(
                            msg=msg,
                            value=user,
                            func=methods.Ban,
                            func_kwargs=dict(
                                client=client,
                                executer=msg.from_user.id,
                                chat_id=chat_id,
                                r_executer_chat=r_executer_chat,
                                chat_settings=chat_settings,
                            ),
                        ),
                    )
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(chat_settings.language, "processing_multiple_command")
                    + "\n"
                    + _(chat_settings.language, "estimated_completion_time_X").format(
                        run_date
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
        commands=utils.GetCommandsVariants(commands=["multipleunban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.group
)
def CmdMultipleUnbanUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    if utils.IsSeniorModOrHigher(
        user_id=msg.from_user.id, chat_id=msg.chat.id, r_user_chat=msg.r_user_chat
    ):
        run_date = None
        for i, user in enumerate(msg.command[1:]):
            # execute at intervals of 5 seconds (max 12 users per minute)
            run_date = datetime.datetime.utcnow() + datetime.timedelta(
                seconds=(i + 1) * 5
            )
            utils.scheduler.add_job(
                func=MultipleFunctionExecution,
                trigger=DateTrigger(run_date=run_date, timezone=utc),
                kwargs=dict(
                    msg=msg,
                    value=user,
                    func=methods.Unban,
                    func_kwargs=dict(
                        client=client,
                        executer=msg.from_user.id,
                        chat_id=msg.chat.id,
                        r_executer_chat=msg.r_user_chat,
                        chat_settings=msg.chat.settings,
                    ),
                ),
            )
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "processing_multiple_command")
            + "\n"
            + _(msg.chat.settings.language, "estimated_completion_time_X").format(
                run_date
            ),
        )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["multipleunban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
def CmdMultipleUnbanChatUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    chat_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(chat_id, str):
        methods.ReplyText(client=client, msg=msg, text=chat_id)
    else:
        chat_settings: db_management.ChatSettings = (
            db_management.ChatSettings.get_or_none(chat_id=chat_id)
        )
        if chat_settings:
            r_executer_chat = db_management.RUserChat.get_or_none(
                user_id=msg.from_user.id, chat_id=chat_id
            )
            if not r_executer_chat:
                r_executer_chat = db_management.RUserChat.create(
                    user_id=msg.from_user.id, chat_id=chat_id
                )
            if utils.IsSeniorModOrHigher(
                user_id=msg.from_user.id, chat_id=chat_id, r_user_chat=r_executer_chat
            ):
                run_date = None
                for i, user in enumerate(msg.command[2:]):
                    # execute at intervals of 5 seconds (max 12 users per minute)
                    run_date = datetime.datetime.utcnow() + datetime.timedelta(
                        seconds=(i + 1) * 5
                    )
                    utils.scheduler.add_job(
                        func=MultipleFunctionExecution,
                        trigger=DateTrigger(run_date=run_date, timezone=utc),
                        kwargs=dict(
                            msg=msg,
                            value=user,
                            func=methods.Unban,
                            func_kwargs=dict(
                                client=client,
                                executer=msg.from_user.id,
                                chat_id=chat_id,
                                r_executer_chat=r_executer_chat,
                                chat_settings=chat_settings,
                            ),
                        ),
                    )
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(chat_settings.language, "processing_multiple_command")
                    + "\n"
                    + _(chat_settings.language, "estimated_completion_time_X").format(
                        run_date
                    ),
                )
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.filters.user(utils.config["masters"])
    & pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["multiplegban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdMultipleGBanUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    seconds = int(msg.command[2])
    run_date = None
    for i, user in enumerate(msg.command[2:]):
        # execute at intervals of 5 seconds (max 12 users per minute)
        run_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=(i + 1) * 5)
        utils.scheduler.add_job(
            func=MultipleFunctionExecution,
            trigger=DateTrigger(run_date=run_date, timezone=utc),
            kwargs=dict(
                msg=msg,
                value=user,
                func=methods.GBan,
                func_kwargs=dict(
                    client=client,
                    executer=msg.from_user.id,
                    chat_id=msg.chat.id,
                    seconds=seconds,
                    r_executer_chat=msg.r_user_chat,
                    chat_settings=msg.chat.settings,
                ),
            ),
        )
    methods.ReplyText(
        client=client,
        msg=msg,
        text=_(msg.chat.settings.language, "processing_multiple_command")
        + "\n"
        + _(msg.chat.settings.language, "estimated_completion_time_X").format(run_date),
    )


@pyrogram.Client.on_message(
    pyrogram.filters.user(utils.config["masters"])
    & pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["multipleungban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdMultipleUngbanUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    run_date = None
    for i, user in enumerate(msg.command[1:]):
        # execute at intervals of 5 seconds (max 12 users per minute)
        run_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=(i + 1) * 5)
        utils.scheduler.add_job(
            func=MultipleFunctionExecution,
            trigger=DateTrigger(run_date=run_date, timezone=utc),
            kwargs=dict(
                msg=msg,
                value=user,
                func=methods.Ungban,
                func_kwargs=dict(
                    client=client,
                    executer=msg.from_user.id,
                    chat_id=msg.chat.id,
                    r_executer_chat=msg.r_user_chat,
                    chat_settings=msg.chat.settings,
                ),
            ),
        )
    methods.ReplyText(
        client=client,
        msg=msg,
        text=_(msg.chat.settings.language, "processing_multiple_command")
        + "\n"
        + _(msg.chat.settings.language, "estimated_completion_time_X").format(run_date),
    )


@pyrogram.Client.on_message(
    pyrogram.filters.user(utils.config["masters"])
    & pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["multipleblock"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdMultipleBlockUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    seconds = int(msg.command[2])
    run_date = None
    for i, user in enumerate(msg.command[2:]):
        # execute at intervals of 5 seconds (max 12 users per minute)
        run_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=(i + 1) * 5)
        utils.scheduler.add_job(
            func=MultipleFunctionExecution,
            trigger=DateTrigger(run_date=run_date, timezone=utc),
            kwargs=dict(
                msg=msg,
                value=user,
                func=methods.Block,
                func_kwargs=dict(
                    client=client,
                    executer=msg.from_user.id,
                    chat_id=msg.chat.id,
                    seconds=seconds,
                    r_executer_chat=msg.r_user_chat,
                    chat_settings=msg.chat.settings,
                ),
            ),
        )
    methods.ReplyText(
        client=client,
        msg=msg,
        text=_(msg.chat.settings.language, "processing_multiple_command")
        + "\n"
        + _(msg.chat.settings.language, "estimated_completion_time_X").format(run_date),
    )


@pyrogram.Client.on_message(
    pyrogram.filters.user(utils.config["masters"])
    & pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["multipleunblock"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
)
def CmdMultipleUnblockUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    run_date = None
    for i, user in enumerate(msg.command[1:]):
        # execute at intervals of 5 seconds (max 12 users per minute)
        run_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=(i + 1) * 5)
        utils.scheduler.add_job(
            func=MultipleFunctionExecution,
            trigger=DateTrigger(run_date=run_date, timezone=utc),
            kwargs=dict(
                msg=msg,
                value=user,
                func=methods.Unblock,
                func_kwargs=dict(
                    client=client,
                    executer=msg.from_user.id,
                    chat_id=msg.chat.id,
                    r_executer_chat=msg.r_user_chat,
                    chat_settings=msg.chat.settings,
                ),
            ),
        )
    methods.ReplyText(
        client=client,
        msg=msg,
        text=_(msg.chat.settings.language, "processing_multiple_command")
        + "\n"
        + _(msg.chat.settings.language, "estimated_completion_time_X").format(run_date),
    )
