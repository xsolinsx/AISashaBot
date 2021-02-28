import traceback

import pyrogram

import db_management
import keyboards
import methods
import utils

_ = utils.GetLocalizedString


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["echo"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.text
)
def CmdEcho(client: pyrogram.Client, msg: pyrogram.types.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = (
            db_management.RChatPlugin.get_or_none(plugin="interact", chat=msg.chat.id)
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == "private"
    if allowed:
        text = utils.RemoveCommand(cmd=msg.command)
        if text != "":
            methods.ReplyText(client=client, msg=msg, text=text)


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["echomarkdown"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.text
)
def CmdEchoMarkdown(client: pyrogram.Client, msg: pyrogram.types.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = (
            db_management.RChatPlugin.get_or_none(plugin="interact", chat=msg.chat.id)
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == "private"
    if allowed:
        text = utils.RemoveCommand(cmd=msg.command)
        methods.ReplyText(client=client, msg=msg, text=text, parse_mode="markdown")


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["echohtml"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.text
)
def CmdEchoHTML(client: pyrogram.Client, msg: pyrogram.types.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = (
            db_management.RChatPlugin.get_or_none(plugin="interact", chat=msg.chat.id)
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == "private"
    if allowed:
        text = utils.RemoveCommand(cmd=msg.command)
        methods.ReplyText(client=client, msg=msg, text=text, parse_mode="html")


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["edit"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.text
    & pyrogram.filters.reply
)
def CmdEdit(client: pyrogram.Client, msg: pyrogram.types.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = (
            db_management.RChatPlugin.get_or_none(plugin="interact", chat=msg.chat.id)
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == "private"
    if allowed:
        text = utils.RemoveCommand(cmd=msg.command)
        if text != "" and msg.reply_to_message.from_user.id == client.ME.id:
            msg.reply_to_message.edit_text(text=text)


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["editmarkdown"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.text
    & pyrogram.filters.reply
)
def CmdEditMarkdown(client: pyrogram.Client, msg: pyrogram.types.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = (
            db_management.RChatPlugin.get_or_none(plugin="interact", chat=msg.chat.id)
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == "private"
    if allowed:
        text = utils.RemoveCommand(cmd=msg.command)
        if text != "" and msg.reply_to_message.from_user.id == client.ME.id:
            msg.reply_to_message.edit_text(text=text, parse_mode="markdown")


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["edithtml"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.text
    & pyrogram.filters.reply
)
def CmdEditHTML(client: pyrogram.Client, msg: pyrogram.types.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = (
            db_management.RChatPlugin.get_or_none(plugin="interact", chat=msg.chat.id)
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == "private"
    if allowed:
        text = utils.RemoveCommand(cmd=msg.command)
        if text != "" and msg.reply_to_message.from_user.id == client.ME.id:
            msg.reply_to_message.edit_text(text=text, parse_mode="html")


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(
            commands=[
                "typing",
                "upload_photo",
                "record_video",
                "upload_video",
                "record_audio",
                "upload_audio",
                "upload_document",
                "find_location",
                "record_video_note",
                "upload_video_note",
                "choose_contact",
                "playing",
                "cancel",
            ],
            del_=True,
        ),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.text
)
def CmdChatAction(client: pyrogram.Client, msg: pyrogram.types.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = (
            db_management.RChatPlugin.get_or_none(plugin="interact", chat=msg.chat.id)
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == "private"
    if allowed:
        try:
            msg.reply_chat_action(action=msg.command[0])
        except Exception as ex:
            print(ex)
            traceback.print_exc()
            methods.ReplyText(
                client=client,
                msg=msg,
                text=_(msg.chat.settings.language, "tg_error_X").format(ex),
            )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["test"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.reply
)
def CmdTestReplyUser(client: pyrogram.Client, msg: pyrogram.types.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = (
            db_management.RChatPlugin.get_or_none(plugin="interact", chat=msg.chat.id)
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == "private"
    if allowed:
        if msg.reply_to_message.service and msg.reply_to_message.new_chat_members:
            if (
                msg.reply_to_message.new_chat_members[0].id
                != msg.reply_to_message.from_user.id
            ):
                msg.reply_to_message.new_chat_members.append(
                    msg.reply_to_message.from_user
                )
            if len(msg.reply_to_message.new_chat_members) > 1:
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(msg.chat.settings.language, "select_target"),
                    reply_markup=pyrogram.types.InlineKeyboardMarkup(
                        keyboards.BuildActionOnAddedUsersList(
                            chat_settings=msg.chat.settings,
                            action="test",
                            new_chat_members=msg.reply_to_message.new_chat_members,
                        )
                    ),
                )
            else:
                try:
                    client.send_chat_action(
                        chat_id=msg.reply_to_message.from_user.id, action="typing"
                    )
                except Exception as ex:
                    print(ex)
                    traceback.print_exc()
                    methods.ReplyText(
                        client=client,
                        msg=msg,
                        text=_(msg.chat.settings.language, "tg_error_X").format(ex),
                    )
        else:
            try:
                client.send_chat_action(
                    chat_id=msg.reply_to_message.from_user.id, action="typing"
                )
            except Exception as ex:
                print(ex)
                traceback.print_exc()
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(msg.chat.settings.language, "tg_error_X").format(ex),
                )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=utils.GetCommandsVariants(commands=["test"], del_=True),
        prefixes=["/", "!", "#", "."],
    )
    & ~pyrogram.filters.reply
)
def CmdTestChat(client: pyrogram.Client, msg: pyrogram.types.Message):
    allowed = False
    if msg.chat.id < 0:
        r_chat_plugin: db_management.RChatPlugin = (
            db_management.RChatPlugin.get_or_none(plugin="interact", chat=msg.chat.id)
        )
        allowed = (
            r_chat_plugin.min_rank <= msg.r_user_chat.rank
            and r_chat_plugin.is_enabled_on_chat
        )
    else:
        allowed = msg.chat.type == "private"
    if allowed:
        user_id = utils.ResolveCommandToId(client=client, value=msg.command[1], msg=msg)
        if isinstance(user_id, str):
            methods.ReplyText(client=client, msg=msg, text=user_id)
        else:
            try:
                client.send_chat_action(chat_id=user_id, action="typing")
            except Exception as ex:
                print(ex)
                traceback.print_exc()
                methods.ReplyText(
                    client=client,
                    msg=msg,
                    text=_(msg.chat.settings.language, "tg_error_X").format(ex),
                )
