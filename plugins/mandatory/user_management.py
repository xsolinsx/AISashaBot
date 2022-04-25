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
from pykeyboard import InlineKeyboard
from pyrogram import errors as pyrogram_errors

_ = utils.GetLocalizedString


@pyrogram.Client.on_message(pyrogram.filters.group, group=-4)
@pyrogram.Client.on_edited_message(pyrogram.filters.group, group=-4)
def SendTagAlerts(client: pyrogram.Client, msg: pyrogram.types.Message):
    if msg.chat.settings.has_tag_alerts:
        query: peewee.ModelSelect = None
        if msg.chat.settings.has_tag_alerts == 1:
            # users in group
            query = (
                db_management.UserSettings.select()
                .join(
                    db_management.RUserChat,
                    on=(
                        db_management.UserSettings.user_id
                        == db_management.RUserChat.user_id
                    ),
                )
                .where(
                    (db_management.UserSettings.wants_tag_alerts > 0)
                    & (db_management.RUserChat.chat_id == msg.chat.id)
                )
            )
        else:
            # all users
            query = db_management.UserSettings.select().where(
                db_management.UserSettings.wants_tag_alerts > 0
            )
        text_to_use = ""
        if msg.text:
            text_to_use += f" {msg.text}"
        if msg.caption:
            text_to_use += f" {msg.caption}"
        text_to_use = text_to_use.strip()
        if text_to_use:
            for user in query:
                if user.user_id != msg.from_user.id:
                    username = user.user.username
                    regex1 = re.compile(
                        pattern=f"\\b([@]?{username})\\b",
                        flags=re.I,
                    )
                    match = regex1.match(text_to_use)
                    if not match and user.nickname:
                        # test all nicknames of the user
                        for nickname in user.nickname.split("|"):
                            regex2 = re.compile(
                                pattern=f"\\b({nickname})\\b",
                                flags=re.I | re.M,
                            )
                            if match or regex2.match(text_to_use):
                                match = True
                                break
                    if match:
                        try:
                            member = client.get_chat_member(
                                chat_id=msg.chat.id, user_id=user.user_id
                            )
                        except pyrogram_errors.FloodWait as ex:
                            print(ex)
                            traceback.print_exc()
                        except pyrogram_errors.RPCError as ex:
                            print(ex)
                            traceback.print_exc()
                        else:
                            is_member = (
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
                            )

                            if (
                                not is_member
                                and user.wants_tag_alerts == 2
                                and msg.chat.settings.has_tag_alerts == 2
                            ) or (is_member and user.wants_tag_alerts):
                                # send tagalert iff (user is member AND wants tagalerts) OR (user is NOT member AND group allows tagalerts to all AND user wants all tags)
                                if msg.media:
                                    media, type_ = utils.ExtractMedia(msg=msg)
                                    if media:
                                        client.send_cached_media(
                                            chat_id=user.user_id,
                                            file_id=media.file_id,
                                            caption=_(
                                                user.language, "tag_message"
                                            ).format(
                                                utils.PrintChat(msg.chat),
                                                utils.PrintUser(msg.from_user),
                                                text_to_use
                                                if len(text_to_use)
                                                <= utils.config["max_length_tag_text"]
                                                else text_to_use[
                                                    : utils.config[
                                                        "max_length_tag_text"
                                                    ]
                                                ]
                                                + "...",
                                                user.user_id,
                                            ),
                                            reply_markup=keyboards.BuildTagKeyboard(
                                                chat=msg.chat,
                                                message_id=msg.id,
                                                chat_settings=msg.chat.settings,
                                                is_member=is_member,
                                            ),
                                        )
                                else:
                                    methods.SendMessage(
                                        client=client,
                                        chat_id=user.user_id,
                                        text=_(user.language, "tag_message").format(
                                            utils.PrintChat(msg.chat),
                                            utils.PrintUser(msg.from_user),
                                            text_to_use
                                            if len(text_to_use)
                                            <= utils.config["max_length_tag_text"]
                                            else text_to_use[
                                                : utils.config["max_length_tag_text"]
                                            ]
                                            + "...",
                                            user.user_id,
                                        ),
                                        reply_markup=keyboards.BuildTagKeyboard(
                                            chat=msg.chat,
                                            message_id=msg.id,
                                            chat_settings=msg.chat.settings,
                                            is_member=is_member,
                                        ),
                                    )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^\(i\)mysettings", flags=re.I)
    & my_filters.callback_private
)
def CbQryMySettingsInfo(client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery):
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry,
        text=_(cb_qry.from_user.settings.language, cb_qry.data),
        show_alert=True,
    )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^mysettings language", flags=re.I)
    & my_filters.callback_private
)
def CbQryMySettingsLanguageChange(
    client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery
):
    i = (
        utils.config["available_languages"].index(cb_qry.from_user.settings.language)
        + 1
    )
    if i >= len(utils.config["available_languages"]):
        i = 0

    cb_qry.from_user.settings.language = utils.config["available_languages"][i]
    cb_qry.from_user.settings.save()
    utils.Log(
        client=client,
        chat_id=cb_qry.from_user.id,
        executer=cb_qry.from_user.id,
        action=f"{cb_qry.data} = {cb_qry.from_user.settings.language}",
        target=cb_qry.from_user.id,
    )
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry,
        text=_(cb_qry.from_user.settings.language, "selected_language").format(
            dictionaries.LANGUAGE_EMOJI.get(
                cb_qry.from_user.settings.language, pyrogram.emoji.PIRATE_FLAG
            )
        ),
        show_alert=False,
    )
    cb_qry.message.edit_reply_markup(
        reply_markup=keyboards.BuildPrivateSettingsMenu(
            user_settings=cb_qry.from_user.settings
        ),
    )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^mysettings wants_tag_alerts", flags=re.I)
    & my_filters.callback_private
)
def CbQryMySettingsWantsTagAlertsChange(
    client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery
):
    cb_qry.from_user.settings.wants_tag_alerts += 1
    if cb_qry.from_user.settings.wants_tag_alerts > 2:
        cb_qry.from_user.settings.wants_tag_alerts = 0
    cb_qry.from_user.settings.save()
    utils.Log(
        client=client,
        chat_id=cb_qry.from_user.id,
        executer=cb_qry.from_user.id,
        action=f"{cb_qry.data} = {cb_qry.from_user.settings.wants_tag_alerts}",
        target=cb_qry.from_user.id,
    )
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry,
        text=_(
            cb_qry.from_user.settings.language,
            "wants_tag_alert_public"
            if cb_qry.from_user.settings.wants_tag_alerts == 2
            else (
                "wants_tag_alert_in_group"
                if cb_qry.from_user.settings.wants_tag_alerts == 1
                else "wants_tag_alert_off"
            ),
        ),
        show_alert=True,
    )
    cb_qry.message.edit_reply_markup(
        reply_markup=keyboards.BuildPrivateSettingsMenu(
            user_settings=cb_qry.from_user.settings
        ),
    )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^mysettings set_nickname", flags=re.I)
    & my_filters.callback_private
)
def CbQryMySettingsSetNickname(
    client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery
):
    utils.tmp_steps[cb_qry.message.chat.id] = (cb_qry, cb_qry.data)
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry,
        text=_(cb_qry.from_user.settings.language, "send_nickname"),
        show_alert=False,
    )

    py_k = InlineKeyboard()
    py_k.row(
        pyrogram.types.InlineKeyboardButton(
            text=_(cb_qry.from_user.settings.language, "cancel"),
            callback_data="cancel mysettings",
        )
    )
    cb_qry.message.edit_text(
        text=_(cb_qry.from_user.settings.language, "nickname_help").format(
            utils.config["max_nicknames"]
        ),
        reply_markup=py_k,
        parse_mode=pyrogram.enums.parse_mode.ParseMode.HTML,
    )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^mysettings get_nickname", flags=re.I)
    & my_filters.callback_private
)
def CbQryMySettingsGetNickname(
    client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery
):
    if cb_qry.from_user.settings.nickname:
        methods.ReplyText(
            client=client, msg=cb_qry.message, text=cb_qry.from_user.settings.nickname
        )
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "ok"),
            show_alert=False,
        )
    else:
        methods.CallbackQueryAnswer(
            cb_qry=cb_qry,
            text=_(cb_qry.from_user.settings.language, "no_nickname_set"),
            show_alert=True,
        )


