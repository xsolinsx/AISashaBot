import datetime
import re
import time
import traceback
import typing

import peewee
import pyrogram

import db_management
import keyboards
import methods
import my_filters
import utils

_ = utils.GetLocalizedString


@pyrogram.Client.on_message(group=-11)
def PreMessage(client: pyrogram.Client, msg: pyrogram.Message):
    # as this is the first handler of this type, if the db is locked wait
    while db_management.DB.is_stopped():
        time.sleep(1)
    # save everything to db
    msg = db_management.DBObject(obj=msg, client=client)
    utils.InstantiateKickedPeopleDictionary(chat_id=msg.chat.id)
    utils.InstantiateInvitedPeopleDictionary(chat_id=msg.chat.id)
    # print("######################\nMESSAGE")
    print(utils.PrintMessage(msg))
    # check for linked channel, ignore message
    if msg.from_user is None:
        msg.stop_propagation()


@pyrogram.Client.on_callback_query(group=-11)
def PreCallbackQuery(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    # as this is the first handler of this type, if the db is locked wait
    while db_management.DB.is_stopped():
        time.sleep(1)
    # save everything to db
    cb_qry = db_management.DBObject(obj=cb_qry, client=client)
    utils.InstantiateKickedPeopleDictionary(chat_id=cb_qry.message.chat.id)
    utils.InstantiateInvitedPeopleDictionary(chat_id=cb_qry.message.chat.id)
    # print("######################\nCALLBACK QUERY")
    print(utils.PrintCallbackQuery(cb_qry))


# @pyrogram.Client.on_deleted_messages(group=-11)
def PreDeletedMessages(client: pyrogram.Client, msgs: typing.List[pyrogram.Message]):
    # as this is the first handler of this type, if the db is locked wait
    while db_management.DB.is_stopped():
        time.sleep(1)
    tmp = ""
    tmp = " ".join([msg.message_id for msg in msgs.messages])
    # print("######################\nDELETED MESSAGES")
    print(
        "[UTC {0}] >>> Deleted messages\nCount: {1}\nMessage IDs: {2}".format(
            datetime.datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S"),
            msgs.total_count,
            tmp,
        )
    )


# @pyrogram.Client.on_user_status(group=-11)
def PreUserStatus(client: pyrogram.Client, user: pyrogram.User):
    # as this is the first handler of this type, if the db is locked wait
    while db_management.DB.is_stopped():
        time.sleep(1)
    # print("######################\nUSER STATUS")
    print(
        +f"{utils.PrintUser(user=user)} Status: {user.status} Last seen "
        + (
            f"UTC {datetime.datetime.utcfromtimestamp(user.last_online_date)}"
            if user.last_online_date
            else None
        )
    )


# @pyrogram.Client.on_raw_update(group=-11)
def PreProcessRawUpdate(
    client: pyrogram.Client,
    update: pyrogram.api.types.Update,
    users: typing.Dict[int, pyrogram.api.types.User],
    chats: typing.Dict[
        int, typing.Union[pyrogram.api.types.Chat, pyrogram.api.types.Channel]
    ],
):
    # as this is the first handler of this type, if the db is locked wait
    while db_management.DB.is_stopped():
        time.sleep(1)
    print("######################\nRAW UPDATE")
    print(str(update))


@pyrogram.Client.on_callback_query(
    my_filters.callback_data(data="cancel")
    | my_filters.callback_regex(pattern=r"^cancel (.+)", flags=re.I),
    group=-7,
)
def CbQryCancelTmpSteps(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    if cb_qry.message.chat.id in utils.tmp_steps:
        original_cb_qry, variable = utils.tmp_steps[cb_qry.message.chat.id]
        if cb_qry.from_user.id == original_cb_qry.from_user.id:
            utils.tmp_steps.pop(cb_qry.message.chat.id)
            methods.CallbackQueryAnswer(
                cb_qry=cb_qry, text=_(cb_qry.from_user.settings.language, "cancelled")
            )
    parameters = cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data.split(
        " "
    )

    utils.Log(
        client=client,
        chat_id=int(parameters[2] if len(parameters) > 2 else cb_qry.message.chat.id),
        executer=cb_qry.from_user.id,
        action=f"{cb_qry.data.lower()}",
        target=int(parameters[2] if len(parameters) > 2 else cb_qry.message.chat.id),
    )

    if len(parameters) == 1:
        try:
            cb_qry.message.delete()
        except pyrogram.errors.MessageDeleteForbidden as ex:
            print(ex)
            traceback.print_exc()
    else:
        kybrd = parameters[1]
        if kybrd == "mainsettings":
            chat_id = int(parameters[2])
            chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                chat_id=chat_id
            )
            cb_qry.message.edit_text(
                text=_(cb_qry.from_user.settings.language, "settings")
                + f" {utils.PrintChat(chat=chat_settings.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildGroupSettingsMenu(
                        chat_settings=chat_settings, current_keyboard="mainsettings",
                    )
                ),
            )
        elif kybrd == "greetingsettings":
            chat_id = int(parameters[2])
            chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                chat_id=chat_id
            )
            cb_qry.message.edit_text(
                text=_(cb_qry.from_user.settings.language, "settings")
                + f" {utils.PrintChat(chat=chat_settings.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildGroupSettingsMenu(
                        chat_settings=chat_settings,
                        current_keyboard="greetingsettings",
                    )
                ),
            )
        elif kybrd == "invitesettings":
            chat_id = int(parameters[2])
            chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                chat_id=chat_id
            )
            cb_qry.message.edit_text(
                text=_(cb_qry.from_user.settings.language, "settings")
                + f" {utils.PrintChat(chat=chat_settings.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildGroupSettingsMenu(
                        chat_settings=chat_settings, current_keyboard="invitesettings",
                    )
                ),
            )
        elif kybrd == "mysettings":
            cb_qry.message.edit_text(
                text=_(cb_qry.from_user.settings.language, "mysettings"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildPrivateSettingsMenu(
                        user_settings=cb_qry.from_user.settings
                    )
                ),
            )
        elif kybrd == "censorships":
            chat_id = int(parameters[2])
            chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                chat_id=chat_id
            )
            cb_qry.message.edit_text(
                text=_(chat_settings.language, "censorships")
                + f" {utils.PrintChat(chat=chat_settings.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildCensorshipsList(chat_settings=chat_settings, page=0)
                ),
            )
        elif kybrd == "extras":
            chat_id = int(parameters[2])
            chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                chat_id=chat_id
            )
            cb_qry.message.edit_text(
                text=_(chat_settings.language, "extras")
                + f" {utils.PrintChat(chat=chat_settings.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildExtraList(chat_settings=chat_settings, page=0)
                ),
            )
        elif kybrd == "whitelistedchats":
            chat_id = int(parameters[2])
            chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                chat_id=chat_id
            )
            cb_qry.message.edit_text(
                text=_(chat_settings.language, "whitelisted_chats")
                + f" {utils.PrintChat(chat=chat_settings.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedChatsList(
                        chat_settings=chat_settings, page=0
                    )
                ),
            )
        elif kybrd == "whitelistedgbanned":
            chat_id = int(parameters[2])
            chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                chat_id=chat_id
            )
            cb_qry.message.edit_text(
                text=_(chat_settings.language, "whitelistedgbanned_users")
                + f" {utils.PrintChat(chat=chat_settings.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedGbannedUsersList(
                        chat_settings=chat_settings, page=0
                    )
                ),
            )
        elif kybrd == "whitelisted":
            chat_id = int(parameters[2])
            chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                chat_id=chat_id
            )
            cb_qry.message.edit_text(
                text=_(chat_settings.language, "whitelisted_users")
                + f" {utils.PrintChat(chat=chat_settings.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildWhitelistedUsersList(
                        chat_settings=chat_settings, page=0
                    )
                ),
            )
        elif kybrd == "gbanned":
            cb_qry.message.edit_text(
                text=_(cb_qry.from_user.settings.language, "globally_banned_users"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildGloballyBannedUsersList(
                        chat_settings=cb_qry.from_user.settings, page=0
                    )
                ),
            )
        elif kybrd == "blocked":
            cb_qry.message.edit_text(
                text=_(cb_qry.from_user.settings.language, "blocked_users"),
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildBlockedUsersList(
                        chat_settings=cb_qry.from_user.settings, page=0
                    )
                ),
            )
        elif kybrd == "alternatives":
            chat_id = int(parameters[2])
            chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                chat_id=chat_id
            )
            cb_qry.message.edit_text(
                text=_(cb_qry.from_user.settings.language, "alternatives")
                + f" {utils.PrintChat(chat=chat_settings.chat)}",
                reply_markup=pyrogram.InlineKeyboardMarkup(
                    keyboards.BuildAlternativeCommandsList(
                        chat_settings=chat_settings, page=0
                    )
                ),
            )


