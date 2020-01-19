import time
import traceback

import pyrogram

import db_management
import keyboards
import methods
import utils

_ = utils.GetLocalizedString


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["invite"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdInviteReplyUser(client: pyrogram.Client, msg: pyrogram.Message):
    if msg.reply_to_message.service and msg.reply_to_message.new_chat_members:
        if (
            msg.reply_to_message.new_chat_members[0].id
            != msg.reply_to_message.from_user.id
        ):
            msg.reply_to_message.new_chat_members.append(msg.reply_to_message.from_user)
        if len(msg.reply_to_message.new_chat_members) > 1:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "select_target"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildActionOnAddedUsersList(
                        chat_settings=msg.chat.settings,
                        action="invite",
                        new_chat_members=msg.reply_to_message.new_chat_members,
                    )
                ),
            )
        else:
            text = methods.Invite(
                client=client,
                executer=msg.from_user.id,
                target=msg.reply_to_message.new_chat_members[0],
                chat_id=msg.chat.id,
                r_executer_chat=msg.r_user_chat,
                chat_settings=msg.chat.settings,
            )
            if text and not msg.text.startswith("del", 1):
                methods.ReplyText(client=client, msg=msg, text=text)
    else:
        text = methods.Invite(
            client=client,
            executer=msg.from_user.id,
            target=msg.reply_to_message.from_user.id,
            chat_id=msg.chat.id,
            r_executer_chat=msg.r_user_chat,
            r_target_chat=msg.reply_to_message.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["invite"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdInviteUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(user_id, str):
        methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        text = methods.Invite(
            client=client,
            executer=msg.from_user.id,
            target=user_id,
            chat_id=msg.chat.id,
            r_executer_chat=msg.r_user_chat,
            chat_settings=msg.chat.settings,
        )
    if text and not msg.text.startswith("del", 1):
        methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["invite"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdInviteChatUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
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
            text = methods.Invite(
                client=client,
                executer=msg.from_user.id,
                target=user_id,
                chat_id=msg.chat.id,
                chat_settings=chat_settings,
            )
        if text:
            methods.ReplyText(client=client, msg=msg, text=text)
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["kickme"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.group
)
def CmdKickme(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    try:
        text = methods.Kick(
            client=client,
            executer=msg.from_user.id,
            target=msg.from_user.id,
            chat_id=msg.chat.id,
        )
    except pyrogram.errors.FloodWait as ex:
        print(ex)
        traceback.print_exc()
        text = _(msg.chat.settings.language, "tg_flood_wait_X").format(ex.x)
    except pyrogram.errors.RPCError as ex:
        print(ex)
        traceback.print_exc()
        text = _(msg.chat.settings.language, "tg_error_X").format(ex)
    else:
        utils.Log(
            client=client,
            chat_id=msg.chat.id,
            executer=msg.from_user.id,
            action=f"{msg.command[0]}",
            target=msg.chat.id,
        )
    if text and not msg.text.startswith("del", 1):
        methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["warn"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdWarnReplyUser(client: pyrogram.Client, msg: pyrogram.Message):
    reason = ""
    if len(msg.command) > 1:
        reason = " ".join(msg.command[1:])
    if msg.reply_to_message.service and msg.reply_to_message.new_chat_members:
        if (
            msg.reply_to_message.new_chat_members[0].id
            != msg.reply_to_message.from_user.id
        ):
            msg.reply_to_message.new_chat_members.append(msg.reply_to_message.from_user)
        if len(msg.reply_to_message.new_chat_members) > 1:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "select_target"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildActionOnAddedUsersList(
                        chat_settings=msg.chat.settings,
                        action="warn",
                        new_chat_members=msg.reply_to_message.new_chat_members,
                    )
                ),
            )
        else:
            text = methods.Warn(
                client=client,
                executer=msg.from_user.id,
                target=msg.reply_to_message.new_chat_members[0],
                chat_id=msg.chat.id,
                reasons=reason,
                r_executer_chat=msg.r_user_chat,
                chat_settings=msg.chat.settings,
            )
            if text and not msg.text.startswith("del", 1):
                methods.ReplyText(client=client, msg=msg, text=text)
    else:
        text = methods.Warn(
            client=client,
            executer=msg.from_user.id,
            target=msg.reply_to_message.from_user.id,
            chat_id=msg.chat.id,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            r_target_chat=msg.reply_to_message.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["warn"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdWarnUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 2:
        reason = " ".join(msg.command[2:])
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(user_id, str):
        methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        text = methods.Warn(
            client=client,
            executer=msg.from_user.id,
            target=user_id,
            chat_id=msg.chat.id,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["warn"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdWarnChatUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 3:
        reason = " ".join(msg.command[3:])
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
            text = methods.Warn(
                client=client,
                executer=msg.from_user.id,
                target=user_id,
                chat_id=chat_id,
                reasons=reason,
                chat_settings=chat_settings,
            )
            if text:
                methods.ReplyText(client=client, msg=msg, text=text)
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["unwarn"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdUnwarnReplyUser(client: pyrogram.Client, msg: pyrogram.Message):
    reason = ""
    if len(msg.command) > 1:
        reason = " ".join(msg.command[1:])
    if msg.reply_to_message.service and msg.reply_to_message.new_chat_members:
        if (
            msg.reply_to_message.new_chat_members[0].id
            != msg.reply_to_message.from_user.id
        ):
            msg.reply_to_message.new_chat_members.append(msg.reply_to_message.from_user)
        if len(msg.reply_to_message.new_chat_members) > 1:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "select_target"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildActionOnAddedUsersList(
                        chat_settings=msg.chat.settings,
                        action="unwarn",
                        new_chat_members=msg.reply_to_message.new_chat_members,
                    )
                ),
            )
        else:
            text = methods.Unwarn(
                client=client,
                executer=msg.from_user.id,
                target=msg.reply_to_message.new_chat_members[0],
                chat_id=msg.chat.id,
                reasons=reason,
                r_executer_chat=msg.r_user_chat,
                chat_settings=msg.chat.settings,
            )
            if text and not msg.text.startswith("del", 1):
                methods.ReplyText(client=client, msg=msg, text=text)
    else:
        text = methods.Unwarn(
            client=client,
            executer=msg.from_user.id,
            target=msg.reply_to_message.from_user.id,
            chat_id=msg.chat.id,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            r_target_chat=msg.reply_to_message.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["unwarn"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdUnwarnUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 2:
        reason = " ".join(msg.command[2:])
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(user_id, str):
        methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        text = methods.Unwarn(
            client=client,
            executer=msg.from_user.id,
            target=user_id,
            chat_id=msg.chat.id,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["unwarn"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdUnwarnChatUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 3:
        reason = " ".join(msg.command[3:])
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
            text = methods.Unwarn(
                client=client,
                executer=msg.from_user.id,
                target=user_id,
                chat_id=chat_id,
                reasons=reason,
                chat_settings=chat_settings,
            )
            if text:
                methods.ReplyText(client=client, msg=msg, text=text)
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["unwarnall"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdUnwarnAllReplyUser(client: pyrogram.Client, msg: pyrogram.Message):
    reason = ""
    if len(msg.command) > 1:
        reason = " ".join(msg.command[1:])
    if msg.reply_to_message.service and msg.reply_to_message.new_chat_members:
        if (
            msg.reply_to_message.new_chat_members[0].id
            != msg.reply_to_message.from_user.id
        ):
            msg.reply_to_message.new_chat_members.append(msg.reply_to_message.from_user)
        if len(msg.reply_to_message.new_chat_members) > 1:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "select_target"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildActionOnAddedUsersList(
                        chat_settings=msg.chat.settings,
                        action="unwarnall",
                        new_chat_members=msg.reply_to_message.new_chat_members,
                    )
                ),
            )
        else:
            text = methods.UnwarnAll(
                client=client,
                executer=msg.from_user.id,
                target=msg.reply_to_message.new_chat_members[0],
                chat_id=msg.chat.id,
                reasons=reason,
                r_executer_chat=msg.r_user_chat,
                chat_settings=msg.chat.settings,
            )
            if text and not msg.text.startswith("del", 1):
                methods.ReplyText(client=client, msg=msg, text=text)
    else:
        text = methods.UnwarnAll(
            client=client,
            executer=msg.from_user.id,
            target=msg.reply_to_message.from_user.id,
            chat_id=msg.chat.id,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            r_target_chat=msg.reply_to_message.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["unwarnall"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdUnwarnAllUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 2:
        reason = " ".join(msg.command[2:])
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(user_id, str):
        methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        text = methods.UnwarnAll(
            client=client,
            executer=msg.from_user.id,
            target=user_id,
            chat_id=msg.chat.id,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["unwarnall"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdUnwarnAllChatUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 3:
        reason = " ".join(msg.command[3:])
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
            text = methods.UnwarnAll(
                client=client,
                executer=msg.from_user.id,
                target=user_id,
                chat_id=chat_id,
                reasons=reason,
                chat_settings=chat_settings,
            )
            if text:
                methods.ReplyText(client=client, msg=msg, text=text)
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["kick"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdKickReplyUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 1:
        reason = " ".join(msg.command[1:])
    if msg.reply_to_message.service and msg.reply_to_message.new_chat_members:
        if (
            msg.reply_to_message.new_chat_members[0].id
            != msg.reply_to_message.from_user.id
        ):
            msg.reply_to_message.new_chat_members.append(msg.reply_to_message.from_user)
        if len(msg.reply_to_message.new_chat_members) > 1:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "select_target"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildActionOnAddedUsersList(
                        chat_settings=msg.chat.settings,
                        action="kick",
                        new_chat_members=msg.reply_to_message.new_chat_members,
                    )
                ),
            )
        else:
            text = methods.Kick(
                client=client,
                executer=msg.from_user.id,
                target=msg.reply_to_message.new_chat_members[0],
                chat_id=msg.chat.id,
                reasons=reason,
                r_executer_chat=msg.r_user_chat,
                chat_settings=msg.chat.settings,
            )
            if text and not msg.text.startswith("del", 1):
                methods.ReplyText(client=client, msg=msg, text=text)
    else:
        text = methods.Kick(
            client=client,
            executer=msg.from_user.id,
            target=msg.reply_to_message.from_user.id,
            chat_id=msg.chat.id,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            r_target_chat=msg.reply_to_message.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["kick"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdKickUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 2:
        reason = " ".join(msg.command[2:])
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(user_id, str):
        methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        text = methods.Kick(
            client=client,
            executer=msg.from_user.id,
            target=user_id,
            chat_id=msg.chat.id,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["kick"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdKickChatUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 3:
        reason = " ".join(msg.command[3:])
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
            text = methods.Kick(
                client=client,
                executer=msg.from_user.id,
                target=user_id,
                chat_id=chat_id,
                reasons=reason,
                chat_settings=chat_settings,
            )
            if text:
                methods.ReplyText(client=client, msg=msg, text=text)
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["temprestrict"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdTempRestrictReplyUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 1:
        reason = " ".join(msg.command[1:])
    if msg.reply_to_message.service and msg.reply_to_message.new_chat_members:
        if (
            msg.reply_to_message.new_chat_members[0].id
            != msg.reply_to_message.from_user.id
        ):
            msg.reply_to_message.new_chat_members.append(msg.reply_to_message.from_user)
        if len(msg.reply_to_message.new_chat_members) > 1:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "select_target"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildActionOnAddedUsersList(
                        chat_settings=msg.chat.settings,
                        action="temprestrict",
                        new_chat_members=msg.reply_to_message.new_chat_members,
                    )
                ),
            )
        else:
            text = methods.Restrict(
                client=client,
                executer=msg.from_user.id,
                target=msg.reply_to_message.new_chat_members[0],
                chat_id=msg.chat.id,
                until_date=int(time.time()) + msg.chat.settings.max_temp_restrict,
                reasons=reason,
                r_executer_chat=msg.r_user_chat,
                chat_settings=msg.chat.settings,
            )
            if text and not msg.text.startswith("del", 1):
                methods.ReplyText(client=client, msg=msg, text=text)
    else:
        text = methods.Restrict(
            client=client,
            executer=msg.from_user.id,
            target=msg.reply_to_message.from_user.id,
            chat_id=msg.chat.id,
            until_date=int(time.time()) + msg.chat.settings.max_temp_restrict,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            r_target_chat=msg.reply_to_message.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["temprestrict"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdTempRestrictUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 2:
        reason = " ".join(msg.command[2:])
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(user_id, str):
        methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        text = methods.Restrict(
            client=client,
            executer=msg.from_user.id,
            target=user_id,
            chat_id=msg.chat.id,
            until_date=int(time.time()) + msg.chat.settings.max_temp_restrict,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["temprestrict"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdTempRestrictChatUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 3:
        reason = " ".join(msg.command[3:])
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
            text = methods.Restrict(
                client=client,
                executer=msg.from_user.id,
                target=user_id,
                chat_id=chat_id,
                until_date=int(time.time()) + chat_settings.max_temp_restrict,
                reasons=reason,
                chat_settings=chat_settings,
            )
            if text:
                methods.ReplyText(client=client, msg=msg, text=text)
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["restrict"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdRestrictReplyUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 1:
        reason = " ".join(msg.command[1:])
    if msg.reply_to_message.service and msg.reply_to_message.new_chat_members:
        if (
            msg.reply_to_message.new_chat_members[0].id
            != msg.reply_to_message.from_user.id
        ):
            msg.reply_to_message.new_chat_members.append(msg.reply_to_message.from_user)
        if len(msg.reply_to_message.new_chat_members) > 1:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "select_target"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildActionOnAddedUsersList(
                        chat_settings=msg.chat.settings,
                        action="restrict",
                        new_chat_members=msg.reply_to_message.new_chat_members,
                    )
                ),
            )
        else:
            text = methods.Restrict(
                client=client,
                executer=msg.from_user.id,
                target=msg.reply_to_message.new_chat_members[0],
                chat_id=msg.chat.id,
                reasons=reason,
                r_executer_chat=msg.r_user_chat,
                chat_settings=msg.chat.settings,
            )
            if text and not msg.text.startswith("del", 1):
                methods.ReplyText(client=client, msg=msg, text=text)
    else:
        text = methods.Restrict(
            client=client,
            executer=msg.from_user.id,
            target=msg.reply_to_message.from_user.id,
            chat_id=msg.chat.id,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            r_target_chat=msg.reply_to_message.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["restrict"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdRestrictUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 2:
        reason = " ".join(msg.command[2:])
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(user_id, str):
        methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        text = methods.Restrict(
            client=client,
            executer=msg.from_user.id,
            target=user_id,
            chat_id=msg.chat.id,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["restrict"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdRestrictChatUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 3:
        reason = " ".join(msg.command[3:])
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
            text = methods.Restrict(
                client=client,
                executer=msg.from_user.id,
                target=user_id,
                chat_id=chat_id,
                reasons=reason,
                chat_settings=chat_settings,
            )
            if text:
                methods.ReplyText(client=client, msg=msg, text=text)
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["unrestrict"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdUnrestrictReplyUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 1:
        reason = " ".join(msg.command[1:])
    if msg.reply_to_message.service and msg.reply_to_message.new_chat_members:
        if (
            msg.reply_to_message.new_chat_members[0].id
            != msg.reply_to_message.from_user.id
        ):
            msg.reply_to_message.new_chat_members.append(msg.reply_to_message.from_user)
        if len(msg.reply_to_message.new_chat_members) > 1:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "select_target"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildActionOnAddedUsersList(
                        chat_settings=msg.chat.settings,
                        action="unrestrict",
                        new_chat_members=msg.reply_to_message.new_chat_members,
                    )
                ),
            )
        else:
            text = methods.Unrestrict(
                client=client,
                executer=msg.from_user.id,
                target=msg.reply_to_message.new_chat_members[0],
                chat_id=msg.chat.id,
                reasons=reason,
                r_executer_chat=msg.r_user_chat,
                chat_settings=msg.chat.settings,
            )
            if text and not msg.text.startswith("del", 1):
                methods.ReplyText(client=client, msg=msg, text=text)
    else:
        text = methods.Unrestrict(
            client=client,
            executer=msg.from_user.id,
            target=msg.reply_to_message.from_user.id,
            chat_id=msg.chat.id,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            r_target_chat=msg.reply_to_message.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["unrestrict"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdUnrestrictUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 2:
        reason = " ".join(msg.command[2:])
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(user_id, str):
        methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        text = methods.Unrestrict(
            client=client,
            executer=msg.from_user.id,
            target=user_id,
            chat_id=msg.chat.id,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["unrestrict"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdUnrestrictChatUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 3:
        reason = " ".join(msg.command[3:])
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
            text = methods.Unrestrict(
                client=client,
                executer=msg.from_user.id,
                target=user_id,
                chat_id=chat_id,
                reasons=reason,
                chat_settings=chat_settings,
            )
            if text:
                methods.ReplyText(client=client, msg=msg, text=text)
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["tempban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdTempBanReplyUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 1:
        reason = " ".join(msg.command[1:])
    if msg.reply_to_message.service and msg.reply_to_message.new_chat_members:
        if (
            msg.reply_to_message.new_chat_members[0].id
            != msg.reply_to_message.from_user.id
        ):
            msg.reply_to_message.new_chat_members.append(msg.reply_to_message.from_user)
        if len(msg.reply_to_message.new_chat_members) > 1:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "select_target"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildActionOnAddedUsersList(
                        chat_settings=msg.chat.settings,
                        action="tempban",
                        new_chat_members=msg.reply_to_message.new_chat_members,
                    )
                ),
            )
        else:
            text = methods.Ban(
                client=client,
                executer=msg.from_user.id,
                target=msg.reply_to_message.new_chat_members[0],
                chat_id=msg.chat.id,
                until_date=int(time.time()) + msg.chat.settings.max_temp_ban,
                reasons=reason,
                r_executer_chat=msg.r_user_chat,
                chat_settings=msg.chat.settings,
            )
            if text and not msg.text.startswith("del", 1):
                methods.ReplyText(client=client, msg=msg, text=text)
    else:
        text = methods.Ban(
            client=client,
            executer=msg.from_user.id,
            target=msg.reply_to_message.from_user.id,
            chat_id=msg.chat.id,
            until_date=int(time.time()) + msg.chat.settings.max_temp_ban,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            r_target_chat=msg.reply_to_message.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["tempban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdTempBanUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 2:
        reason = " ".join(msg.command[2:])
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(user_id, str):
        methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        text = methods.Ban(
            client=client,
            executer=msg.from_user.id,
            target=user_id,
            chat_id=msg.chat.id,
            until_date=int(time.time()) + msg.chat.settings.max_temp_ban,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["tempban"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdTempBanChatUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 3:
        reason = " ".join(msg.command[3:])
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
            text = methods.Ban(
                client=client,
                executer=msg.from_user.id,
                target=user_id,
                chat_id=chat_id,
                until_date=int(time.time()) + msg.chat.settings.max_temp_ban,
                reasons=reason,
                chat_settings=chat_settings,
            )
            if text:
                methods.ReplyText(client=client, msg=msg, text=text)
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["ban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdBanReplyUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 1:
        reason = " ".join(msg.command[1:])
    if msg.reply_to_message.service and msg.reply_to_message.new_chat_members:
        if (
            msg.reply_to_message.new_chat_members[0].id
            != msg.reply_to_message.from_user.id
        ):
            msg.reply_to_message.new_chat_members.append(msg.reply_to_message.from_user)
        if len(msg.reply_to_message.new_chat_members) > 1:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "select_target"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildActionOnAddedUsersList(
                        chat_settings=msg.chat.settings,
                        action="ban",
                        new_chat_members=msg.reply_to_message.new_chat_members,
                    )
                ),
            )
        else:
            text = methods.Ban(
                client=client,
                executer=msg.from_user.id,
                target=msg.reply_to_message.new_chat_members[0],
                chat_id=msg.chat.id,
                reasons=reason,
                r_executer_chat=msg.r_user_chat,
                chat_settings=msg.chat.settings,
            )
            if text and not msg.text.startswith("del", 1):
                methods.ReplyText(client=client, msg=msg, text=text)
    else:
        text = methods.Ban(
            client=client,
            executer=msg.from_user.id,
            target=msg.reply_to_message.from_user.id,
            chat_id=msg.chat.id,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            r_target_chat=msg.reply_to_message.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text:
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["ban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdBanUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 2:
        reason = " ".join(msg.command[2:])
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(user_id, str):
        methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        text = methods.Ban(
            client=client,
            executer=msg.from_user.id,
            target=user_id,
            chat_id=msg.chat.id,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["ban"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdBanChatUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 3:
        reason = " ".join(msg.command[3:])
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
            text = methods.Ban(
                client=client,
                executer=msg.from_user.id,
                target=user_id,
                chat_id=chat_id,
                reasons=reason,
                chat_settings=chat_settings,
            )
            if text:
                methods.ReplyText(client=client, msg=msg, text=text)
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["unban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdUnbanReplyUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 1:
        reason = " ".join(msg.command[1:])
    if msg.reply_to_message.service and msg.reply_to_message.new_chat_members:
        if (
            msg.reply_to_message.new_chat_members[0].id
            != msg.reply_to_message.from_user.id
        ):
            msg.reply_to_message.new_chat_members.append(msg.reply_to_message.from_user)
        if len(msg.reply_to_message.new_chat_members) > 1:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "select_target"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildActionOnAddedUsersList(
                        chat_settings=msg.chat.settings,
                        action="unban",
                        new_chat_members=msg.reply_to_message.new_chat_members,
                    )
                ),
            )
        else:
            text = methods.Unban(
                client=client,
                executer=msg.from_user.id,
                target=msg.reply_to_message.new_chat_members[0],
                chat_id=msg.chat.id,
                reasons=reason,
                r_executer_chat=msg.r_user_chat,
                chat_settings=msg.chat.settings,
            )
            if text and not msg.text.startswith("del", 1):
                methods.ReplyText(client=client, msg=msg, text=text)
    else:
        text = methods.Unban(
            client=client,
            executer=msg.from_user.id,
            target=msg.reply_to_message.from_user.id,
            chat_id=msg.chat.id,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            r_target_chat=msg.reply_to_message.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["unban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdUnbanUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 2:
        reason = " ".join(msg.command[2:])
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(user_id, str):
        methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        text = methods.Unban(
            client=client,
            executer=msg.from_user.id,
            target=user_id,
            chat_id=msg.chat.id,
            reasons=reason,
            r_executer_chat=msg.r_user_chat,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["unban"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdUnbanChatUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 3:
        reason = " ".join(msg.command[3:])
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
            text = methods.Unban(
                client=client,
                executer=msg.from_user.id,
                target=user_id,
                chat_id=chat_id,
                reasons=reason,
                chat_settings=chat_settings,
            )
            if text:
                methods.ReplyText(client=client, msg=msg, text=text)
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["gban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
)
def CmdGBanReplyUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    seconds = 86400
    reason = ""
    if len(msg.command) > 1:
        if utils.IsInt(msg.command[1]):
            seconds = int(msg.command[1])
            reason = " ".join(msg.command[2:])
        else:
            reason = " ".join(msg.command[1:])
    if msg.reply_to_message.service and msg.reply_to_message.new_chat_members:
        if (
            msg.reply_to_message.new_chat_members[0].id
            != msg.reply_to_message.from_user.id
        ):
            msg.reply_to_message.new_chat_members.append(msg.reply_to_message.from_user)
        if len(msg.reply_to_message.new_chat_members) > 1:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "select_target"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildActionOnAddedUsersList(
                        chat_settings=msg.chat.settings,
                        action="gban",
                        new_chat_members=msg.reply_to_message.new_chat_members,
                    )
                ),
            )
        else:
            text = methods.GBan(
                client=client,
                executer=msg.from_user.id,
                target=msg.reply_to_message.new_chat_members[0],
                chat_id=msg.chat.id,
                seconds=seconds,
                reasons=reason,
                chat_settings=msg.chat.settings,
            )
            if text and not msg.text.startswith("del", 1):
                methods.ReplyText(client=client, msg=msg, text=text)
    else:
        text = methods.GBan(
            client=client,
            executer=msg.from_user.id,
            target=msg.reply_to_message.from_user.id,
            chat_id=msg.chat.id,
            seconds=seconds,
            reasons=reason,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["gban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.Filters.reply
)
def CmdGBanUser(client: pyrogram.Client, msg: pyrogram.Message):
    seconds = 86400
    reason = ""
    if len(msg.command) > 2:
        if utils.IsInt(msg.command[2]):
            seconds = int(msg.command[2])
            reason = " ".join(msg.command[3:])
        else:
            reason = " ".join(msg.command[2:])
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(user_id, str):
        methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        text = methods.GBan(
            client=client,
            executer=msg.from_user.id,
            target=user_id,
            chat_id=msg.chat.id,
            seconds=seconds,
            reasons=reason,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["ungban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
)
def CmdUngbanReplyUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 1:
        reason = " ".join(msg.command[1:])
    if msg.reply_to_message.service and msg.reply_to_message.new_chat_members:
        if (
            msg.reply_to_message.new_chat_members[0].id
            != msg.reply_to_message.from_user.id
        ):
            msg.reply_to_message.new_chat_members.append(msg.reply_to_message.from_user)
        if len(msg.reply_to_message.new_chat_members) > 1:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "select_target"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildActionOnAddedUsersList(
                        chat_settings=msg.chat.settings,
                        action="ungban",
                        new_chat_members=msg.reply_to_message.new_chat_members,
                    )
                ),
            )
        else:
            text = methods.Ungban(
                client=client,
                executer=msg.from_user.id,
                target=msg.reply_to_message.new_chat_members[0],
                chat_id=msg.chat.id,
                reasons=reason,
                chat_settings=msg.chat.settings,
            )
            if text and not msg.text.startswith("del", 1):
                methods.ReplyText(client=client, msg=msg, text=text)
    else:
        text = methods.Ungban(
            client=client,
            executer=msg.from_user.id,
            target=msg.reply_to_message.from_user.id,
            chat_id=msg.chat.id,
            reasons=reason,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["ungban"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.Filters.reply
)
def CmdUngbanUser(client: pyrogram.Client, msg: pyrogram.Message):
    reason = ""
    if len(msg.command) > 2:
        reason = " ".join(msg.command[2:])
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(user_id, str):
        methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        text = methods.Ungban(
            client=client,
            executer=msg.from_user.id,
            target=user_id,
            chat_id=msg.chat.id,
            reasons=reason,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["block"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
)
def CmdBlockReplyUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    seconds = 3600
    reason = ""
    if len(msg.command) > 1:
        if utils.IsInt(msg.command[1]):
            seconds = int(msg.command[1])
            reason = " ".join(msg.command[2:])
        else:
            reason = " ".join(msg.command[1:])
    if msg.reply_to_message.service and msg.reply_to_message.new_chat_members:
        if (
            msg.reply_to_message.new_chat_members[0].id
            != msg.reply_to_message.from_user.id
        ):
            msg.reply_to_message.new_chat_members.append(msg.reply_to_message.from_user)
        if len(msg.reply_to_message.new_chat_members) > 1:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "select_target"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildActionOnAddedUsersList(
                        chat_settings=msg.chat.settings,
                        action="block",
                        new_chat_members=msg.reply_to_message.new_chat_members,
                    )
                ),
            )
        else:
            text = methods.Block(
                client=client,
                executer=msg.from_user.id,
                target=msg.reply_to_message.new_chat_members[0],
                chat_id=msg.chat.id,
                seconds=seconds,
                reasons=reason,
                chat_settings=msg.chat.settings,
            )
            if text and not msg.text.startswith("del", 1):
                methods.ReplyText(client=client, msg=msg, text=text)
    else:
        text = methods.Block(
            client=client,
            executer=msg.from_user.id,
            target=msg.reply_to_message.from_user.id,
            chat_id=msg.chat.id,
            seconds=seconds,
            reasons=reason,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["block"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.Filters.reply
)
def CmdBlockUser(client: pyrogram.Client, msg: pyrogram.Message):
    seconds = 3600
    reason = ""
    if len(msg.command) > 2:
        if utils.IsInt(msg.command[2]):
            seconds = int(msg.command[2])
            reason = " ".join(msg.command[3:])
        else:
            reason = " ".join(msg.command[2:])
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(user_id, str):
        methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        text = methods.Block(
            client=client,
            executer=msg.from_user.id,
            target=user_id,
            chat_id=msg.chat.id,
            seconds=seconds,
            reasons=reason,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["unblock"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
)
def CmdUnblockReplyUser(client: pyrogram.Client, msg: pyrogram.Message):
    text = ""
    reason = ""
    if len(msg.command) > 1:
        reason = " ".join(msg.command[1:])
    if msg.reply_to_message.service and msg.reply_to_message.new_chat_members:
        if (
            msg.reply_to_message.new_chat_members[0].id
            != msg.reply_to_message.from_user.id
        ):
            msg.reply_to_message.new_chat_members.append(msg.reply_to_message.from_user)
        if len(msg.reply_to_message.new_chat_members) > 1:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "select_target"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildActionOnAddedUsersList(
                        chat_settings=msg.chat.settings,
                        action="unblock",
                        new_chat_members=msg.reply_to_message.new_chat_members,
                    )
                ),
            )
        else:
            text = methods.Unblock(
                client=client,
                executer=msg.from_user.id,
                target=msg.reply_to_message.new_chat_members[0],
                chat_id=msg.chat.id,
                reasons=reason,
                chat_settings=msg.chat.settings,
            )
            if text and not msg.text.startswith("del", 1):
                methods.ReplyText(client=client, msg=msg, text=text)
    else:
        text = methods.Unblock(
            client=client,
            executer=msg.from_user.id,
            target=msg.reply_to_message.from_user.id,
            chat_id=msg.chat.id,
            reasons=reason,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.Filters.user(utils.config["masters"])
    & pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["unblock"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.Filters.reply
)
def CmdUnblockUser(client: pyrogram.Client, msg: pyrogram.Message):
    reason = ""
    if len(msg.command) > 2:
        reason = " ".join(msg.command[2:])
    user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
    if isinstance(user_id, str):
        methods.ReplyText(client=client, msg=msg, text=user_id)
    else:
        text = methods.Unblock(
            client=client,
            executer=msg.from_user.id,
            target=user_id,
            chat_id=msg.chat.id,
            reasons=reason,
            chat_settings=msg.chat.settings,
        )
        if text and not msg.text.startswith("del", 1):
            methods.ReplyText(client=client, msg=msg, text=text)
