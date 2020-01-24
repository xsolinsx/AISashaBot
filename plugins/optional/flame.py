import random
import traceback

import pyrogram

import db_management
import dictionaries
import methods
import utils

_ = utils.GetLocalizedString


@pyrogram.Client.on_message(pyrogram.Filters.group, group=-2)
def FlameUser(client: pyrogram.Client, msg: pyrogram.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
            plugin="flame", chat=msg.chat.id
        )
        allowed = r_chat_plugin.is_enabled_on_chat
    if allowed:
        r_flameduser_chat: db_management.RFlamedUserChat = db_management.RFlamedUserChat.get_or_none(
            chat_id=msg.chat.id, flamed_user_id=msg.from_user.id
        )
        if r_flameduser_chat:
            # atomic update
            db_management.RFlamedUserChat.update(
                {
                    db_management.RFlamedUserChat.counter: db_management.RFlamedUserChat.counter
                    + 1
                }
            ).where(
                (db_management.RFlamedUserChat.flamed_user == msg.from_user.id)
                & (db_management.RFlamedUserChat.chat == msg.chat.id)
            ).execute()
            r_flameduser_chat = db_management.RFlamedUserChat.get_or_none(
                chat_id=msg.chat.id, flamed_user_id=msg.from_user.id
            )
            if r_flameduser_chat.counter >= r_flameduser_chat.max_flame:
                r_flameduser_chat.delete_instance()
                text = methods.Kick(
                    client=client,
                    executer=client.ME.id,
                    target=msg.from_user.id,
                    chat_id=msg.chat.id,
                    reasons="#flame",
                    r_target_chat=msg.r_user_chat,
                    chat_settings=msg.chat.settings,
                )
                if text:
                    methods.ReplyText(client=client, msg=msg, text=text)
            else:
                r_flameduser_chat.save()
                flame_strings: list = utils.GetLocalizedDictionary(
                    msg.chat.settings.language
                )["flame_sentences"]
                methods.ReplyText(
                    client=client, msg=msg, text=random.choice(flame_strings)
                )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["flame"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdFlameReplyUser(client: pyrogram.Client, msg: pyrogram.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
            plugin="flame", chat=msg.chat.id
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    if allowed:
        if not msg.reply_to_message.r_user_chat.is_whitelisted:
            if utils.CompareRanks(
                executer=msg.from_user.id,
                target=msg.reply_to_message.from_user.id,
                chat_id=msg.chat.id,
                r_executer_chat=msg.r_user_chat,
                r_target_chat=msg.reply_to_message.r_user_chat,
                min_rank=dictionaries.RANKS["junior_mod"],
            ):
                if not db_management.RFlamedUserChat.get_or_none(
                    chat_id=msg.chat.id,
                    flamed_user_id=msg.reply_to_message.from_user.id,
                ):
                    flame_strings: list = utils.GetLocalizedDictionary(
                        msg.chat.settings.language
                    )["flame_sentences"]
                    if flame_strings:
                        limit = utils.config["default_flame_limit"]
                        if len(msg.command) > 1:
                            limit = int(msg.command[1])
                        try:
                            db_management.RFlamedUserChat.create(
                                chat_id=msg.chat.id,
                                flamed_user_id=msg.reply_to_message.from_user.id,
                                max_flame=limit,
                            )
                        except Exception as ex:
                            print(ex)
                            traceback.print_exc()
                            methods.ReplyText(
                                client=client,
                                msg=msg,
                                text=_(msg.chat.settings.language, "error_try_again"),
                            )
                        else:
                            utils.Log(
                                client=client,
                                chat_id=msg.chat.id,
                                executer=msg.from_user.id,
                                action=f"{msg.command[0]} {limit}",
                                target=msg.reply_to_message.from_user.id,
                            )
                            if not msg.text.startswith("del", 1):
                                if limit > len(flame_strings):
                                    methods.ReplyText(
                                        client=client,
                                        msg=msg,
                                        text=_(
                                            msg.chat.settings.language, "begin_flame"
                                        )
                                        + "\n"
                                        + _(
                                            msg.chat.settings.language,
                                            "few_flame_sentences_X",
                                        ).format(limit),
                                    )
                                else:
                                    methods.ReplyText(
                                        client=client,
                                        msg=msg,
                                        text=_(
                                            msg.chat.settings.language, "begin_flame"
                                        ),
                                    )
                    else:
                        methods.ReplyText(
                            client=client,
                            msg=msg,
                            text=_(msg.chat.settings.language, "no_flame_sentences"),
                        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["flame"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdFlameUser(client: pyrogram.Client, msg: pyrogram.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
            plugin="flame", chat=msg.chat.id
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    if allowed:
        user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
        if isinstance(user_id, str):
            methods.ReplyText(client=client, msg=msg, text=user_id)
        else:
            r_target_chat: db_management.RUserChat = db_management.RUserChat.get_or_none(
                user_id=user_id, chat_id=msg.chat.id
            )
            if not r_target_chat:
                r_target_chat = db_management.RUserChat.create(
                    user_id=user_id, chat_id=msg.chat.id
                )
            if not r_target_chat.is_whitelisted:
                if utils.CompareRanks(
                    executer=msg.from_user.id,
                    target=user_id,
                    chat_id=msg.chat.id,
                    r_executer_chat=msg.r_user_chat,
                    r_target_chat=r_target_chat,
                    min_rank=dictionaries.RANKS["junior_mod"],
                ):
                    if not db_management.RFlamedUserChat.get_or_none(
                        chat_id=msg.chat.id, flamed_user_id=user_id,
                    ):
                        flame_strings: list = utils.GetLocalizedDictionary(
                            msg.chat.settings.language
                        )["flame_sentences"]
                        if flame_strings:
                            limit = utils.config["default_flame_limit"]
                            if len(msg.command) > 2:
                                limit = int(msg.command[2])
                            try:
                                db_management.RFlamedUserChat.create(
                                    chat_id=msg.chat.id,
                                    flamed_user_id=user_id,
                                    max_flame=limit,
                                )
                            except Exception as ex:
                                print(ex)
                                traceback.print_exc()
                                methods.ReplyText(
                                    client=client,
                                    msg=msg,
                                    text=_(
                                        msg.chat.settings.language, "error_try_again"
                                    ),
                                )
                            else:
                                utils.Log(
                                    client=client,
                                    chat_id=msg.chat.id,
                                    executer=msg.from_user.id,
                                    action=f"{msg.command[0]} {limit}",
                                    target=user_id,
                                )
                                if not msg.text.startswith("del", 1):
                                    if limit > len(flame_strings):
                                        methods.ReplyText(
                                            client=client,
                                            msg=msg,
                                            text=_(
                                                msg.chat.settings.language,
                                                "begin_flame",
                                            )
                                            + "\n"
                                            + _(
                                                msg.chat.settings.language,
                                                "few_flame_sentences_X",
                                            ).format(limit),
                                        )
                                    else:
                                        methods.ReplyText(
                                            client=client,
                                            msg=msg,
                                            text=_(
                                                msg.chat.settings.language,
                                                "begin_flame",
                                            ),
                                        )
                        else:
                            methods.ReplyText(
                                client=client,
                                msg=msg,
                                text=_(
                                    msg.chat.settings.language, "no_flame_sentences"
                                ),
                            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["flame"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdFlameChatUser(client: pyrogram.Client, msg: pyrogram.Message):
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
            r_executer_chat = db_management.RUserChat.get_or_none(
                user_id=msg.from_user.id, chat_id=chat_id
            )
            if not r_executer_chat:
                r_executer_chat = db_management.RUserChat.create(
                    user_id=msg.from_user.id, chat_id=chat_id
                )
            allowed = False
            if chat_id < 0:
                r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
                    plugin="flame", chat=chat_id
                )
                allowed = (
                    r_chat_plugin.min_rank <= r_executer_chat.rank
                    and r_chat_plugin.is_enabled_on_chat
                )
            if allowed:
                r_target_chat: db_management.RUserChat = db_management.RUserChat.get_or_none(
                    user_id=user_id, chat_id=chat_id
                )
                if not r_target_chat:
                    r_target_chat = db_management.RUserChat.create(
                        user_id=user_id, chat_id=chat_id
                    )
                if not r_target_chat.is_whitelisted:
                    if utils.CompareRanks(
                        executer=msg.from_user.id,
                        target=user_id,
                        chat_id=chat_id,
                        r_executer_chat=r_executer_chat,
                        r_target_chat=r_target_chat,
                        min_rank=dictionaries.RANKS["junior_mod"],
                    ):
                        if not db_management.RFlamedUserChat.get_or_none(
                            chat_id=chat_id, flamed_user_id=user_id,
                        ):
                            flame_strings: list = utils.GetLocalizedDictionary(
                                msg.chat.settings.language
                            )["flame_sentences"]
                            if flame_strings:
                                limit = utils.config["default_flame_limit"]
                                if len(msg.command) > 3:
                                    limit = int(msg.command[3])
                                try:
                                    db_management.RFlamedUserChat.create(
                                        chat_id=chat_id,
                                        flamed_user_id=user_id,
                                        max_flame=limit,
                                    )
                                except Exception as ex:
                                    print(ex)
                                    traceback.print_exc()
                                    methods.ReplyText(
                                        client=client,
                                        msg=msg,
                                        text=_(
                                            msg.chat.settings.language,
                                            "error_try_again",
                                        ),
                                    )
                                else:
                                    utils.Log(
                                        client=client,
                                        chat_id=chat_id,
                                        executer=msg.from_user.id,
                                        action=f"{msg.command[0]} {limit}",
                                        target=user_id,
                                    )
                                    if limit > len(flame_strings):
                                        methods.ReplyText(
                                            client=client,
                                            msg=msg,
                                            text=_(
                                                msg.chat.settings.language,
                                                "begin_flame",
                                            )
                                            + "\n"
                                            + _(
                                                msg.chat.settings.language,
                                                "few_flame_sentences_X",
                                            ).format(limit),
                                        )
                                    else:
                                        methods.ReplyText(
                                            client=client,
                                            msg=msg,
                                            text=_(
                                                msg.chat.settings.language,
                                                "begin_flame",
                                            ),
                                        )
                            else:
                                methods.ReplyText(
                                    client=client,
                                    msg=msg,
                                    text=_(
                                        msg.chat.settings.language, "no_flame_sentences"
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
        commands=utils.GetCommandsVariants(commands=["stopflame"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdStopFlameReplyUser(client: pyrogram.Client, msg: pyrogram.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
            plugin="flame", chat=msg.chat.id
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    if allowed:
        if not msg.reply_to_message.r_user_chat.is_whitelisted:
            if utils.CompareRanks(
                executer=msg.from_user.id,
                target=msg.reply_to_message.from_user.id,
                chat_id=msg.chat.id,
                r_executer_chat=msg.r_user_chat,
                r_target_chat=msg.reply_to_message.r_user_chat,
                min_rank=dictionaries.RANKS["junior_mod"],
            ):
                r_flameduser_chat: db_management.RFlamedUserChat = db_management.RFlamedUserChat.get_or_none(
                    chat_id=msg.chat.id,
                    flamed_user_id=msg.reply_to_message.from_user.id,
                )
                if r_flameduser_chat:
                    r_flameduser_chat.delete_instance()
                    utils.Log(
                        client=client,
                        chat_id=msg.chat.id,
                        executer=msg.from_user.id,
                        action=msg.command[0],
                        target=msg.reply_to_message.from_user.id,
                    )
                    if not msg.text.startswith("del", 1):
                        methods.ReplyText(
                            client=client,
                            msg=msg,
                            text=_(msg.chat.settings.language, "stop_flame"),
                        )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["stopflame"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.Filters.reply
    & pyrogram.Filters.group
)
def CmdStopFlameUser(client: pyrogram.Client, msg: pyrogram.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
            plugin="flame", chat=msg.chat.id
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    if allowed:
        user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
        if isinstance(user_id, str):
            methods.ReplyText(client=client, msg=msg, text=user_id)
        else:
            r_target_chat: db_management.RUserChat = db_management.RUserChat.get_or_none(
                user_id=user_id, chat_id=msg.chat.id
            )
            if not r_target_chat:
                r_target_chat = db_management.RUserChat.create(
                    user_id=user_id, chat_id=msg.chat.id
                )
            if not r_target_chat.is_whitelisted:
                if utils.CompareRanks(
                    executer=msg.from_user.id,
                    target=user_id,
                    chat_id=msg.chat.id,
                    r_executer_chat=msg.r_user_chat,
                    r_target_chat=r_target_chat,
                    min_rank=dictionaries.RANKS["junior_mod"],
                ):
                    r_flameduser_chat: db_management.RFlamedUserChat = db_management.RFlamedUserChat.get_or_none(
                        chat_id=msg.chat.id, flamed_user_id=user_id,
                    )
                    if r_flameduser_chat:
                        r_flameduser_chat.delete_instance()
                        utils.Log(
                            client=client,
                            chat_id=msg.chat.id,
                            executer=msg.from_user.id,
                            action=msg.command[0],
                            target=user_id,
                        )
                        if not msg.text.startswith("del", 1):
                            methods.ReplyText(
                                client=client,
                                msg=msg,
                                text=_(msg.chat.settings.language, "stop_flame"),
                            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(commands=["stopflame"], prefixes=["/", "!", "#", "."],)
    & pyrogram.Filters.private
)
def CmdStopFlameChatUser(client: pyrogram.Client, msg: pyrogram.Message):
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
            r_executer_chat = db_management.RUserChat.get_or_none(
                user_id=msg.from_user.id, chat_id=chat_id
            )
            if not r_executer_chat:
                r_executer_chat = db_management.RUserChat.create(
                    user_id=msg.from_user.id, chat_id=chat_id
                )
            allowed = False
            if chat_id < 0:
                r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
                    plugin="flame", chat=chat_id
                )
                allowed = (
                    r_chat_plugin.min_rank <= r_executer_chat.rank
                    and r_chat_plugin.is_enabled_on_chat
                )
            if allowed:
                r_target_chat: db_management.RUserChat = db_management.RUserChat.get_or_none(
                    user_id=user_id, chat_id=chat_id
                )
                if not r_target_chat:
                    r_target_chat = db_management.RUserChat.create(
                        user_id=user_id, chat_id=chat_id
                    )
                if not r_target_chat.is_whitelisted:
                    if utils.CompareRanks(
                        executer=msg.from_user.id,
                        target=user_id,
                        chat_id=chat_id,
                        r_executer_chat=r_executer_chat,
                        r_target_chat=r_target_chat,
                        min_rank=dictionaries.RANKS["junior_mod"],
                    ):
                        r_flameduser_chat: db_management.RFlamedUserChat = db_management.RFlamedUserChat.get_or_none(
                            chat_id=chat_id, flamed_user_id=user_id,
                        )
                        if r_flameduser_chat:
                            r_flameduser_chat.delete_instance()
                            utils.Log(
                                client=client,
                                chat_id=chat_id,
                                executer=msg.from_user.id,
                                action=msg.command[0],
                                target=user_id,
                            )
                            methods.ReplyText(
                                client=client,
                                msg=msg,
                                text=_(msg.chat.settings.language, "stop_flame"),
                            )
        else:
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.from_user.settings.language, "no_chat_settings"),
            )