@pyrogram.Client.on_message(
    pyrogram.Filters.command(
        commands=utils.GetCommandsVariants(commands=["cancel"], del_=True)
    ),
    group=-7,
)
def CmdCancelTmpSteps(client: pyrogram.Client, msg: pyrogram.Message):
    msg.reply_chat_action(action="cancel")
    if msg.chat.id in utils.tmp_steps:
        original_cb_qry, variable = utils.tmp_steps[msg.chat.id]
        if msg.from_user.id == original_cb_qry.from_user.id:
            utils.tmp_steps.pop(msg.chat.id)
            parameters = original_cb_qry.message.reply_markup.inline_keyboard[0][
                0
            ].callback_data.split(" ")
            utils.Log(
                client=client,
                chat_id=int(parameters[1] if len(parameters) > 1 else msg.chat.id),
                executer=msg.from_user.id,
                action=f"{original_cb_qry.message.reply_markup.inline_keyboard[0][0].callback_data}",
                target=int(parameters[1] if len(parameters) > 1 else msg.chat.id),
            )
            methods.ReplyText(
                client=client,
                msg=original_cb_qry.message,
                text=_(msg.from_user.settings.language, "cancelled"),
            )
            kybrd = parameters[0].replace("useless", "")

            if kybrd == "mainsettings":
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                original_cb_qry.message.edit_text(
                    text=_(msg.from_user.settings.language, "settings")
                    + f" {utils.PrintChat(chat=chat_settings.chat)}",
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildGroupSettingsMenu(
                            chat_settings=chat_settings,
                            current_keyboard="mainsettings",
                        )
                    ),
                )
            elif kybrd == "greetingsettings":
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                original_cb_qry.message.edit_text(
                    text=_(msg.from_user.settings.language, "settings")
                    + f" {utils.PrintChat(chat=chat_settings.chat)}",
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildGroupSettingsMenu(
                            chat_settings=chat_settings,
                            current_keyboard="greetingsettings",
                        )
                    ),
                )
            elif kybrd == "invitesettings":
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                original_cb_qry.message.edit_text(
                    text=_(msg.from_user.settings.language, "settings")
                    + f" {utils.PrintChat(chat=chat_settings.chat)}",
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildGroupSettingsMenu(
                            chat_settings=chat_settings,
                            current_keyboard="invitesettings",
                        )
                    ),
                )
            elif kybrd == "mysettings":
                original_cb_qry.message.edit_text(
                    text=_(msg.from_user.settings.language, "mysettings"),
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildPrivateSettingsMenu(
                            user_settings=msg.from_user.settings
                        )
                    ),
                )
            elif kybrd == "censorships":
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                original_cb_qry.message.edit_text(
                    text=_(chat_settings.language, "censorships")
                    + f" {utils.PrintChat(chat=chat_settings.chat)}",
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildCensorshipsList(
                            chat_settings=chat_settings, page=0
                        )
                    ),
                )
            elif kybrd == "extras":
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                original_cb_qry.message.edit_text(
                    text=_(chat_settings.language, "extras")
                    + f" {utils.PrintChat(chat=chat_settings.chat)}",
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildExtraList(chat_settings=chat_settings, page=0)
                    ),
                )
            elif kybrd == "whitelistedchats":
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                original_cb_qry.message.edit_text(
                    text=_(chat_settings.language, "whitelisted_chats")
                    + f" {utils.PrintChat(chat=chat_settings.chat)}",
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildWhitelistedChatsList(
                            chat_settings=chat_settings, page=0
                        )
                    ),
                )
            elif kybrd == "whitelistedgbanned":
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                original_cb_qry.message.edit_text(
                    text=_(chat_settings.language, "whitelistedgbanned_users")
                    + f" {utils.PrintChat(chat=chat_settings.chat)}",
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildGloballyBannedUsersList(
                            chat_settings=chat_settings, page=0
                        )
                    ),
                )
            elif kybrd == "whitelisted":
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                original_cb_qry.message.edit_text(
                    text=_(chat_settings.language, "whitelisted_users")
                    + f" {utils.PrintChat(chat=chat_settings.chat)}",
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildWhitelistedUsersList(
                            chat_settings=chat_settings, page=0
                        )
                    ),
                )
            elif kybrd == "gbanned":
                original_cb_qry.message.edit_text(
                    text=_(msg.from_user.settings.language, "globally_banned_users"),
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildGloballyBannedUsersList(
                            chat_settings=msg.from_user.settings, page=0
                        )
                    ),
                )
            elif kybrd == "blocked":
                original_cb_qry.message.edit_text(
                    text=_(msg.from_user.settings.language, "blocked_users"),
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildBlockedUsersList(
                            chat_settings=msg.from_user.settings, page=0
                        )
                    ),
                )
            elif kybrd == "alternatives":
                original_cb_qry.message.edit_text(
                    text=_(msg.from_user.settings.language, "alternatives")
                    + f" {utils.PrintChat(chat=chat_settings.chat)}",
                    reply_markup=pyrogram.InlineKeyboardMarkup(
                        keyboards.BuildAlternativeCommandsList(
                            chat_settings=chat_settings, page=0
                        )
                    ),
                )