@pyrogram.Client.on_callback_query(
    pyrogram.filters.regex(pattern=r"^mysettings unset_nickname", flags=re.I)
    & my_filters.callback_private
)
def CbQryMySettingsUnsetNickname(
    client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery
):
    cb_qry.from_user.settings.nickname = None
    cb_qry.from_user.settings.save()
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry,
        text=_(cb_qry.from_user.settings.language, "success"),
        show_alert=False,
    )

    cb_qry.message.edit_reply_markup(
        reply_markup=keyboards.BuildPrivateSettingsMenu(
            user_settings=cb_qry.from_user.settings
        )
    )


@pyrogram.Client.on_callback_query(
    my_filters.callback_command(commands=["mysettings"]) & my_filters.callback_private
)
def CbQryMySettings(client: pyrogram.Client, cb_qry: pyrogram.types.CallbackQuery):
    methods.CallbackQueryAnswer(
        cb_qry=cb_qry,
        text=_(cb_qry.from_user.settings.language, "updating"),
        show_alert=False,
    )
    cb_qry.message.edit_text(
        text=_(cb_qry.from_user.settings.language, "mysettings"),
        reply_markup=keyboards.BuildPrivateSettingsMenu(
            user_settings=cb_qry.from_user.settings
        ),
    )


@pyrogram.Client.on_message(
    pyrogram.filters.command(
        commands=["mysettings"],
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
@pyrogram.Client.on_edited_message(
    pyrogram.filters.command(
        commands=["mysettings"],
        prefixes=["/", "!", "#", "."],
    )
    & pyrogram.filters.private
)
def CmdMySettings(client: pyrogram.Client, msg: pyrogram.types.Message):
    methods.ReplyText(
        client=client,
        msg=msg,
        text=_(msg.from_user.settings.language, "mysettings"),
        reply_markup=keyboards.BuildPrivateSettingsMenu(
            user_settings=msg.from_user.settings
        ),
    )