@pyrogram.Client.on_message(~pyrogram.Filters.service, group=-7)
def ProcessTmpSteps(client: pyrogram.Client, msg: pyrogram.Message):
    if msg.chat.id in utils.tmp_steps:
        original_cb_qry, variable = utils.tmp_steps[msg.chat.id]
        if msg.from_user.id == original_cb_qry.from_user.id:
            text = ""
            parameters = original_cb_qry.message.reply_markup.inline_keyboard[0][
                0
            ].callback_data.split(" ")
            success = True
            chat_id = None
            chat_settings = None
            dont_pop = False
            if variable == "settings set_goodbye" or variable == "settings set_welcome":
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                media_variable = None
                if msg.media:
                    media, type_ = utils.ExtractMedia(msg=msg)
                    if hasattr(media, "file_id"):
                        media_variable = f"###{media.file_id}"
                        if msg.caption:
                            media_variable += f"${msg.caption}"

                db_management.ChatExtras.update(
                    value=media_variable if media_variable else msg.text,
                    is_media=media_variable is not None,
                    original_chat_id=msg.chat.id if media_variable else None,
                    original_message_id=msg.message_id if media_variable else None,
                ).where(
                    (db_management.ChatExtras.chat_id == chat_settings.chat_id)
                    & (
                        db_management.ChatExtras.key
                        == variable.replace("settings set_", "")
                    )
                    & (db_management.ChatExtras.is_group_data)
                ).execute()
            elif (
                variable == "settings set_rules"
                or variable == "settings set_welcome_buttons"
            ):
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                if variable.replace("settings set_", "") == "welcome_buttons":
                    welcome_buttons = keyboards.BuildWelcomeButtonsKeyboard(
                        welcome_buttons=msg.text
                    )
                    if len(welcome_buttons) <= 0 or len(welcome_buttons[0]) <= 0:
                        # malformed keyboard
                        success = False

                if success:
                    db_management.ChatExtras.update(
                        value=msg.text,
                        is_media=False,
                        original_chat_id=None,
                        original_message_id=None,
                    ).where(
                        (db_management.ChatExtras.chat_id == chat_settings.chat_id)
                        & (
                            db_management.ChatExtras.key
                            == variable.replace("settings set_", "")
                        )
                        & (db_management.ChatExtras.is_group_data)
                    ).execute()
            elif variable == "settings set_link":
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                chat_settings.link = msg.text
                try:
                    chat_settings.save()
                except Exception as ex:
                    print(ex)
                    traceback.print_exc()
                    text += f"\n{ex}"
                else:
                    utils.Log(
                        client=client,
                        chat_id=chat_id,
                        executer=msg.from_user.id,
                        action=f"{variable} = {msg.text}",
                        target=chat_id,
                    )
            elif variable == "mysettings set_nickname":
                tmp_nicknames = set()
                for nickname in msg.text.split("|"):
                    if len(tmp_nicknames) < utils.config["max_nicknames"]:
                        if len(nickname.strip()) > 2:
                            # escape because people could set a regex as nickname
                            tmp_nicknames.add(re.escape(nickname.strip()))
                    else:
                        break

                if tmp_nicknames:
                    nickname = "|".join(tmp_nicknames)
                    msg.from_user.settings.nickname = nickname
                    try:
                        msg.from_user.settings.save()
                    except Exception as ex:
                        print(ex)
                        traceback.print_exc()
                        text += f"\n{ex}"
                else:
                    # nickname too short
                    success = False
            elif variable == "censorships add text":
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                if db_management.ChatCensorships.get_or_none(
                    chat_id=chat_id, value=msg.text, is_media=False, is_regex=False
                ):
                    db_management.ChatCensorships.update(
                        value=msg.text, is_media=False, is_regex=False
                    ).where(
                        (db_management.ChatCensorships.chat_id == chat_id)
                    ).execute()
                else:
                    db_management.ChatCensorships.create(
                        chat=chat_id, value=msg.text, is_media=False, is_regex=False
                    )
                utils.Log(
                    client=client,
                    chat_id=chat_id,
                    executer=msg.from_user.id,
                    action=f"{variable} = {msg.text}",
                    target=chat_id,
                )
            elif variable == "censorships add media":
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                media, type_ = utils.ExtractMedia(msg=msg)
                if media:
                    if db_management.ChatCensorships.get_or_none(
                        chat_id=chat_id,
                        value=media.media_id,
                        is_media=True,
                        is_regex=False,
                        original_chat_id=msg.chat.id,
                        original_message_id=msg.message_id,
                    ):
                        db_management.ChatCensorships.update(
                            value=media.media_id, is_media=True, is_regex=False
                        ).where(
                            (db_management.ChatCensorships.chat_id == chat_id)
                        ).execute()
                    else:
                        db_management.ChatCensorships.create(
                            chat=chat_id,
                            value=media.media_id,
                            is_media=True,
                            is_regex=False,
                            original_chat_id=msg.chat.id,
                            original_message_id=msg.message_id,
                        )
                    utils.Log(
                        client=client,
                        chat_id=chat_id,
                        executer=msg.from_user.id,
                        action=f"{variable} = {media.media_id}",
                        target=chat_id,
                    )
            elif variable == "censorships add regex":
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                if db_management.ChatCensorships.get_or_none(
                    chat_id=chat_id, value=msg.text, is_media=False, is_regex=True
                ):
                    db_management.ChatCensorships.update(
                        value=msg.text, is_media=False, is_regex=True
                    ).where(
                        (db_management.ChatCensorships.chat_id == chat_id)
                    ).execute()
                else:
                    db_management.ChatCensorships.create(
                        chat=chat_id, value=msg.text, is_media=False, is_regex=True
                    )
                utils.Log(
                    client=client,
                    chat_id=chat_id,
                    executer=msg.from_user.id,
                    action=f"{variable} = {msg.text}",
                    target=chat_id,
                )
            elif variable.startswith("extras set regex") or variable.startswith(
                "extras set text"
            ):
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                if (
                    variable == "extras set text text"
                    or variable == "extras set text media"
                    or variable == "extras set regex text"
                    or variable == "extras set regex media"
                ):
                    methods.ReplyText(
                        client=client,
                        msg=msg,
                        text=_(msg.from_user.settings.language, "send_extra_value"),
                    )
                    utils.tmp_steps[msg.chat.id] = (
                        original_cb_qry,
                        f"{variable} {msg.text}",
                    )
                    dont_pop = True
                elif (
                    variable.startswith("extras set text text ")
                    or variable.startswith("extras set text media ")
                    or variable.startswith("extras set regex text ")
                    or variable.startswith("extras set regex media ")
                ):
                    tmp = variable.replace("extras set ", "", 1)
                    tmp = tmp.split(" ")
                    key_type, value_type = tmp[0], tmp[1]
                    key = " ".join(tmp[2:])
                    value = None
                    if value_type == "media":
                        media, type_ = utils.ExtractMedia(msg=msg)
                        if hasattr(media, "file_id"):
                            value = f"###{media.file_id}"
                            if msg.caption:
                                value += f"${msg.caption}"
                    else:
                        value = msg.text
                    if value:
                        if db_management.ChatExtras.get_or_none(
                            chat_id=chat_id, key=key
                        ):
                            db_management.ChatExtras.update(
                                value=value,
                                is_media=value_type == "media",
                                is_regex=key_type == "regex",
                                original_chat_id=msg.chat.id
                                if value_type == "media"
                                else None,
                                original_message_id=msg.message_id
                                if value_type == "media"
                                else None,
                            ).where(
                                (db_management.ChatExtras.chat_id == chat_id)
                                & (db_management.ChatExtras.key == key)
                            ).execute()
                        else:
                            db_management.ChatExtras.create(
                                chat=chat_id,
                                key=key,
                                value=value,
                                is_media=value_type == "media",
                                is_regex=key_type == "regex",
                                original_chat_id=msg.chat.id
                                if value_type == "media"
                                else None,
                                original_message_id=msg.message_id
                                if value_type == "media"
                                else None,
                            )
                        utils.Log(
                            client=client,
                            chat_id=chat_id,
                            executer=msg.from_user.id,
                            action=f"{key_type}:{key} = {value_type}:{value}",
                            target=chat_id,
                        )
                    else:
                        # no value recognized
                        success = False
                else:
                    # no value recognized
                    success = False
            elif variable == "whitelistedchats add":
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                whitelisted_chat_id = None
                tmp = str(utils.CleanLink(url=msg.text))
                if utils.LINK_REGEX.findall(string=tmp):
                    # t.me/joinchat/<blablabla>
                    link_parameters = (None, None, None)
                    try:
                        link_parameters = utils.ResolveInviteLink(link=tmp)
                    except Exception as ex:
                        print(ex)
                        traceback.print_exc()
                    if link_parameters[1]:
                        whitelisted_chat_id = link_parameters[1]
                else:
                    # anything else
                    whitelisted_chat_id = utils.ResolveCommandToId(
                        client=client, value=msg.text
                    )
                    if isinstance(whitelisted_chat_id, str) or whitelisted_chat_id > 0:
                        whitelisted_chat_id = None

                if whitelisted_chat_id:
                    if not db_management.ChatWhitelistedChats.get_or_none(
                        chat=chat_id, whitelisted_chat=whitelisted_chat_id
                    ):
                        db_management.ChatWhitelistedChats.create(
                            chat=chat_id, whitelisted_chat=whitelisted_chat_id
                        )
                        utils.Log(
                            client=client,
                            chat_id=chat_id,
                            executer=msg.from_user.id,
                            action=f"{variable} {msg.text} ({whitelisted_chat_id})",
                            target=chat_id,
                        )
                else:
                    success = False
            elif variable == "whitelistedgbanned add":
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                user_id = utils.ResolveCommandToId(client=client, value=msg.text)
                if isinstance(user_id, str) or int(user_id) < 0:
                    success = False
                else:
                    r_user_chat = db_management.RUserChat.get_or_none(
                        user_id=user_id, chat_id=chat_id
                    )
                    if not r_user_chat:
                        r_user_chat = db_management.RUserChat.create(
                            user_id=user_id, chat_id=chat_id
                        )
                    r_user_chat.is_global_ban_whitelisted = True
                    r_user_chat.save()
                    utils.Log(
                        client=client,
                        chat_id=chat_id,
                        executer=msg.from_user.id,
                        action=f"{variable} {msg.text} ({user_id})",
                        target=chat_id,
                    )
            elif variable == "whitelisted add":
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                user_id = utils.ResolveCommandToId(client=client, value=msg.text)
                if isinstance(user_id, str) or int(user_id) < 0:
                    success = False
                else:
                    r_user_chat = db_management.RUserChat.get_or_none(
                        user_id=user_id, chat_id=chat_id
                    )
                    if not r_user_chat:
                        r_user_chat = db_management.RUserChat.create(
                            user_id=user_id, chat_id=chat_id
                        )
                    r_user_chat.is_whitelisted = True
                    r_user_chat.save()
                    utils.Log(
                        client=client,
                        chat_id=chat_id,
                        executer=msg.from_user.id,
                        action=f"{variable} {msg.text} ({user_id})",
                        target=chat_id,
                    )
            elif variable == "gbanned add":
                chat_settings: db_management.UserSettings = msg.from_user.settings
                seconds = utils.config["default_gban"]
                reason = ""
                splitted = msg.text.split(" ")
                if len(splitted) > 1:
                    if utils.IsInt(splitted[1]):
                        seconds = int(splitted[1])
                        reason = " ".join(splitted[2:])
                    else:
                        reason = " ".join(splitted[2:])
                user_id = utils.ResolveCommandToId(client=client, value=splitted[0])
                if isinstance(user_id, str) or int(user_id) < 0:
                    success = False
                else:
                    text = methods.GBan(
                        client=client,
                        executer=msg.from_user.id,
                        target=user_id,
                        chat_id=msg.from_user.id,
                        seconds=seconds,
                        reasons=reason,
                    )
                    if text:
                        utils.Log(
                            client=client,
                            chat_id=user_id,
                            executer=msg.from_user.id,
                            action=f"{variable} {splitted[0]} ({user_id}) {seconds} {reason}",
                            target=user_id,
                        )
            elif variable == "blocked add":
                chat_settings: db_management.UserSettings = msg.from_user.settings
                seconds = utils.config["default_block"]
                reason = ""
                splitted = msg.text.split(" ")
                if len(splitted) > 1:
                    if utils.IsInt(splitted[1]):
                        seconds = int(splitted[1])
                        reason = " ".join(splitted[2:])
                    else:
                        reason = " ".join(splitted[2:])
                user_id = utils.ResolveCommandToId(client=client, value=splitted[0])
                if isinstance(user_id, str) or int(user_id) < 0:
                    success = False
                else:
                    text = methods.Block(
                        client=client,
                        executer=msg.from_user.id,
                        target=user_id,
                        chat_id=msg.from_user.id,
                        seconds=seconds,
                        reasons=reason,
                    )
                    if text:
                        utils.Log(
                            client=client,
                            chat_id=user_id,
                            executer=msg.from_user.id,
                            action=f"{variable} {splitted[0]} ({user_id}) {seconds} {reason}",
                            target=user_id,
                        )
            elif variable.startswith("alternatives set"):
                chat_id = int(parameters[1])
                chat_settings: db_management.ChatSettings = db_management.ChatSettings.get(
                    chat_id=chat_id
                )
                if variable == "alternatives set":
                    if msg.text:
                        # remove prefix if present
                        original = (
                            msg.text
                            if not msg.text.startswith(("@", "/", "!", "#", "."))
                            else msg.text[1:]
                        )
                        methods.ReplyText(
                            client=client,
                            msg=msg,
                            text=_(
                                msg.from_user.settings.language,
                                "send_alternative_command_X",
                            ).format(original),
                        )
                        utils.tmp_steps[msg.chat.id] = (
                            original_cb_qry,
                            f"{variable} {original}",
                        )
                        dont_pop = True
                    else:
                        success = False
                else:
                    original = variable.replace("alternatives set ", "", 1)
                    alternative = None
                    is_media = False
                    if msg.media:
                        media, type_ = utils.ExtractMedia(msg=msg)
                        if hasattr(media, "file_id"):
                            alternative = media.file_id
                            is_media = True
                    else:
                        alternative = msg.text
                    if alternative:
                        if db_management.ChatAlternatives.get_or_none(
                            chat_id=chat_id, alternative=alternative
                        ):
                            db_management.ChatAlternatives.update(
                                original=original,
                                alternative=alternative,
                                is_media=is_media,
                                original_chat_id=msg.chat.id if is_media else None,
                                original_message_id=msg.message_id
                                if is_media
                                else None,
                            ).where(
                                (db_management.ChatAlternatives.chat_id == chat_id)
                                & (db_management.ChatAlternatives.original == original)
                                & (
                                    db_management.ChatAlternatives.alternative
                                    == alternative
                                )
                            ).execute()
                        else:
                            db_management.ChatAlternatives.create(
                                chat=chat_id,
                                original=original,
                                alternative=alternative,
                                is_media=is_media,
                                original_chat_id=msg.chat.id if is_media else None,
                                original_message_id=msg.message_id
                                if is_media
                                else None,
                            )
                        utils.Log(
                            client=client,
                            chat_id=chat_id,
                            executer=msg.from_user.id,
                            action=f"{variable} {alternative}",
                            target=chat_id,
                        )
                    else:
                        # no value recognized
                        success = False
            elif variable == "delfrom" and (msg.text or msg.caption) == "delto":
                pass
            elif variable == "delto" and (msg.text or msg.caption) == "delall":
                pass
            else:
                # unrecognized variable
                success = False

            if not dont_pop:
                utils.tmp_steps.pop(msg.chat.id)
                if success:
                    methods.ReplyText(
                        client=client,
                        msg=msg,
                        text=_(msg.from_user.settings.language, "success"),
                    )
                    if variable.startswith("settings"):
                        kybrd = parameters[0].replace("useless", "")
                        text = (
                            _(chat_settings.language, kybrd).format(
                                _(chat_settings.language, "settings")
                            )
                            + f" {utils.PrintChat(chat=chat_settings.chat)}"
                            + text,
                        )

                        original_cb_qry.message.edit_text(
                            text=text,
                            reply_markup=pyrogram.InlineKeyboardMarkup(
                                keyboards.BuildGroupSettingsMenu(
                                    chat_settings=chat_settings, current_keyboard=kybrd,
                                )
                            ),
                        )
                    elif variable.startswith("mysettings"):
                        original_cb_qry.message.edit_text(
                            text=_(msg.from_user.settings.language, "mysettings"),
                            reply_markup=pyrogram.InlineKeyboardMarkup(
                                keyboards.BuildPrivateSettingsMenu(
                                    user_settings=msg.from_user.settings
                                )
                            ),
                        )
                    elif variable.startswith("censorships"):
                        original_cb_qry.message.edit_text(
                            text=_(chat_settings.language, "censorships")
                            + f" {utils.PrintChat(chat=chat_settings.chat)}",
                            reply_markup=pyrogram.InlineKeyboardMarkup(
                                keyboards.BuildCensorshipsList(
                                    chat_settings=chat_settings, page=int(parameters[2])
                                )
                            ),
                        )
                    elif variable.startswith("extras"):
                        original_cb_qry.message.edit_text(
                            text=_(chat_settings.language, "extras")
                            + f" {utils.PrintChat(chat=chat_settings.chat)}",
                            reply_markup=pyrogram.InlineKeyboardMarkup(
                                keyboards.BuildExtraList(
                                    chat_settings=chat_settings,
                                    page=int(parameters[2]),
                                )
                            ),
                        )
                    elif variable.startswith("whitelistedchats"):
                        original_cb_qry.message.edit_text(
                            text=_(chat_settings.language, "whitelisted_chats")
                            + f" {utils.PrintChat(chat=chat_settings.chat)}",
                            reply_markup=pyrogram.InlineKeyboardMarkup(
                                keyboards.BuildWhitelistedChatsList(
                                    chat_settings=chat_settings,
                                    page=int(parameters[2]),
                                )
                            ),
                        )
                    elif variable.startswith("whitelistedgbanned"):
                        original_cb_qry.message.edit_text(
                            text=_(chat_settings.language, "whitelistedgbanned_users")
                            + f" {utils.PrintChat(chat=chat_settings.chat)}",
                            reply_markup=pyrogram.InlineKeyboardMarkup(
                                keyboards.BuildWhitelistedGbannedUsersList(
                                    chat_settings=chat_settings,
                                    page=int(parameters[2]),
                                )
                            ),
                        )
                    elif variable.startswith("whitelisted"):
                        original_cb_qry.message.edit_text(
                            text=_(chat_settings.language, "whitelisted_users")
                            + f" {utils.PrintChat(chat=chat_settings.chat)}",
                            reply_markup=pyrogram.InlineKeyboardMarkup(
                                keyboards.BuildWhitelistedUsersList(
                                    chat_settings=chat_settings,
                                    page=int(parameters[2]),
                                )
                            ),
                        )
                    elif variable.startswith("gbanned"):
                        original_cb_qry.message.edit_text(
                            text=_(chat_settings.language, "globally_banned_users"),
                            reply_markup=pyrogram.InlineKeyboardMarkup(
                                keyboards.BuildGloballyBannedUsersList(
                                    chat_settings=chat_settings,
                                    page=int(parameters[1]),
                                )
                            ),
                        )
                    elif variable.startswith("blocked"):
                        original_cb_qry.message.edit_text(
                            text=_(chat_settings.language, "blocked_users"),
                            reply_markup=pyrogram.InlineKeyboardMarkup(
                                keyboards.BuildBlockedUsersList(
                                    chat_settings=chat_settings,
                                    page=int(parameters[1]),
                                )
                            ),
                        )
                    elif variable.startswith("alternatives"):
                        original_cb_qry.message.edit_text(
                            text=_(chat_settings.language, "alternatives")
                            + f" {utils.PrintChat(chat=chat_settings.chat)}",
                            reply_markup=pyrogram.InlineKeyboardMarkup(
                                keyboards.BuildAlternativeCommandsList(
                                    chat_settings=chat_settings,
                                    page=int(parameters[2]),
                                )
                            ),
                        )
                else:
                    methods.ReplyText(
                        client=client,
                        msg=msg,
                        text=_(msg.from_user.settings.language, "error_try_again"),
                    )


@pyrogram.Client.on_message(group=1)
def PostMessageCleanUp(client: pyrogram.Client, msg: pyrogram.Message):
    # delete resolved objects older than X minutes
    subquery: peewee.ModelSelect = db_management.ResolvedObjects.select().where(
        db_management.ResolvedObjects.timestamp
        < datetime.datetime.utcnow()
        - datetime.timedelta(
            seconds=utils.config["tmp_dicts_expiration"]["resolvedObjects"]
        )
    )
    db_management.ResolvedObjects.delete().where(
        db_management.ResolvedObjects.id.in_(subquery)
    ).execute()

    msg.continue_propagation()


@pyrogram.Client.on_message(
    (
        pyrogram.Filters.regex(pattern="^[/!#.]del", flags=re.I)
        | pyrogram.Filters.regex(pattern="^[/!#.]delete", flags=re.I)
    )
    & pyrogram.Filters.group,
    group=1,
)
def PostDeleteMessage(client: pyrogram.Client, msg: pyrogram.Message):
    try:
        msg.delete()
    except pyrogram.errors.MessageDeleteForbidden as ex:
        print(ex)
        traceback.print_exc()
        methods.ReplyText(
            client=client,
            msg=msg,
            text=_(msg.chat.settings.language, "cant_delete_message"),
        )

    msg.continue_propagation()


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^useless", flags=re.I), group=-8
)
def CbQryUseless(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry, text=_(cb_qry.from_user.settings.language, "useless_button")
    )
    cb_qry.stop_propagation()


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^(\w+)_all", flags=re.I), group=-7,
)
def CbQryActionAll(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    if utils.IsJuniorModOrHigher(
        user_id=cb_qry.from_user.id,
        chat_id=cb_qry.message.chat.id,
        r_user_chat=cb_qry.r_user_chat,
    ):
        rows = cb_qry.message.reply_markup.inline_keyboard[1:]
        text = ""
        for row in rows:
            action, user_id = row[1].callback_data.split(" ")
            if action == "invite":
                text += f"{user_id}: " + methods.Invite(
                    client=client,
                    executer=cb_qry.from_user.id,
                    target=user_id,
                    chat_id=cb_qry.message.chat.id,
                    r_executer_chat=cb_qry.r_user_chat,
                    chat_settings=cb_qry.message.chat.settings,
                )
            elif action == "warn":
                text += f"{user_id}: " + methods.Warn(
                    client=client,
                    executer=cb_qry.from_user.id,
                    target=user_id,
                    chat_id=cb_qry.message.chat.id,
                    r_executer_chat=cb_qry.r_user_chat,
                    chat_settings=cb_qry.message.chat.settings,
                )
            elif action == "unwarn":
                text += f"{user_id}: " + methods.Unwarn(
                    client=client,
                    executer=cb_qry.from_user.id,
                    target=user_id,
                    chat_id=cb_qry.message.chat.id,
                    r_executer_chat=cb_qry.r_user_chat,
                    chat_settings=cb_qry.message.chat.settings,
                )
            elif action == "unwarnall":
                text += f"{user_id}: " + methods.UnwarnAll(
                    client=client,
                    executer=cb_qry.from_user.id,
                    target=user_id,
                    chat_id=cb_qry.message.chat.id,
                    r_executer_chat=cb_qry.r_user_chat,
                    chat_settings=cb_qry.message.chat.settings,
                )
            elif action == "kick":
                text += f"{user_id}: " + methods.Kick(
                    client=client,
                    executer=cb_qry.from_user.id,
                    target=user_id,
                    chat_id=cb_qry.message.chat.id,
                    r_executer_chat=cb_qry.r_user_chat,
                    chat_settings=cb_qry.message.chat.settings,
                )
            elif action == "temprestrict":
                text += f"{user_id}: " + methods.Restrict(
                    client=client,
                    executer=cb_qry.from_user.id,
                    target=user_id,
                    chat_id=cb_qry.message.chat.id,
                    until_date=cb_qry.message.chat.settings.max_temp_restrict,
                    r_executer_chat=cb_qry.r_user_chat,
                    chat_settings=cb_qry.message.chat.settings,
                )
            elif action == "restrict":
                text += f"{user_id}: " + methods.Restrict(
                    client=client,
                    executer=cb_qry.from_user.id,
                    target=user_id,
                    chat_id=cb_qry.message.chat.id,
                    r_executer_chat=cb_qry.r_user_chat,
                    chat_settings=cb_qry.message.chat.settings,
                )
            elif action == "unrestrict":
                text += f"{user_id}: " + methods.Unrestrict(
                    client=client,
                    executer=cb_qry.from_user.id,
                    target=user_id,
                    chat_id=cb_qry.message.chat.id,
                    r_executer_chat=cb_qry.r_user_chat,
                    chat_settings=cb_qry.message.chat.settings,
                )
            elif action == "tempban":
                text += f"{user_id}: " + methods.Ban(
                    client=client,
                    executer=cb_qry.from_user.id,
                    target=user_id,
                    chat_id=cb_qry.message.chat.id,
                    until_date=cb_qry.message.chat.settings.max_temp_ban,
                    r_executer_chat=cb_qry.r_user_chat,
                    chat_settings=cb_qry.message.chat.settings,
                )
            elif action == "ban":
                text += f"{user_id}: " + methods.Ban(
                    client=client,
                    executer=cb_qry.from_user.id,
                    target=user_id,
                    chat_id=cb_qry.message.chat.id,
                    r_executer_chat=cb_qry.r_user_chat,
                    chat_settings=cb_qry.message.chat.settings,
                )
            elif action == "unban":
                text += f"{user_id}: " + methods.Unban(
                    client=client,
                    executer=cb_qry.from_user.id,
                    target=user_id,
                    chat_id=cb_qry.message.chat.id,
                    r_executer_chat=cb_qry.r_user_chat,
                    chat_settings=cb_qry.message.chat.settings,
                )
            elif action == "test":
                try:
                    client.send_chat_action(chat_id=user_id, action="typing")
                except Exception as ex:
                    print(ex)
                    traceback.print_exc()
                    text += f"{user_id}: {ex}"
            else:
                if utils.IsMasterOrBot(user_id=cb_qry.from_user.id):
                    if action == "gban":
                        text += f"{user_id}: " + methods.GBan(
                            client=client,
                            executer=cb_qry.from_user.id,
                            target=user_id,
                            chat_id=cb_qry.message.chat.id,
                            chat_settings=cb_qry.message.chat.settings,
                        )
                    elif action == "ungban":
                        text += f"{user_id}: " + methods.Ungban(
                            client=client,
                            executer=cb_qry.from_user.id,
                            target=user_id,
                            chat_id=cb_qry.message.chat.id,
                            chat_settings=cb_qry.message.chat.settings,
                        )
                    elif action == "block":
                        text += f"{user_id}: " + methods.Block(
                            client=client,
                            executer=cb_qry.from_user.id,
                            target=user_id,
                            chat_id=cb_qry.message.chat.id,
                            chat_settings=cb_qry.message.chat.settings,
                        )
                    elif action == "unblock":
                        text += f"{user_id}: " + methods.Unblock(
                            client=client,
                            executer=cb_qry.from_user.id,
                            target=user_id,
                            chat_id=cb_qry.message.chat.id,
                            chat_settings=cb_qry.message.chat.settings,
                        )
                else:
                    methods.CallbackQueryAnswer(
                        cb_qry=cb_qry,
                        text=_(
                            cb_qry.from_user.settings.language, "insufficient_rights"
                        ),
                        show_alert=True,
                    )
                    break
            text += "\n"

        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "success"),
            show_alert=True,
        )
        utils.Log(
            client=client,
            chat_id=cb_qry.message.chat.id,
            executer=cb_qry.from_user.id,
            action=cb_qry.data.lower(),
            target=cb_qry.message.chat.id,
        )
        cb_qry.message.edit_text(text=text)
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    my_filters.callback_regex(pattern=r"^(\w+) (\d+)", flags=re.I), group=-7,
)
def CbQryActionUser(client: pyrogram.Client, cb_qry: pyrogram.CallbackQuery):
    if utils.IsJuniorModOrHigher(
        user_id=cb_qry.from_user.id,
        chat_id=cb_qry.message.chat.id,
        r_user_chat=cb_qry.r_user_chat,
    ):
        text = ""
        action, user_id = cb_qry.data.split(" ")
        if action == "invite":
            text = f"{user_id}: " + methods.Invite(
                client=client,
                executer=cb_qry.from_user.id,
                target=user_id,
                chat_id=cb_qry.message.chat.id,
                r_executer_chat=cb_qry.r_user_chat,
                chat_settings=cb_qry.message.chat.settings,
            )
        elif action == "warn":
            text = f"{user_id}: " + methods.Warn(
                client=client,
                executer=cb_qry.from_user.id,
                target=user_id,
                chat_id=cb_qry.message.chat.id,
                r_executer_chat=cb_qry.r_user_chat,
                chat_settings=cb_qry.message.chat.settings,
            )
        elif action == "unwarn":
            text = f"{user_id}: " + methods.Unwarn(
                client=client,
                executer=cb_qry.from_user.id,
                target=user_id,
                chat_id=cb_qry.message.chat.id,
                r_executer_chat=cb_qry.r_user_chat,
                chat_settings=cb_qry.message.chat.settings,
            )
        elif action == "unwarnall":
            text = f"{user_id}: " + methods.UnwarnAll(
                client=client,
                executer=cb_qry.from_user.id,
                target=user_id,
                chat_id=cb_qry.message.chat.id,
                r_executer_chat=cb_qry.r_user_chat,
                chat_settings=cb_qry.message.chat.settings,
            )
        elif action == "kick":
            text = f"{user_id}: " + methods.Kick(
                client=client,
                executer=cb_qry.from_user.id,
                target=user_id,
                chat_id=cb_qry.message.chat.id,
                r_executer_chat=cb_qry.r_user_chat,
                chat_settings=cb_qry.message.chat.settings,
            )
        elif action == "temprestrict":
            text = f"{user_id}: " + methods.Restrict(
                client=client,
                executer=cb_qry.from_user.id,
                target=user_id,
                chat_id=cb_qry.message.chat.id,
                until_date=cb_qry.message.chat.settings.max_temp_restrict,
                r_executer_chat=cb_qry.r_user_chat,
                chat_settings=cb_qry.message.chat.settings,
            )
        elif action == "restrict":
            text = f"{user_id}: " + methods.Restrict(
                client=client,
                executer=cb_qry.from_user.id,
                target=user_id,
                chat_id=cb_qry.message.chat.id,
                r_executer_chat=cb_qry.r_user_chat,
                chat_settings=cb_qry.message.chat.settings,
            )
        elif action == "unrestrict":
            text = f"{user_id}: " + methods.Unrestrict(
                client=client,
                executer=cb_qry.from_user.id,
                target=user_id,
                chat_id=cb_qry.message.chat.id,
                r_executer_chat=cb_qry.r_user_chat,
                chat_settings=cb_qry.message.chat.settings,
            )
        elif action == "tempban":
            text = f"{user_id}: " + methods.Ban(
                client=client,
                executer=cb_qry.from_user.id,
                target=user_id,
                chat_id=cb_qry.message.chat.id,
                until_date=cb_qry.message.chat.settings.max_temp_ban,
                r_executer_chat=cb_qry.r_user_chat,
                chat_settings=cb_qry.message.chat.settings,
            )
        elif action == "ban":
            text = f"{user_id}: " + methods.Ban(
                client=client,
                executer=cb_qry.from_user.id,
                target=user_id,
                chat_id=cb_qry.message.chat.id,
                r_executer_chat=cb_qry.r_user_chat,
                chat_settings=cb_qry.message.chat.settings,
            )
        elif action == "unban":
            text = f"{user_id}: " + methods.Unban(
                client=client,
                executer=cb_qry.from_user.id,
                target=user_id,
                chat_id=cb_qry.message.chat.id,
                r_executer_chat=cb_qry.r_user_chat,
                chat_settings=cb_qry.message.chat.settings,
            )
        elif action == "test":
            try:
                client.send_chat_action(chat_id=user_id, action="typing")
            except Exception as ex:
                print(ex)
                traceback.print_exc()
                text = f"{user_id}: {ex}"
        else:
            if utils.IsMasterOrBot(user_id=cb_qry.from_user.id):
                if action == "gban":
                    text = f"{user_id}: " + methods.GBan(
                        client=client,
                        executer=cb_qry.from_user.id,
                        target=user_id,
                        chat_id=cb_qry.message.chat.id,
                        chat_settings=cb_qry.message.chat.settings,
                    )
                elif action == "ungban":
                    text = f"{user_id}: " + methods.Ungban(
                        client=client,
                        executer=cb_qry.from_user.id,
                        target=user_id,
                        chat_id=cb_qry.message.chat.id,
                        chat_settings=cb_qry.message.chat.settings,
                    )
                elif action == "block":
                    text = f"{user_id}: " + methods.Block(
                        client=client,
                        executer=cb_qry.from_user.id,
                        target=user_id,
                        chat_id=cb_qry.message.chat.id,
                        chat_settings=cb_qry.message.chat.settings,
                    )
                elif action == "unblock":
                    text = f"{user_id}: " + methods.Unblock(
                        client=client,
                        executer=cb_qry.from_user.id,
                        target=user_id,
                        chat_id=cb_qry.message.chat.id,
                        chat_settings=cb_qry.message.chat.settings,
                    )
            else:
                methods.CallbackQueryAnswer(
                    cb_qry=cb_qry,
                    text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
                    show_alert=True,
                )
                return
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry, text=text, show_alert=True,
        )
        utils.Log(
            client=client,
            chat_id=cb_qry.message.chat.id,
            executer=cb_qry.from_user.id,
            action=cb_qry.data.lower(),
            target=cb_qry.message.chat.id,
        )

        new_chat_members = [
            x[1].callback_data.split(" ")[1]
            for x in cb_qry.message.reply_markup.inline_keyboard[1:]
            if x[1].callback_data.split(" ")[1] != user_id
        ]
        cb_qry.message.edit_text(
            text=f"{cb_qry.message.text}\n{text}",
            reply_markup=pyrogram.InlineKeyboardMarkup(
                keyboards.BuildActionOnAddedUsersList(
                    chat_settings=cb_qry.message.chat.settings,
                    action=action,
                    new_chat_members=db_management.Users.select().where(
                        db_management.Users.id.in_(new_chat_members)
                    ),
                )
            )
            if len(new_chat_members) > 0
            else None,
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "insufficient_rights"),
            show_alert=True,
        )
