import datetime
import math
import typing

import peewee
import pyrogram

import db_management
import dictionaries
import utils

_ = utils.GetLocalizedString


def BuildKeyboard(
    main_buttons: list = None, header_buttons: list = None, footer_buttons: list = None
) -> list:
    """
    Build a list that can be used for an inline keyboard.

    main_buttons (``list``): Main list of buttons.

    header_buttons (``list``, *optional*, default = None): Buttons to place on the top of the keyboard.

    footer_buttons (``list``, *optional*, default = None): Buttons to place on the bottom of the keyboard.


    SUCCESS Returns ``list`` of buttons.
    """
    menu = list()
    if header_buttons:
        menu.extend(header_buttons)
    if main_buttons:
        menu.extend(main_buttons)
    if footer_buttons:
        menu.extend(footer_buttons)

    return menu


def AdjustPage(page: int, max_n: int, max_items_page: int):
    if page < 0:
        page = math.ceil(max_n / max_items_page) + page

    # fallback
    if page < 0:
        page = 0
    return page


def BuildPager(
    base_callback_data: str, page: int, n_items: int, max_items_keyboard: int
) -> list:
    """
    Use this method to create the pager on the bottom of the keyboards.

    base_callback_data (``str``): Starting callback_data that is dependent on where you call this function.

    page (``int``): Current page you are on.

    n_items (``int``): Number of items to put in the keyboard.

    max_items_keyboard (``int``): Maximum number of items to put in the keyboard per page.


    SUCCESS Returns ``list`` of buttons to append to a keyboard that needs it.
    """
    page = int(page)
    n_items = int(n_items)
    max_items_keyboard = int(max_items_keyboard)
    pager = list()
    if n_items > max_items_keyboard:
        page_shift_row = list()
        if page - 2 >= 0:
            # goto first
            page_shift_row.append(
                pyrogram.types.InlineKeyboardButton(
                    pyrogram.emoji.LAST_TRACK_BUTTON,
                    callback_data=f"{base_callback_data} PAGES<<",
                )
            )
        if page - 1 >= 0:
            # previous page
            page_shift_row.append(
                pyrogram.types.InlineKeyboardButton(
                    pyrogram.emoji.REVERSE_BUTTON,
                    callback_data=f"{base_callback_data} PAGES-",
                )
            )
        # select page button
        page_shift_row.append(
            pyrogram.types.InlineKeyboardButton(
                f"{page + 1}/{math.ceil(n_items / max_items_keyboard)}",
                callback_data=f"useless{base_callback_data} PAGES",
            )
        )
        if page + 1 < math.ceil(n_items / max_items_keyboard):
            # next page
            page_shift_row.append(
                pyrogram.types.InlineKeyboardButton(
                    pyrogram.emoji.PLAY_BUTTON,
                    callback_data=f"{base_callback_data} PAGES+",
                )
            )
        if page + 2 < math.ceil(n_items / max_items_keyboard):
            # goto last
            page_shift_row.append(
                pyrogram.types.InlineKeyboardButton(
                    pyrogram.emoji.NEXT_TRACK_BUTTON,
                    callback_data=f"{base_callback_data} PAGES>>",
                )
            )
        pager.append(page_shift_row)
    return pager


def BuildStartMenu(
    user_settings: db_management.UserSettings, bot_username: str, channel_username: str
) -> list:
    channel_username = channel_username.replace("@", "")

    keyboard = list()
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(user_settings.language, "add_me_to_group"),
                url=f"t.me/{bot_username}?startgroup=new_group",
            )
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.INFORMATION
                + " "
                + _(user_settings.language, "about"),
                callback_data="about",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.MEGAPHONE
                + " "
                + _(user_settings.language, "channel"),
                url=f"t.me/{channel_username}",
            ),
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.WORLD_MAP
                + " "
                + _(user_settings.language, "set_your_language"),
                callback_data="mysettings",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.OPEN_BOOK
                + " "
                + _(user_settings.language, "commands"),
                callback_data="mainhelp",
            ),
        ]
    )
    return BuildKeyboard(main_buttons=keyboard)


def BuildPrivateSettingsMenu(user_settings: db_management.UserSettings) -> list:
    keyboard = list()
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(user_settings.language, "language"),
                callback_data="(i)mysettings language",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=dictionaries.LANGUAGE_EMOJI.get(
                    user_settings.language, pyrogram.emoji.PIRATE_FLAG
                ),
                callback_data="mysettings language",
            ),
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(user_settings.language, "wants_tag_alerts"),
                callback_data="(i)mysettings wants_tag_alerts",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(
                    user_settings.language,
                    "yes"
                    if user_settings.wants_tag_alerts == 2
                    else ("my_groups" if user_settings.wants_tag_alerts == 1 else "no"),
                ),
                callback_data="mysettings wants_tag_alerts",
            ),
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(user_settings.language, "nickname"),
                callback_data="(i)mysettings nickname",
            ),
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.MEMO
                + (
                    _(user_settings.language, "replace")
                    if user_settings.nickname
                    else _(user_settings.language, "set")
                ),
                callback_data="mysettings set_nickname",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.EYE + _(user_settings.language, "get"),
                callback_data="mysettings get_nickname",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.CROSS_MARK + _(user_settings.language, "unset"),
                callback_data="mysettings unset_nickname",
            ),
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(user_settings.language, "back_to_main_menu"),
                callback_data="start",
            )
        ]
    )
    return BuildKeyboard(main_buttons=keyboard)


def BuildTelegramSettingsMenu(chat_settings: db_management.ChatSettings) -> list:
    keyboard = list()
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "can_send_messages"),
                callback_data="settings can_send_messages",
            )
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "can_send_media_messages "),
                callback_data="settings can_send_media_messages",
            )
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "can_send_other_messages "),
                callback_data="settings can_send_other_messages",
            )
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "can_add_web_page_previews "),
                callback_data="settings can_add_web_page_previews",
            )
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "can_send_polls"),
                callback_data="settings can_send_polls",
            )
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "can_change_info"),
                callback_data="settings can_change_info",
            )
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "can_invite_users"),
                callback_data="settings can_invite_users",
            )
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "can_pin_messages"),
                callback_data="settings can_pin_messages",
            )
        ]
    )

    return keyboard


def BuildGroupSettingsMenu(
    chat_settings: db_management.ChatSettings,
    current_keyboard: typing.Union[str, bytes],
    selected_setting: str = None,
) -> list:
    current_keyboard = current_keyboard.replace("useless", "")

    header_buttons = list()
    header_buttons.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, current_keyboard).upper(),
                callback_data=f"useless{current_keyboard} {chat_settings.chat_id}",
            )
        ]
    )

    keyboard = list()
    if current_keyboard == "mainsettings":
        # keyboard.append([pyrogram.types.InlineKeyboardButton(text=_(chat_settings.language, "telegramsettings"),
        #                                               callback_data="telegramsettings")])
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "generalsettings"),
                    callback_data="generalsettings",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "floodsettings"),
                    callback_data="floodsettings",
                ),
            ]
        )
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "invitesettings"),
                    callback_data="invitesettings",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "greetingsettings"),
                    callback_data="greetingsettings",
                ),
            ]
        )
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "actionsettings"),
                    callback_data="actionsettings",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "messagesettings"),
                    callback_data="messagesettings",
                ),
            ]
        )
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "censorships"),
                    callback_data=f"censorships {chat_settings.chat_id} 0",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "alternatives"),
                    callback_data=f"alternatives {chat_settings.chat_id} 0",
                ),
            ]
        )
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "nightmodesettings"),
                    callback_data="nightmodesettings",
                )
            ]
        )
        # keyboard.append([pyrogram.types.InlineKeyboardButton(text=_(chat_settings.language, "nightmodesettings"),
        #                                                callback_data="nightmodesettings"),
        #                  pyrogram.types.InlineKeyboardButton(text=_(chat_settings.language, "slowmodesettings"),
        #                                                callback_data="slowmodesettings")])
        if chat_settings.allow_temporary_punishments:
            keyboard.append(
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=_(chat_settings.language, "temporarypunishmentssettings"),
                        callback_data="temporarypunishmentssettings",
                    )
                ]
            )
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "whitelist").upper(),
                    callback_data="(i)settings whitelist",
                ),
            ]
        )
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "users"),
                    callback_data=f"whitelisted {chat_settings.chat_id} 0",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "gbanned"),
                    callback_data=f"whitelistedgbanned {chat_settings.chat_id} 0",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "chats"),
                    callback_data=f"whitelistedchats {chat_settings.chat_id} 0",
                ),
            ]
        )
    elif current_keyboard == "telegramsettings":
        keyboard = BuildTelegramSettingsMenu(chat_settings=chat_settings)
    elif current_keyboard == "generalsettings":
        keyboard = BuildGeneralSettingsMenu(
            chat_settings=chat_settings, selected_setting=selected_setting
        )
    elif current_keyboard == "floodsettings":
        keyboard = BuildFloodSettingsMenu(
            chat_settings=chat_settings, selected_setting=selected_setting
        )
    elif current_keyboard == "invitesettings":
        keyboard = BuildInviteSettingsMenu(
            chat_settings=chat_settings, selected_setting=selected_setting
        )
    elif current_keyboard == "greetingsettings":
        keyboard = BuildGreetingSettingsMenu(chat_settings=chat_settings)
    elif current_keyboard == "actionsettings":
        keyboard = BuildActionTypeSettingsMenu(
            chat_settings=chat_settings, selected_setting=selected_setting
        )
    elif current_keyboard == "messagesettings":
        keyboard = BuildMessageTypeSettingsMenu(
            chat_settings=chat_settings, selected_setting=selected_setting
        )
    elif current_keyboard == "nightmodesettings":
        keyboard = BuildNightModeSettingsMenu(
            chat_settings=chat_settings, selected_setting=selected_setting
        )
    elif current_keyboard == "slowmodesettings":
        keyboard = BuildSlowModeSettingsMenu(
            chat_settings=chat_settings, selected_setting=selected_setting
        )
    elif current_keyboard == "temporarypunishmentssettings":
        keyboard = BuildTempPunishmentMenu(chat_settings=chat_settings)
    elif current_keyboard == "max_temp_restrict" or current_keyboard == "max_temp_ban":
        keyboard = BuildTempPunishmentMenu(
            chat_settings=chat_settings,
            max_temp_punishment_time=int(getattr(chat_settings, current_keyboard)),
            current_keyboard=f"settings {current_keyboard}",
        )

    footer_buttons = list()
    if current_keyboard == "mainsettings":
        footer_buttons.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "chat")
                    + f" {pyrogram.emoji.INFORMATION}",
                    callback_data=f"maininfo {chat_settings.chat_id}",
                )
            ]
        )
    else:
        footer_buttons.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "back_to_settings_menu").format(
                        pyrogram.emoji.GEAR
                    ),
                    callback_data="mainsettings",
                )
            ]
        )

    return BuildKeyboard(
        main_buttons=keyboard,
        header_buttons=header_buttons,
        footer_buttons=footer_buttons,
    )


def BuildGeneralSettingsMenu(
    chat_settings: db_management.ChatSettings, selected_setting: str = None
) -> list:
    if selected_setting:
        punishments_rows = [
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[0]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[0])}",
                    callback_data=f"settings {selected_setting} selectvalue0",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[1]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[1])}",
                    callback_data=f"settings {selected_setting} selectvalue1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[2]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[2])}",
                    callback_data=f"settings {selected_setting} selectvalue2",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[3]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[3])}",
                    callback_data=f"settings {selected_setting} selectvalue3",
                ),
            ],
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[4]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[4])}",
                    callback_data=f"settings {selected_setting} selectvalue4",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[5]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[5])}",
                    callback_data=f"settings {selected_setting} selectvalue5",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[6]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[6])}",
                    callback_data=f"settings {selected_setting} selectvalue6",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[7]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[7])}",
                    callback_data=f"settings {selected_setting} selectvalue7",
                ),
            ],
        ]
        if not chat_settings.allow_temporary_punishments:
            # remove temporary punishments from the rows
            tmp = punishments_rows[0].pop(3)
            punishments_rows[1][0] = tmp
            punishments_rows[1].pop(2)

    keyboard = list()
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "are_locked"),
                callback_data="(i)settings are_locked",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{pyrogram.emoji.LOCKED} " + _(chat_settings.language, "locked")
                if chat_settings.are_locked
                else f"{pyrogram.emoji.UNLOCKED} "
                + _(chat_settings.language, "unlocked"),
                callback_data="settings are_locked",
            ),
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "language"),
                callback_data="(i)settings language",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=dictionaries.LANGUAGE_EMOJI.get(
                    chat_settings.language, pyrogram.emoji.PIRATE_FLAG
                ),
                callback_data="settings language",
            ),
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "is_bot_on"),
                callback_data="(i)settings is_bot_on",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=dictionaries.YES_NO_EMOJI[chat_settings.is_bot_on],
                callback_data="settings is_bot_on",
            ),
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "has_pin_markers"),
                callback_data="(i)settings has_pin_markers",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=dictionaries.YES_NO_EMOJI[chat_settings.has_pin_markers],
                callback_data="settings has_pin_markers",
            ),
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "allow_temporary_punishments"),
                callback_data="(i)settings allow_temporary_punishments",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=dictionaries.YES_NO_EMOJI[
                    chat_settings.allow_temporary_punishments
                ],
                callback_data="settings allow_temporary_punishments",
            ),
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "has_tag_alerts"),
                callback_data="(i)settings has_tag_alerts",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(
                    chat_settings.language,
                    "yes"
                    if chat_settings.has_tag_alerts == 2
                    else (
                        "users_in_group" if chat_settings.has_tag_alerts == 1 else "no"
                    ),
                ),
                callback_data="settings has_tag_alerts",
            ),
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "group_notices"),
                callback_data="(i)settings group_notices",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.group_notices])}^"
                if chat_settings.group_notices
                else dictionaries.YES_NO_EMOJI[chat_settings.group_notices],
                callback_data="settings group_notices",
            ),
        ]
    )
    if selected_setting == "group_notices":
        row1 = [punishments_rows[0][0]]
        row1.extend(punishments_rows[0][2:])
        row2 = punishments_rows[1]
        keyboard.extend([row1, row2])

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "decrement"),
                callback_data="settings max_warns--",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "max_warns").format(
                    chat_settings.max_warns
                ),
                callback_data="(i)settings max_warns",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "increment"),
                callback_data="settings max_warns++",
            ),
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "max_warns_punishment"),
                callback_data="(i)settings max_warns_punishment",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.max_warns_punishment]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.max_warns_punishment])}",
                callback_data="settings max_warns_punishment",
            ),
        ]
    )
    if selected_setting == "max_warns_punishment":
        keyboard.extend(punishments_rows)
    return keyboard


def BuildFloodSettingsMenu(
    chat_settings: db_management.ChatSettings, selected_setting: str = None
) -> list:
    if selected_setting:
        punishments_rows = [
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[0]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[0])}",
                    callback_data=f"settings {selected_setting} selectvalue0",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[1]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[1])}",
                    callback_data=f"settings {selected_setting} selectvalue1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[2]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[2])}",
                    callback_data=f"settings {selected_setting} selectvalue2",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[3]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[3])}",
                    callback_data=f"settings {selected_setting} selectvalue3",
                ),
            ],
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[4]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[4])}",
                    callback_data=f"settings {selected_setting} selectvalue4",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[5]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[5])}",
                    callback_data=f"settings {selected_setting} selectvalue5",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[6]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[6])}",
                    callback_data=f"settings {selected_setting} selectvalue6",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[7]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[7])}",
                    callback_data=f"settings {selected_setting} selectvalue7",
                ),
            ],
        ]
        if not chat_settings.allow_temporary_punishments:
            # remove temporary punishments from the rows
            tmp = punishments_rows[0].pop(3)
            punishments_rows[1][0] = tmp
            punishments_rows[1].pop(2)

    keyboard = list()
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "flood_punishment"),
                callback_data="(i)settings flood_punishment",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.flood_punishment]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.flood_punishment])}",
                callback_data="settings flood_punishment",
            ),
        ]
    )
    if selected_setting == "flood_punishment":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "decrement"),
                callback_data="settings max_flood--",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "max_flood").format(
                    chat_settings.max_flood
                ),
                callback_data="(i)settings max_flood",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "increment"),
                callback_data="settings max_flood++",
            ),
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "decrement"),
                callback_data="settings max_flood_time--",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "max_flood_time").format(
                    chat_settings.max_flood_time
                ),
                callback_data="(i)settings max_flood_time",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "increment"),
                callback_data="settings max_flood_time++",
            ),
        ]
    )

    return keyboard


def BuildInviteSettingsMenu(
    chat_settings: db_management.ChatSettings, selected_setting: str = None
) -> list:
    if selected_setting:
        punishments_rows = [
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[0]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[0])}",
                    callback_data=f"settings {selected_setting} selectvalue0",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[1]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[1])}",
                    callback_data=f"settings {selected_setting} selectvalue1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[2]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[2])}",
                    callback_data=f"settings {selected_setting} selectvalue2",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[3]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[3])}",
                    callback_data=f"settings {selected_setting} selectvalue3",
                ),
            ],
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[4]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[4])}",
                    callback_data=f"settings {selected_setting} selectvalue4",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[5]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[5])}",
                    callback_data=f"settings {selected_setting} selectvalue5",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[6]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[6])}",
                    callback_data=f"settings {selected_setting} selectvalue6",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[7]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[7])}",
                    callback_data=f"settings {selected_setting} selectvalue7",
                ),
            ],
        ]
        if not chat_settings.allow_temporary_punishments:
            # remove temporary punishments from the rows
            tmp = punishments_rows[0].pop(3)
            punishments_rows[1][0] = tmp
            punishments_rows[1].pop(2)

    keyboard = list()
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "decrement"),
                callback_data="settings max_invites--",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "max_invites").format(
                    chat_settings.max_invites
                ),
                callback_data="(i)settings max_invites",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "increment"),
                callback_data="settings max_invites++",
            ),
        ]
    )

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "add_punishment"),
                callback_data="(i)settings add_punishment",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.add_punishment]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.add_punishment])}",
                callback_data="settings add_punishment",
            ),
        ]
    )
    if selected_setting == "add_punishment":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "join_punishment"),
                callback_data="(i)settings join_punishment",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.join_punishment]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.join_punishment])}",
                callback_data="settings join_punishment",
            ),
        ]
    )
    if selected_setting == "join_punishment":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "is_link_public"),
                callback_data="(i)settings is_link_public",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(
                    chat_settings.language,
                    "yes"
                    if chat_settings.is_link_public == 2
                    else (
                        "users_in_group" if chat_settings.is_link_public == 1 else "no"
                    ),
                ),
                callback_data="settings is_link_public",
            ),
        ]
    )

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "link"), callback_data="(i)settings link"
            ),
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.NEW_BUTTON + _(chat_settings.language, "generate"),
                callback_data="settings generate_link",
            ),
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.MEMO + _(chat_settings.language, "set"),
                callback_data="settings set_link",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.EYE + _(chat_settings.language, "get"),
                callback_data="settings get_link",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.CROSS_MARK + _(chat_settings.language, "unset"),
                callback_data="settings unset_link",
            ),
        ]
    )

    return keyboard


def BuildGreetingSettingsMenu(chat_settings: db_management.ChatSettings) -> list:
    keyboard = list()
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "welcome").upper(),
                callback_data="(i)settings welcome",
            )
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "decrement"),
                callback_data="settings welcome_members--",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "welcome_members").format(
                    chat_settings.welcome_members
                ),
                callback_data="(i)settings welcome_members",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "increment"),
                callback_data="settings welcome_members++",
            ),
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.MEMO + _(chat_settings.language, "set"),
                callback_data="settings set_welcome",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.EYE + _(chat_settings.language, "get"),
                callback_data="settings get_welcome",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.CROSS_MARK + _(chat_settings.language, "unset"),
                callback_data="settings unset_welcome",
            ),
        ]
    )

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.INPUT_LATIN_UPPERCASE
                + _(chat_settings.language, "welcome_buttons")
                + pyrogram.emoji.INPUT_LATIN_UPPERCASE,
                callback_data="(i)settings welcome_buttons",
            )
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.MEMO + _(chat_settings.language, "set"),
                callback_data="settings set_welcome_buttons",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.EYE + _(chat_settings.language, "get"),
                callback_data="settings get_welcome_buttons",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.CROSS_MARK + _(chat_settings.language, "unset"),
                callback_data="settings unset_welcome_buttons",
            ),
        ]
    )

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "goodbye").upper(),
                callback_data="(i)settings goodbye",
            )
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.MEMO + _(chat_settings.language, "set"),
                callback_data="settings set_goodbye",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.EYE + _(chat_settings.language, "get"),
                callback_data="settings get_goodbye",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.CROSS_MARK + _(chat_settings.language, "unset"),
                callback_data="settings unset_goodbye",
            ),
        ]
    )

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "rules").upper(),
                callback_data="(i)settings rules",
            )
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.MEMO + _(chat_settings.language, "set"),
                callback_data="settings set_rules",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.EYE + _(chat_settings.language, "get"),
                callback_data="settings get_rules",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=pyrogram.emoji.CROSS_MARK + _(chat_settings.language, "unset"),
                callback_data="settings unset_rules",
            ),
        ]
    )
    return keyboard


def BuildActionTypeSettingsMenu(
    chat_settings: db_management.ChatSettings, selected_setting: str = None
) -> list:
    if selected_setting:
        punishments_rows = [
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[0]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[0])}",
                    callback_data=f"settings {selected_setting} selectvalue0",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[1]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[1])}",
                    callback_data=f"settings {selected_setting} selectvalue1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[2]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[2])}",
                    callback_data=f"settings {selected_setting} selectvalue2",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[3]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[3])}",
                    callback_data=f"settings {selected_setting} selectvalue3",
                ),
            ],
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[4]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[4])}",
                    callback_data=f"settings {selected_setting} selectvalue4",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[5]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[5])}",
                    callback_data=f"settings {selected_setting} selectvalue5",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[6]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[6])}",
                    callback_data=f"settings {selected_setting} selectvalue6",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[7]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[7])}",
                    callback_data=f"settings {selected_setting} selectvalue7",
                ),
            ],
        ]
        if not chat_settings.allow_temporary_punishments:
            # remove temporary punishments from the rows
            tmp = punishments_rows[0].pop(3)
            punishments_rows[1][0] = tmp
            punishments_rows[1].pop(2)

    keyboard = list()
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "arabic_punishment"),
                callback_data="(i)settings arabic_punishment",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.arabic_punishment]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.arabic_punishment])}",
                callback_data="settings arabic_punishment",
            ),
        ]
    )
    if selected_setting == "arabic_punishment":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "bot_punishment"),
                callback_data="(i)settings bot_punishment",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.bot_punishment]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.bot_punishment])}",
                callback_data="settings bot_punishment",
            ),
        ]
    )
    if selected_setting == "bot_punishment":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "forward_punishment"),
                callback_data="(i)settings forward_punishment",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.forward_punishment]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.forward_punishment])}",
                callback_data="settings forward_punishment",
            ),
        ]
    )
    if selected_setting == "forward_punishment":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "globally_banned_punishment"),
                callback_data="(i)settings globally_banned_punishment",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.globally_banned_punishment]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.globally_banned_punishment])}",
                callback_data="settings globally_banned_punishment",
            ),
        ]
    )
    if selected_setting == "globally_banned_punishment":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "link_spam_punishment"),
                callback_data="(i)settings link_spam_punishment",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.link_spam_punishment]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.link_spam_punishment])}",
                callback_data="settings link_spam_punishment",
            ),
        ]
    )
    if selected_setting == "link_spam_punishment":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "rtl_punishment"),
                callback_data="(i)settings rtl_punishment",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.rtl_punishment]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.rtl_punishment])}",
                callback_data="settings rtl_punishment",
            ),
        ]
    )
    if selected_setting == "rtl_punishment":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "shitstorm_punishment"),
                callback_data="(i)settings shitstorm_punishment",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.shitstorm_punishment]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.shitstorm_punishment])}",
                callback_data="settings shitstorm_punishment",
            ),
        ]
    )
    if selected_setting == "shitstorm_punishment":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "text_spam_punishment"),
                callback_data="(i)settings text_spam_punishment",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.text_spam_punishment]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.text_spam_punishment])}",
                callback_data="settings text_spam_punishment",
            ),
        ]
    )
    if selected_setting == "text_spam_punishment":
        keyboard.extend(punishments_rows)

    return keyboard


def BuildMessageTypeSettingsMenu(
    chat_settings: db_management.ChatSettings, selected_setting: str = None
) -> list:
    if selected_setting:
        punishments_rows = [
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[0]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[0])}",
                    callback_data=f"settings {selected_setting} selectvalue0",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[1]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[1])}",
                    callback_data=f"settings {selected_setting} selectvalue1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[2]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[2])}",
                    callback_data=f"settings {selected_setting} selectvalue2",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[3]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[3])}",
                    callback_data=f"settings {selected_setting} selectvalue3",
                ),
            ],
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[4]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[4])}",
                    callback_data=f"settings {selected_setting} selectvalue4",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[5]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[5])}",
                    callback_data=f"settings {selected_setting} selectvalue5",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[6]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[6])}",
                    callback_data=f"settings {selected_setting} selectvalue6",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[7]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[7])}",
                    callback_data=f"settings {selected_setting} selectvalue7",
                ),
            ],
        ]
        if not chat_settings.allow_temporary_punishments:
            # remove temporary punishments from the rows
            tmp = punishments_rows[0].pop(3)
            punishments_rows[1][0] = tmp
            punishments_rows[1].pop(2)

    keyboard = list()
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "anti_everything"),
                callback_data="(i)settings anti_everything",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.anti_everything]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.anti_everything])}",
                callback_data="settings anti_everything",
            ),
        ]
    )
    if selected_setting == "anti_everything":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "anti_animation"),
                callback_data="(i)settings anti_animation",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.anti_animation]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.anti_animation])}",
                callback_data="settings anti_animation",
            ),
        ]
    )
    if selected_setting == "anti_animation":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "anti_audio"),
                callback_data="(i)settings anti_audio",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.anti_audio]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.anti_audio])}",
                callback_data="settings anti_audio",
            ),
        ]
    )
    if selected_setting == "anti_audio":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "anti_contact"),
                callback_data="(i)settings anti_contact",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.anti_contact]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.anti_contact])}",
                callback_data="settings anti_contact",
            ),
        ]
    )
    if selected_setting == "anti_contact":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "anti_document"),
                callback_data="(i)settings anti_document",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.anti_document]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.anti_document])}",
                callback_data="settings anti_document",
            ),
        ]
    )
    if selected_setting == "anti_document":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "anti_game"),
                callback_data="(i)settings anti_game",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.anti_game]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.anti_game])}",
                callback_data="settings anti_game",
            ),
        ]
    )
    if selected_setting == "anti_game":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "anti_location"),
                callback_data="(i)settings anti_location",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.anti_location]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.anti_location])}",
                callback_data="settings anti_location",
            ),
        ]
    )
    if selected_setting == "anti_location":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "anti_photo"),
                callback_data="(i)settings anti_photo",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.anti_photo]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.anti_photo])}",
                callback_data="settings anti_photo",
            ),
        ]
    )
    if selected_setting == "anti_photo":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "anti_sticker"),
                callback_data="(i)settings anti_sticker",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.anti_sticker]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.anti_sticker])}",
                callback_data="settings anti_sticker",
            ),
        ]
    )
    if selected_setting == "anti_sticker":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "anti_text"),
                callback_data="(i)settings anti_text",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.anti_text]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.anti_text])}",
                callback_data="settings anti_text",
            ),
        ]
    )
    if selected_setting == "anti_text":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "anti_venue"),
                callback_data="(i)settings anti_venue",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.anti_venue]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.anti_venue])}",
                callback_data="settings anti_venue",
            ),
        ]
    )
    if selected_setting == "anti_venue":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "anti_video"),
                callback_data="(i)settings anti_video",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.anti_video]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.anti_video])}",
                callback_data="settings anti_video",
            ),
        ]
    )
    if selected_setting == "anti_video":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "anti_video_note"),
                callback_data="(i)settings anti_video_note",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.anti_video_note]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.anti_video_note])}",
                callback_data="settings anti_video_note",
            ),
        ]
    )
    if selected_setting == "anti_video_note":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "anti_voice"),
                callback_data="(i)settings anti_voice",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.anti_voice]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.anti_voice])}",
                callback_data="settings anti_voice",
            ),
        ]
    )
    if selected_setting == "anti_voice":
        keyboard.extend(punishments_rows)

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "allow_media_group"),
                callback_data="(i)settings allow_media_group",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=dictionaries.YES_NO_EMOJI[chat_settings.allow_media_group],
                callback_data="settings allow_media_group",
            ),
        ]
    )

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "allow_service_messages"),
                callback_data="(i)settings allow_service_messages",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=dictionaries.YES_NO_EMOJI[chat_settings.allow_service_messages],
                callback_data="settings allow_service_messages",
            ),
        ]
    )

    return keyboard


def BuildNightModeSettingsMenu(
    chat_settings: db_management.ChatSettings, selected_setting: str = None
) -> list:
    keyboard = list()
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "night_mode_punishment"),
                callback_data="(i)settings night_mode_punishment",
            )
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=utils.ConvertTimedModeToTime(value=chat_settings.night_mode_from),
                callback_data="settings night_mode_from",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=dictionaries.YES_NO_EMOJI[chat_settings.night_mode_punishment]
                if not chat_settings.night_mode_punishment
                else f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.night_mode_punishment]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.night_mode_punishment])}",
                callback_data="settings night_mode_punishment",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=utils.ConvertTimedModeToTime(value=chat_settings.night_mode_to),
                callback_data="settings night_mode_to",
            ),
        ]
    )
    if selected_setting == "night_mode_punishment":
        punishments_rows = [
            [
                pyrogram.types.InlineKeyboardButton(
                    text=dictionaries.YES_NO_EMOJI[0],
                    callback_data=f"settings {selected_setting} selectvalue0",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[1]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[1])}",
                    callback_data=f"settings {selected_setting} selectvalue1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[2]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[2])}",
                    callback_data=f"settings {selected_setting} selectvalue2",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[3]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[3])}",
                    callback_data=f"settings {selected_setting} selectvalue3",
                ),
            ],
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[4]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[4])}",
                    callback_data=f"settings {selected_setting} selectvalue4",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[5]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[5])}",
                    callback_data=f"settings {selected_setting} selectvalue5",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[6]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[6])}",
                    callback_data=f"settings {selected_setting} selectvalue6",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[7]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[7])}",
                    callback_data=f"settings {selected_setting} selectvalue7",
                ),
            ],
        ]
        if not chat_settings.allow_temporary_punishments:
            # remove temporary punishments from the rows
            tmp = punishments_rows[0].pop(3)
            punishments_rows[1][0] = tmp
            punishments_rows[1].pop(2)

        keyboard[-1][1].text = f".{keyboard[-1][1].text}."
        keyboard.extend(punishments_rows)
    elif (
        selected_setting == "night_mode_fromhour"
        or selected_setting == "night_mode_tohour"
        or selected_setting == "night_mode_fromminute"
        or selected_setting == "night_mode_tominute"
    ):
        setting = None
        if "night_mode_from" in selected_setting:
            setting = "night_mode_from"
            # mark what is selected
            keyboard[-1][0].text = f".{keyboard[-1][0].text}."
        elif "night_mode_to" in selected_setting:
            setting = "night_mode_to"
            keyboard[-1][2].text = f".{keyboard[-1][2].text}."
        if "hour" in selected_setting:
            hours_rows = [
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=f"{i:02d}",
                        callback_data=f"settings {setting} selecthour {j}",
                    )
                    for i, j in zip(range(0, 6), range(0, 24, 4))
                ],
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=f"{i:02d}",
                        callback_data=f"settings {setting} selecthour {j}",
                    )
                    for i, j in zip(range(6, 12), range(24, 48, 4))
                ],
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=f"{i:02d}",
                        callback_data=f"settings {setting} selecthour {j}",
                    )
                    for i, j in zip(range(12, 18), range(48, 72, 4))
                ],
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=f"{i:02d}",
                        callback_data=f"settings {setting} selecthour {j}",
                    )
                    for i, j in zip(range(18, 24), range(72, 96, 4))
                ],
            ]
            keyboard.extend(hours_rows)
        elif "minute" in selected_setting:
            minutes_rows = [
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=utils.ConvertTimedModeToTime(
                            value=getattr(chat_settings, setting)
                        ),
                        callback_data=f"settings {setting} selectminute {getattr(chat_settings, setting)}",
                    ),
                    pyrogram.types.InlineKeyboardButton(
                        text=utils.ConvertTimedModeToTime(
                            value=getattr(chat_settings, setting) + 1
                        ),
                        callback_data=f"settings {setting} selectminute {getattr(chat_settings, setting) + 1}",
                    ),
                    pyrogram.types.InlineKeyboardButton(
                        text=utils.ConvertTimedModeToTime(
                            value=getattr(chat_settings, setting) + 2
                        ),
                        callback_data=f"settings {setting} selectminute {getattr(chat_settings, setting) + 2}",
                    ),
                    pyrogram.types.InlineKeyboardButton(
                        text=utils.ConvertTimedModeToTime(
                            value=getattr(chat_settings, setting) + 3
                        ),
                        callback_data=f"settings {setting} selectminute {getattr(chat_settings, setting) + 3}",
                    ),
                ]
            ]
            keyboard.extend(minutes_rows)
    return keyboard


def BuildSlowModeSettingsMenu(
    chat_settings: db_management.ChatSettings, selected_setting: str = None
) -> list:
    keyboard = list()
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "slow_mode_value"),
                callback_data="(i)settings slow_mode_value",
            )
        ]
    )
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=utils.ConvertTimedModeToTime(value=chat_settings.slow_mode_from),
                callback_data="settings slow_mode_from",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=dictionaries.YES_NO_EMOJI[chat_settings.slow_mode_value]
                if not chat_settings.slow_mode_value
                else utils.TimeFormatter(
                    int(dictionaries.SLOW_MODE_VALUES[chat_settings.slow_mode_value])
                    * 1000
                ),
                callback_data="settings slow_mode_value",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=utils.ConvertTimedModeToTime(value=chat_settings.slow_mode_to),
                callback_data="settings slow_mode_to",
            ),
        ]
    )

    if selected_setting == "slow_mode_value":
        mode_values = [
            [
                pyrogram.types.InlineKeyboardButton(
                    text=dictionaries.YES_NO_EMOJI[0],
                    callback_data="settings slow_mode_value selectvalue0",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=utils.TimeFormatter(
                        int(dictionaries.SLOW_MODE_VALUES[1]) * 1000
                    ),
                    callback_data="settings slow_mode_value selectvalue1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=utils.TimeFormatter(
                        int(dictionaries.SLOW_MODE_VALUES[2]) * 1000
                    ),
                    callback_data="settings slow_mode_value selectvalue2",
                ),
            ],
            [
                pyrogram.types.InlineKeyboardButton(
                    text=utils.TimeFormatter(
                        int(dictionaries.SLOW_MODE_VALUES[3]) * 1000
                    ),
                    callback_data="settings slow_mode_value selectvalue3",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=utils.TimeFormatter(
                        int(dictionaries.SLOW_MODE_VALUES[4]) * 1000
                    ),
                    callback_data="settings slow_mode_value selectvalue4",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=utils.TimeFormatter(
                        int(dictionaries.SLOW_MODE_VALUES[5]) * 1000
                    ),
                    callback_data="settings slow_mode_value selectvalue5",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=utils.TimeFormatter(
                        int(dictionaries.SLOW_MODE_VALUES[6]) * 1000
                    ),
                    callback_data="settings slow_mode_value selectvalue6",
                ),
            ],
        ]
        keyboard[-1][1].text = f".{keyboard[-1][1].text}."
        keyboard.extend(mode_values)
    elif (
        selected_setting == "slow_mode_fromhour"
        or selected_setting == "slow_mode_tohour"
        or selected_setting == "slow_mode_fromminute"
        or selected_setting == "slow_mode_tominute"
    ):
        setting = None
        if "slow_mode_from" in selected_setting:
            setting = "slow_mode_from"
            # mark what is selected
            keyboard[-1][0].text = f".{keyboard[-1][0].text}."
        elif "slow_mode_to" in selected_setting:
            setting = "slow_mode_to"
            keyboard[-1][2].text = f".{keyboard[-1][2].text}."
        if "hour" in selected_setting:
            hours_rows = [
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=f"{i:02d}",
                        callback_data=f"settings {setting} selecthour {j}",
                    )
                    for i, j in zip(range(0, 6), range(0, 24, 4))
                ],
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=f"{i:02d}",
                        callback_data=f"settings {setting} selecthour {j}",
                    )
                    for i, j in zip(range(6, 12), range(24, 48, 4))
                ],
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=f"{i:02d}",
                        callback_data=f"settings {setting} selecthour {j}",
                    )
                    for i, j in zip(range(12, 18), range(48, 72, 4))
                ],
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=f"{i:02d}",
                        callback_data=f"settings {setting} selecthour {j}",
                    )
                    for i, j in zip(range(18, 24), range(72, 96, 4))
                ],
            ]
            keyboard.extend(hours_rows)
        elif "minute" in selected_setting:
            minutes_rows = [
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=utils.ConvertTimedModeToTime(
                            value=getattr(chat_settings, setting)
                        ),
                        callback_data=f"settings {setting} selectminute{getattr(chat_settings, setting)}",
                    ),
                    pyrogram.types.InlineKeyboardButton(
                        text=utils.ConvertTimedModeToTime(
                            value=getattr(chat_settings, setting) + 1
                        ),
                        callback_data=f"settings {setting} selectminute{getattr(chat_settings, setting) + 1}",
                    ),
                    pyrogram.types.InlineKeyboardButton(
                        text=utils.ConvertTimedModeToTime(
                            value=getattr(chat_settings, setting) + 2
                        ),
                        callback_data=f"settings {setting} selectminute{getattr(chat_settings, setting) + 2}",
                    ),
                    pyrogram.types.InlineKeyboardButton(
                        text=utils.ConvertTimedModeToTime(
                            value=getattr(chat_settings, setting) + 3
                        ),
                        callback_data=f"settings {setting} selectminute{getattr(chat_settings, setting) + 3}",
                    ),
                ]
            ]
            keyboard.extend(minutes_rows)
    return keyboard


def BuildTempPunishmentMenu(
    chat_settings: db_management.ChatSettings,
    max_temp_punishment_time: int = None,
    current_keyboard: typing.Union[str, bytes] = None,
    punishing_user: bool = False,
) -> list:
    keyboard = list()
    if not current_keyboard:
        restrict_duration = utils.ConvertUnixToDuration(
            timestamp=chat_settings.max_temp_restrict
        )
        ban_duration = utils.ConvertUnixToDuration(timestamp=chat_settings.max_temp_ban)

        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "max_temp_restrict"),
                    callback_data="(i)settings max_temp_restrict",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=pyrogram.emoji.INFINITY
                    if not chat_settings.max_temp_restrict
                    else (
                        (
                            (
                                f"{restrict_duration[0] * 7 + restrict_duration[1]} "
                                + _(chat_settings.language, "days")
                            )
                            if restrict_duration[0] * 7 + restrict_duration[1]
                            else ""
                        )
                        + (
                            (
                                f"{restrict_duration[2]} "
                                + _(chat_settings.language, "hours")
                            )
                            if restrict_duration[2]
                            else ""
                        )
                        + (
                            (
                                f"{restrict_duration[3]} "
                                + _(chat_settings.language, "minutes")
                            )
                            if restrict_duration[3]
                            else ""
                        )
                        + (
                            (
                                f"{restrict_duration[4]} "
                                + _(chat_settings.language, "seconds")
                            )
                            if restrict_duration[4]
                            else ""
                        )
                    ),
                    callback_data="settings max_temp_restrict",
                ),
            ]
        )

        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "max_temp_ban"),
                    callback_data="(i)settings max_temp_ban",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=pyrogram.emoji.INFINITY
                    if not chat_settings.max_temp_ban
                    else (
                        (
                            (
                                f"{ban_duration[0] * 7 + ban_duration[1]} "
                                + _(chat_settings.language, "days")
                            )
                            if ban_duration[0] * 7 + ban_duration[1]
                            else ""
                        )
                        + (
                            (f"{ban_duration[2]} " + _(chat_settings.language, "hours"))
                            if ban_duration[2]
                            else ""
                        )
                        + (
                            (
                                f"{ban_duration[3]} "
                                + _(chat_settings.language, "minutes")
                            )
                            if ban_duration[3]
                            else ""
                        )
                        + (
                            (
                                f"{ban_duration[4]} "
                                + _(chat_settings.language, "seconds")
                            )
                            if ban_duration[4]
                            else ""
                        )
                    ),
                    callback_data="settings max_temp_ban",
                ),
            ]
        )
    else:
        current_keyboard = current_keyboard.replace("useless", "")
        duration = utils.ConvertUnixToDuration(timestamp=max_temp_punishment_time)
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "weeks") + f" ({duration[0]})",
                    callback_data=f"(i){current_keyboard} weeks",
                )
            ]
        )
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "decrement_X").format(10),
                    callback_data=f"{current_keyboard} weeks-10",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "decrement_X").format(5),
                    callback_data=f"{current_keyboard} weeks-5",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "decrement_X").format(1),
                    callback_data=f"{current_keyboard} weeks-1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "increment_X").format(1),
                    callback_data=f"{current_keyboard} weeks+1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "increment_X").format(5),
                    callback_data=f"{current_keyboard} weeks+5",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "increment_X").format(10),
                    callback_data=f"{current_keyboard} weeks+10",
                ),
            ]
        )

        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "days") + f" ({duration[1]})",
                    callback_data=f"(i){current_keyboard} days",
                )
            ]
        )
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "decrement_X").format(3),
                    callback_data=f"{current_keyboard} days-3",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "decrement_X").format(2),
                    callback_data=f"{current_keyboard} days-2",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "decrement_X").format(1),
                    callback_data=f"{current_keyboard} days-1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "increment_X").format(1),
                    callback_data=f"{current_keyboard} days+1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "increment_X").format(2),
                    callback_data=f"{current_keyboard} days+2",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "increment_X").format(3),
                    callback_data=f"{current_keyboard} days+3",
                ),
            ]
        )

        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "hours") + f" ({duration[2]})",
                    callback_data=f"(i){current_keyboard} hours",
                )
            ]
        )
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "decrement_X").format(7),
                    callback_data=f"{current_keyboard} hours-7",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "decrement_X").format(4),
                    callback_data=f"{current_keyboard} hours-4",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "decrement_X").format(1),
                    callback_data=f"{current_keyboard} hours-1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "increment_X").format(1),
                    callback_data=f"{current_keyboard} hours+1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "increment_X").format(4),
                    callback_data=f"{current_keyboard} hours+4",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "increment_X").format(7),
                    callback_data=f"{current_keyboard} hours+7",
                ),
            ]
        )

        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "minutes") + f" ({duration[3]})",
                    callback_data=f"(i){current_keyboard} minutes",
                )
            ]
        )
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "decrement_X").format(10),
                    callback_data=f"{current_keyboard} minutes-10",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "decrement_X").format(5),
                    callback_data=f"{current_keyboard} minutes-5",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "decrement_X").format(1),
                    callback_data=f"{current_keyboard} minutes-1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "increment_X").format(1),
                    callback_data=f"{current_keyboard} minutes+1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "increment_X").format(5),
                    callback_data=f"{current_keyboard} minutes+5",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "increment_X").format(10),
                    callback_data=f"{current_keyboard} minutes+10",
                ),
            ]
        )

        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "seconds") + f" ({duration[4]})",
                    callback_data=f"(i){current_keyboard} seconds",
                )
            ]
        )
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "decrement_X").format(10),
                    callback_data=f"{current_keyboard} seconds-10",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "decrement_X").format(5),
                    callback_data=f"{current_keyboard} seconds-5",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "decrement_X").format(1),
                    callback_data=f"{current_keyboard} seconds-1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "increment_X").format(1),
                    callback_data=f"{current_keyboard} seconds+1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "increment_X").format(5),
                    callback_data=f"{current_keyboard} seconds+5",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "increment_X").format(10),
                    callback_data=f"{current_keyboard} seconds+10",
                ),
            ]
        )
        if max_temp_punishment_time:
            keyboard.append(
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=(
                            (
                                f"{duration[0] * 7 + duration[1]} "
                                + _(chat_settings.language, "days")
                            )
                            if duration[0] * 7 + duration[1]
                            else ""
                        )
                        + (
                            (f"{duration[2]} " + _(chat_settings.language, "hours"))
                            if duration[2]
                            else ""
                        )
                        + (
                            (f"{duration[3]} " + _(chat_settings.language, "minutes"))
                            if duration[3]
                            else ""
                        )
                        + (
                            (f"{duration[4]} " + _(chat_settings.language, "seconds"))
                            if duration[4]
                            else ""
                        ),
                        callback_data=f"{current_keyboard} {max_temp_punishment_time}"
                        if punishing_user
                        else f"useless{current_keyboard} {max_temp_punishment_time}",
                    )
                ]
            )
        else:
            keyboard.append(
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=pyrogram.emoji.INFINITY,
                        callback_data=f"{current_keyboard} 0"
                        if punishing_user
                        else f"useless{current_keyboard} 0",
                    )
                ]
            )
    return keyboard


def BuildWelcomeButtonsKeyboard(welcome_buttons: str) -> list:
    keyboard = list()
    for row in welcome_buttons.splitlines():
        keyboard_row = list()
        for button in row.split("&&"):
            button_parameters = button.split("|")
            if len(button_parameters) > 1:
                keyboard_row.append(
                    pyrogram.types.InlineKeyboardButton(
                        text=button_parameters[0].strip(),
                        url=button_parameters[1].strip(),
                    )
                )
        keyboard.append(keyboard_row)
    return keyboard


def BuildCensorshipsList(
    chat_settings: db_management.ChatSettings,
    page: int = 0,
    selected_setting: str = None,
) -> list:
    if selected_setting:
        punishments_rows = [
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[0]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[0])}",
                    callback_data=f"censorships {selected_setting} selectvalue0",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[1]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[1])}",
                    callback_data=f"censorships {selected_setting} selectvalue1",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[2]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[2])}",
                    callback_data=f"censorships {selected_setting} selectvalue2",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[3]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[3])}",
                    callback_data=f"censorships {selected_setting} selectvalue3",
                ),
            ],
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[4]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[4])}",
                    callback_data=f"censorships {selected_setting} selectvalue4",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[5]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[5])}",
                    callback_data=f"censorships {selected_setting} selectvalue5",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[6]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[6])}",
                    callback_data=f"censorships {selected_setting} selectvalue6",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[7]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[7])}",
                    callback_data=f"censorships {selected_setting} selectvalue7",
                ),
            ],
        ]
        if not chat_settings.allow_temporary_punishments:
            # remove temporary punishments from the rows
            tmp = punishments_rows[0].pop(3)
            punishments_rows[1][0] = tmp
            punishments_rows[1].pop(2)

    header = list()
    header.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "censorships").upper(),
                callback_data=f"uselesscensorships {chat_settings.chat_id} {page}",
            )
        ]
    )

    keyboard = list()
    if not selected_setting or selected_setting == "punishment":
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "censorships_punishment"),
                    callback_data="(i)settings censorships_punishment",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.PUNISHMENT_EMOJI[chat_settings.censorships_punishment]} {_(chat_settings.language, dictionaries.PUNISHMENT_STRING[chat_settings.censorships_punishment])}",
                    callback_data="censorships punishment",
                ),
            ]
        )
        if selected_setting == "punishment":
            keyboard.extend(punishments_rows)

        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "add_censorship"),
                    callback_data=f"censorships add",
                )
            ]
        )

        query: peewee.ModelSelect = chat_settings.censorships.order_by(
            peewee.fn.LOWER(db_management.ChatCensorships.value)
        )
        page = AdjustPage(
            page=page,
            max_n=len(query),
            max_items_page=utils.config["max_items_keyboard"],
        )
        begin = page * utils.config["max_items_keyboard"]
        end = min(len(query), (page + 1) * utils.config["max_items_keyboard"])
        for i in range(begin, end):
            keyboard.append(
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=query[i].value, callback_data=f"(i)censorships {i}",
                    ),
                    pyrogram.types.InlineKeyboardButton(
                        text=pyrogram.emoji.EYE + _(chat_settings.language, "get"),
                        callback_data=f"censorships get {i}",
                    ),
                    pyrogram.types.InlineKeyboardButton(
                        text=pyrogram.emoji.CROSS_MARK,
                        callback_data=f"censorships remove {i}",
                    ),
                ]
            )

        footer = BuildPager(
            base_callback_data="censorships",
            page=page,
            n_items=len(query),
            max_items_keyboard=utils.config["max_items_keyboard"],
        )
        footer.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "back_to_settings_menu").format(
                        pyrogram.emoji.GEAR
                    ),
                    callback_data="mainsettings",
                )
            ]
        )

        return BuildKeyboard(
            main_buttons=keyboard, header_buttons=header, footer_buttons=footer
        )
    elif selected_setting == "add":
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "text"),
                    callback_data="censorships add text",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "media"),
                    callback_data="censorships add media",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "regex"),
                    callback_data="censorships add regex",
                ),
            ]
        )

        return BuildKeyboard(main_buttons=keyboard, header_buttons=header)


def BuildExtraList(
    chat_settings: db_management.ChatSettings,
    page: int = 0,
    selected_setting: str = None,
) -> list:
    header = list()
    header.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "extras").upper(),
                callback_data=f"uselessextras {chat_settings.chat_id} {page}",
            )
        ]
    )

    keyboard = list()
    if not selected_setting:
        header.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "set_extra"),
                    callback_data=f"extras set",
                )
            ]
        )
        query: peewee.ModelSelect = chat_settings.extras.order_by(
            peewee.fn.LOWER(db_management.ChatExtras.key)
        ).where(~db_management.ChatExtras.is_group_data)
        page = AdjustPage(
            page=page,
            max_n=len(query),
            max_items_page=utils.config["max_items_keyboard"],
        )
        begin = page * utils.config["max_items_keyboard"]
        end = min(len(query), (page + 1) * utils.config["max_items_keyboard"])
        for i in range(begin, end):
            keyboard.append(
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=query[i].key, callback_data=f"(i)extras {i}",
                    ),
                    pyrogram.types.InlineKeyboardButton(
                        text=pyrogram.emoji.MEMO + _(chat_settings.language, "set"),
                        callback_data=f"extras replace {i}",
                    ),
                    pyrogram.types.InlineKeyboardButton(
                        text=pyrogram.emoji.EYE + _(chat_settings.language, "get"),
                        callback_data=f"extras get {i}",
                    ),
                    pyrogram.types.InlineKeyboardButton(
                        text=pyrogram.emoji.CROSS_MARK
                        + _(chat_settings.language, "unset"),
                        callback_data=f"extras unset {i}",
                    ),
                ]
            )

        footer = BuildPager(
            base_callback_data="extras",
            page=page,
            n_items=len(query),
            max_items_keyboard=utils.config["max_items_keyboard"],
        )

        return BuildKeyboard(
            main_buttons=keyboard, header_buttons=header, footer_buttons=footer
        )
    elif selected_setting == "set":
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "key_text_value_text"),
                    callback_data=f"extras set text text",
                ),
            ]
        )
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "key_text_value_media"),
                    callback_data=f"extras set text media",
                ),
            ]
        )
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "key_regex_value_text"),
                    callback_data=f"extras set regex text",
                ),
            ]
        )
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "key_regex_value_media"),
                    callback_data=f"extras set regex media",
                ),
            ]
        )

        return BuildKeyboard(main_buttons=keyboard, header_buttons=header)


def BuildMessagesList(
    chat_settings: db_management.ChatSettings, members_only: bool = True, page: int = 0
) -> list:
    total_chat_messages = (
        db_management.RUserChat.select(
            peewee.fn.SUM(db_management.RUserChat.message_counter).alias("total")
        )
        .where(
            (db_management.RUserChat.chat == chat_settings.chat)
            & (db_management.RUserChat.is_member)
        )
        .group_by(db_management.RUserChat.chat)[0]
        .total
        if members_only
        else db_management.RUserChat.select(
            peewee.fn.SUM(db_management.RUserChat.message_counter).alias("total")
        )
        .where(db_management.RUserChat.chat == chat_settings.chat)
        .group_by(db_management.RUserChat.chat)[0]
        .total
    )
    header = [
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "messages").upper()
                + f" ({total_chat_messages})",
                callback_data=f"uselessmessages {chat_settings.chat_id} {int(members_only)} {page}",
            )
        ],
    ]

    keyboard = list()
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "members_only"),
                callback_data="(i)messages members_only",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=dictionaries.YES_NO_EMOJI[int(members_only)],
                callback_data="messages members_only",
            ),
        ]
    )
    query: peewee.ModelSelect = (
        db_management.RUserChat.select()
        .where(
            (db_management.RUserChat.chat_id == chat_settings.chat_id)
            & (db_management.RUserChat.is_member)
        )
        .join(
            db_management.Users,
            on=(db_management.RUserChat.user_id == db_management.Users.id),
        )
        .order_by(
            db_management.RUserChat.message_counter.desc(),
            peewee.fn.LOWER(db_management.Users.first_name),
            peewee.fn.LOWER(db_management.Users.last_name),
            db_management.Users.id,
        )
        if members_only
        else db_management.RUserChat.select()
        .where(db_management.RUserChat.chat_id == chat_settings.chat_id)
        .join(
            db_management.Users,
            on=(db_management.RUserChat.user_id == db_management.Users.id),
        )
        .order_by(
            db_management.RUserChat.message_counter.desc(),
            peewee.fn.LOWER(db_management.Users.first_name),
            peewee.fn.LOWER(db_management.Users.last_name),
            db_management.Users.id,
        )
    )
    page = AdjustPage(
        page=page, max_n=len(query), max_items_page=utils.config["max_items_keyboard"],
    )
    begin = page * utils.config["max_items_keyboard"]
    end = min(len(query), (page + 1) * utils.config["max_items_keyboard"])
    for i in range(begin, end):
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{query[i].user_id} - {query[i].user.first_name}",
                    callback_data=f"(i)messages {query[i].user_id}",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{query[i].message_counter * 100 / total_chat_messages:.2f}% ({query[i].message_counter})",
                    callback_data="uselessmessages",
                ),
            ]
        )

    footer = BuildPager(
        base_callback_data="messages",
        page=page,
        n_items=len(query),
        max_items_keyboard=utils.config["max_items_keyboard"],
    )

    return BuildKeyboard(
        main_buttons=keyboard, header_buttons=header, footer_buttons=footer
    )


def BuildInactivesConfirmation(
    chat_settings: db_management.ChatSettings, method: str, min_date: datetime.datetime
) -> list:
    header = [
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, method).upper()
                + " "
                + _(chat_settings.language, "inactives").upper(),
                callback_data=f"uselessinactives {chat_settings.chat_id} {method} {min_date}",
            )
        ],
    ]

    keyboard = [
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "yes"), callback_data="inactives yes",
            ),
        ],
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "yes_send_list"),
                callback_data="inactives yes_list",
            ),
        ],
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "yes_send_list_pvt"),
                callback_data="inactives yes_list_pvt",
            ),
        ],
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "no_send_list_pvt"),
                callback_data="inactives no_list_pvt",
            ),
        ],
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "no_send_list"),
                callback_data="inactives no_list",
            ),
        ],
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "no"), callback_data="inactives no",
            ),
        ],
    ]

    return BuildKeyboard(main_buttons=keyboard, header_buttons=header)


def BuildWhitelistedUsersList(
    chat_settings: db_management.ChatSettings, page: int = 0,
) -> list:
    header = [
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "whitelisted_users").upper(),
                callback_data=f"uselesswhitelisted {chat_settings.chat_id} {page}",
            )
        ],
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "add_user"),
                callback_data="whitelisted add",
            )
        ],
    ]

    keyboard = list()
    query: peewee.ModelSelect = (
        db_management.RUserChat.select()
        .where(
            (db_management.RUserChat.chat_id == chat_settings.chat_id)
            & (db_management.RUserChat.is_whitelisted)
        )
        .join(
            db_management.Users,
            on=(db_management.RUserChat.user_id == db_management.Users.id),
        )
        .order_by(
            peewee.fn.LOWER(db_management.Users.first_name),
            peewee.fn.LOWER(db_management.Users.last_name),
            db_management.Users.id,
        )
    )
    page = AdjustPage(
        page=page, max_n=len(query), max_items_page=utils.config["max_items_keyboard"],
    )
    begin = page * utils.config["max_items_keyboard"]
    end = min(len(query), (page + 1) * utils.config["max_items_keyboard"])
    for i in range(begin, end):
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{query[i].user_id} - {query[i].user.first_name}",
                    callback_data=f"(i)whitelisted  {query[i].user_id}",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=pyrogram.emoji.CROSS_MARK,
                    callback_data=f"whitelisted remove {query[i].user_id}",
                ),
            ]
        )

    footer = BuildPager(
        base_callback_data="whitelisted",
        page=page,
        n_items=len(query),
        max_items_keyboard=utils.config["max_items_keyboard"],
    )
    footer.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "back_to_settings_menu").format(
                    pyrogram.emoji.GEAR
                ),
                callback_data="mainsettings",
            )
        ]
    )

    return BuildKeyboard(
        main_buttons=keyboard, header_buttons=header, footer_buttons=footer
    )


def BuildWhitelistedGbannedUsersList(
    chat_settings: db_management.ChatSettings, page: int = 0,
) -> list:
    header = [
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "whitelistedgbanned_users").upper(),
                callback_data=f"uselesswhitelistedgbanned {chat_settings.chat_id} {page}",
            )
        ],
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "add_user"),
                callback_data="whitelistedgbanned add",
            )
        ],
    ]

    keyboard = list()
    query: peewee.ModelSelect = (
        db_management.RUserChat.select()
        .where(
            (db_management.RUserChat.chat_id == chat_settings.chat_id)
            & (db_management.RUserChat.is_global_ban_whitelisted)
        )
        .join(
            db_management.Users,
            on=(db_management.RUserChat.user_id == db_management.Users.id),
        )
        .order_by(
            peewee.fn.LOWER(db_management.Users.first_name),
            peewee.fn.LOWER(db_management.Users.last_name),
            db_management.Users.id,
        )
    )
    page = AdjustPage(
        page=page, max_n=len(query), max_items_page=utils.config["max_items_keyboard"],
    )
    begin = page * utils.config["max_items_keyboard"]
    end = min(len(query), (page + 1) * utils.config["max_items_keyboard"])
    for i in range(begin, end):
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{query[i].user_id} - {query[i].user.first_name}",
                    callback_data=f"(i)whitelistedgbanned  {query[i].user_id}",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=pyrogram.emoji.CROSS_MARK,
                    callback_data=f"whitelistedgbanned remove {query[i].user_id}",
                ),
            ]
        )

    footer = BuildPager(
        base_callback_data="whitelistedgbanned",
        page=page,
        n_items=len(query),
        max_items_keyboard=utils.config["max_items_keyboard"],
    )
    footer.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "back_to_settings_menu").format(
                    pyrogram.emoji.GEAR
                ),
                callback_data="mainsettings",
            )
        ]
    )

    return BuildKeyboard(
        main_buttons=keyboard, header_buttons=header, footer_buttons=footer
    )


def BuildWhitelistedChatsList(
    chat_settings: db_management.ChatSettings, page: int = 0,
) -> list:
    header = [
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "whitelisted_chats").upper(),
                callback_data=f"uselesswhitelistedchats {chat_settings.chat_id} {page}",
            )
        ],
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "add_chat"),
                callback_data="whitelistedchats add",
            )
        ],
    ]

    keyboard = list()
    query: peewee.ModelSelect = (
        chat_settings.whitelisted_chats.join(
            db_management.Chats,
            on=(db_management.ChatWhitelistedChats.chat_id == db_management.Chats.id),
        )
        .where(db_management.ChatWhitelistedChats.chat_id == chat_settings.chat_id)
        .order_by(
            peewee.fn.LOWER(db_management.Chats.title),
            peewee.fn.LOWER(db_management.Chats.id),
        )
    )
    page = AdjustPage(
        page=page, max_n=len(query), max_items_page=utils.config["max_items_keyboard"],
    )
    begin = page * utils.config["max_items_keyboard"]
    end = min(len(query), (page + 1) * utils.config["max_items_keyboard"])
    for i in range(begin, end):
        text = None
        if query[i].whitelisted_chat > 0:
            text = _(chat_settings.language, "link") + f" - {query[i].whitelisted_chat}"
        else:
            chat = db_management.Chats.get_or_none(id=query[i].whitelisted_chat)
            text = f"{query[i].whitelisted_chat} - {chat.title if chat else None}"
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=text,
                    callback_data=f"(i)whitelistedchats  {query[i].whitelisted_chat}",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=pyrogram.emoji.CROSS_MARK,
                    callback_data=f"whitelistedchats remove {query[i].whitelisted_chat}",
                ),
            ]
        )

    footer = BuildPager(
        base_callback_data="whitelistedchats",
        page=page,
        n_items=len(query),
        max_items_keyboard=utils.config["max_items_keyboard"],
    )
    footer.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "back_to_settings_menu").format(
                    pyrogram.emoji.GEAR
                ),
                callback_data="mainsettings",
            )
        ]
    )

    return BuildKeyboard(
        main_buttons=keyboard, header_buttons=header, footer_buttons=footer
    )


def BuildGloballyBannedUsersList(
    chat_settings: typing.Union[db_management.ChatSettings, db_management.UserSettings],
    page: int = 0,
) -> list:
    header = [
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "globally_banned_users").upper(),
                callback_data=f"uselessgbanned {page}",
            )
        ],
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "add_user"), callback_data="gbanned add",
            )
        ],
    ]

    keyboard = list()
    query: peewee.ModelSelect = (
        db_management.UserSettings.select()
        .where(db_management.UserSettings.global_ban_expiration > datetime.date.today())
        .join(
            db_management.Users,
            on=(db_management.UserSettings.user_id == db_management.Users.id),
        )
        .order_by(
            peewee.fn.LOWER(db_management.Users.first_name),
            peewee.fn.LOWER(db_management.Users.last_name),
            db_management.Users.id,
        )
    )
    page = AdjustPage(
        page=page, max_n=len(query), max_items_page=utils.config["max_items_keyboard"],
    )
    begin = page * utils.config["max_items_keyboard"]
    end = min(len(query), (page + 1) * utils.config["max_items_keyboard"])
    for i in range(begin, end):
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{query[i].user_id} - {query[i].user.first_name}",
                    callback_data=f"(i)gbanned  {query[i].user_id}",
                ),
            ]
        )
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{query[i].global_ban_expiration}",
                    callback_data=f"(i)gbanned  {query[i].user_id}",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=pyrogram.emoji.CROSS_MARK,
                    callback_data=f"gbanned remove {query[i].user_id}",
                ),
            ]
        )

    footer = BuildPager(
        base_callback_data="gbanned",
        page=page,
        n_items=len(query),
        max_items_keyboard=utils.config["max_items_keyboard"],
    )

    return BuildKeyboard(
        main_buttons=keyboard, header_buttons=header, footer_buttons=footer
    )


def BuildBlockedUsersList(
    chat_settings: typing.Union[db_management.ChatSettings, db_management.UserSettings],
    page: int = 0,
) -> list:
    header = [
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "blocked_users").upper(),
                callback_data=f"uselessblocked {page}",
            )
        ],
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "add_user"), callback_data="blocked add",
            )
        ],
    ]

    keyboard = list()
    query: peewee.ModelSelect = (
        db_management.UserSettings.select()
        .where(db_management.UserSettings.block_expiration > datetime.datetime.utcnow())
        .join(
            db_management.Users,
            on=(db_management.UserSettings.user_id == db_management.Users.id),
        )
        .order_by(
            peewee.fn.LOWER(db_management.Users.first_name),
            peewee.fn.LOWER(db_management.Users.last_name),
            db_management.Users.id,
        )
    )
    page = AdjustPage(
        page=page, max_n=len(query), max_items_page=utils.config["max_items_keyboard"],
    )
    begin = page * utils.config["max_items_keyboard"]
    end = min(len(query), (page + 1) * utils.config["max_items_keyboard"])
    for i in range(begin, end):
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{query[i].user_id} - {query[i].user.first_name}",
                    callback_data=f"(i)blocked  {query[i].user_id}",
                ),
            ]
        )
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{query[i].block_expiration}",
                    callback_data=f"(i)blocked  {query[i].user_id}",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=pyrogram.emoji.CROSS_MARK,
                    callback_data=f"blocked remove {query[i].user_id}",
                ),
            ]
        )

    footer = BuildPager(
        base_callback_data="blocked",
        page=page,
        n_items=len(query),
        max_items_keyboard=utils.config["max_items_keyboard"],
    )

    return BuildKeyboard(
        main_buttons=keyboard, header_buttons=header, footer_buttons=footer
    )


def BuildAlternativeCommandsList(
    chat_settings: db_management.ChatSettings, page: int = 0,
) -> list:
    header = list()
    header.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "alternatives").upper(),
                callback_data=f"uselessalternatives {chat_settings.chat_id} {page}",
            )
        ]
    )
    header.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "set_alternative"),
                callback_data=f"alternatives set",
            )
        ]
    )

    keyboard = list()
    query: peewee.ModelSelect = chat_settings.alternative_commands.order_by(
        peewee.fn.LOWER(db_management.ChatAlternatives.original),
        peewee.fn.LOWER(db_management.ChatAlternatives.alternative),
    )
    page = AdjustPage(
        page=page, max_n=len(query), max_items_page=utils.config["max_items_keyboard"],
    )
    begin = page * utils.config["max_items_keyboard"]
    end = min(len(query), (page + 1) * utils.config["max_items_keyboard"])
    for i in range(begin, end):
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"/{query[i].original}", callback_data=f"(i)alternatives {i}",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{pyrogram.emoji.EYE} {query[i].alternative}",
                    callback_data=f"alternatives get {i}",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=pyrogram.emoji.CROSS_MARK + _(chat_settings.language, "unset"),
                    callback_data=f"alternatives unset {i}",
                ),
            ]
        )

    footer = BuildPager(
        base_callback_data="alternatives",
        page=page,
        n_items=len(query),
        max_items_keyboard=utils.config["max_items_keyboard"],
    )
    footer.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "back_to_settings_menu").format(
                    pyrogram.emoji.GEAR
                ),
                callback_data="mainsettings",
            )
        ]
    )

    return BuildKeyboard(
        main_buttons=keyboard, header_buttons=header, footer_buttons=footer
    )


def BuildPromotionsKeyboard(
    chat_settings: db_management.ChatSettings, r_user_chat: db_management.RUserChat
) -> list:
    keyboard = list()

    return keyboard


def BuildPermissionsKeyboard(
    chat_settings: db_management.ChatSettings,
    r_bot_chat: db_management.RUserChat,
    r_user_chat: db_management.RUserChat,
) -> list:
    keyboard = list()
    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "can_be_edited")
                + " "
                + (
                    _(chat_settings.language, "yes")
                    if r_user_chat.can_be_edited
                    else _(chat_settings.language, "no")
                ),
                callback_data="(i)permissions can_be_edited",
            )
        ]
    )

    for permission in dictionaries.PERMISSIONS:
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, permission),
                    callback_data=f"(i)permissions {permission}",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=(
                        ""
                        if r_bot_chat.can_promote_members
                        and getattr(r_bot_chat, permission, 0)
                        and r_user_chat.rank < 3
                        else pyrogram.emoji.NO_ENTRY
                    )
                    + dictionaries.YES_NO_EMOJI[
                        getattr(r_user_chat, permission, 0)
                        if r_user_chat.rank < 3
                        else 1
                    ],
                    callback_data=f"permissions {permission}",
                ),
            ]
        )

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "is_admin_on_telegram")
                + " "
                + (
                    _(chat_settings.language, "yes")
                    if r_user_chat.is_admin
                    else _(chat_settings.language, "no")
                ),
                callback_data="(i)permissions is_admin_on_telegram",
            )
        ]
    )

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "sync_bot2tg"),
                callback_data="permissions sync_bot2tg",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "sync_tg2bot"),
                callback_data="permissions sync_tg2bot",
            ),
        ]
    )

    return keyboard


def BuildRestrictionsKeyboard(
    chat_settings: db_management.ChatSettings,
    r_bot_chat: db_management.RUserChat,
    chat_member: pyrogram.types.ChatMember,
) -> list:
    keyboard = list()
    for restriction in dictionaries.RESTRICTIONS:
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, restriction),
                    callback_data="(i)restrictions {restriction}",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=(
                        ""
                        if r_bot_chat.can_restrict_members
                        and chat_member.status != "creator"
                        else pyrogram.emoji.NO_ENTRY
                    )
                    + dictionaries.YES_NO_EMOJI[
                        getattr(chat_member, restriction, 0)
                        if chat_member.status != "creator"
                        else 1
                    ],
                    callback_data="restrictions {restriction}",
                ),
            ]
        )

    return keyboard


def BuildInfoMenu(
    target: int,
    chat_id: int,
    current_keyboard: typing.Union[str, bytes],
    chat_settings: typing.Union[
        db_management.ChatSettings, db_management.UserSettings
    ] = None,
    r_target_chat: db_management.RUserChat = None,
    selected_setting: str = None,
) -> list:
    current_keyboard = current_keyboard.replace("useless", "")
    chat_settings = chat_settings or (
        # user in chat
        db_management.ChatSettings.get_or_none(chat_id=chat_id)
        if chat_id < 0
        else db_management.UserSettings.get_or_none(user_id=chat_id)
        # user or chat
    )

    header_buttons = list()
    header_buttons.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, current_keyboard).upper(),
                callback_data=f"useless{current_keyboard} {target} {chat_id}",
            )
        ]
    )

    keyboard = list()
    if current_keyboard == "maininfo":
        if target < 0:
            # chat
            keyboard.append(
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=pyrogram.emoji.GEAR
                        + _(chat_settings.language, "settings").upper()
                        + pyrogram.emoji.GEAR,
                        callback_data=f"mainsettings {chat_id}",
                    )
                ]
            )

            keyboard.append(
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=pyrogram.emoji.CONTROL_KNOBS
                        + _(chat_settings.language, "plugins").upper()
                        + pyrogram.emoji.CONTROL_KNOBS,
                        callback_data=f"chatplugins {chat_id} 0",
                    )
                ]
            )
        else:
            target_settings = db_management.UserSettings.get_or_none(user_id=target)
            if not target_settings:
                target_settings = db_management.UserSettings.create(user_id=target)

            if target_settings.global_ban_expiration > datetime.date.today():
                keyboard.append(
                    [
                        pyrogram.types.InlineKeyboardButton(
                            text=_(chat_settings.language, "info_gbanned"),
                            callback_data="(i)info gbanned",
                        ),
                        pyrogram.types.InlineKeyboardButton(
                            text=str(target_settings.global_ban_expiration),
                            callback_data="uselessinfo gbanned",
                        ),
                    ]
                )
            if target_settings.block_expiration > datetime.datetime.utcnow():
                keyboard.append(
                    [
                        pyrogram.types.InlineKeyboardButton(
                            text=_(chat_settings.language, "info_blocked"),
                            callback_data="(i)info blocked",
                        ),
                        pyrogram.types.InlineKeyboardButton(
                            text=str(target_settings.block_expiration),
                            callback_data="uselessinfo blocked",
                        ),
                    ]
                )

            if chat_id < 0:
                # info of target in chat_id
                r_target_chat = r_target_chat or db_management.RUserChat.get_or_none(
                    user_id=target, chat_id=chat_id
                )
                if not r_target_chat:
                    r_target_chat = db_management.RUserChat.create(
                        user_id=target, chat_id=chat_id
                    )
                keyboard.append(
                    [
                        pyrogram.types.InlineKeyboardButton(
                            text=_(chat_settings.language, "privileged_user"),
                            callback_data="(i)info privileged_user",
                        ),
                        pyrogram.types.InlineKeyboardButton(
                            text=_(chat_settings.language, "junior_mod"),
                            callback_data="(i)info junior_mod",
                        ),
                        pyrogram.types.InlineKeyboardButton(
                            text=_(chat_settings.language, "senior_mod"),
                            callback_data="(i)info senior_mod",
                        ),
                    ]
                )
                keyboard.append(
                    [
                        pyrogram.types.InlineKeyboardButton(
                            text=dictionaries.RADIOBUTTON_EMOJI[
                                int(
                                    r_target_chat.rank
                                    == dictionaries.RANK_STRING["privileged_user"]
                                )
                            ],
                            callback_data="info privileged_user",
                        ),
                        pyrogram.types.InlineKeyboardButton(
                            text=dictionaries.RADIOBUTTON_EMOJI[
                                int(
                                    r_target_chat.rank
                                    == dictionaries.RANK_STRING["junior_mod"]
                                )
                            ],
                            callback_data="info junior_mod",
                        ),
                        pyrogram.types.InlineKeyboardButton(
                            text=dictionaries.RADIOBUTTON_EMOJI[
                                int(
                                    r_target_chat.rank
                                    == dictionaries.RANK_STRING["senior_mod"]
                                )
                            ],
                            callback_data="info senior_mod",
                        ),
                    ]
                )

                if target_settings.global_ban_expiration > datetime.date.today():
                    keyboard.append(
                        [
                            pyrogram.types.InlineKeyboardButton(
                                text=_(chat_settings.language, "whitelisted"),
                                callback_data="(i)info whitelisted",
                            ),
                            pyrogram.types.InlineKeyboardButton(
                                text=_(
                                    chat_settings.language, "global_ban_whitelisted"
                                ),
                                callback_data="(i)info global_ban_whitelisted",
                            ),
                        ]
                    )
                    keyboard.append(
                        [
                            pyrogram.types.InlineKeyboardButton(
                                text=dictionaries.YES_NO_EMOJI[
                                    int(r_target_chat.is_whitelisted)
                                ],
                                callback_data="info whitelisted",
                            ),
                            pyrogram.types.InlineKeyboardButton(
                                text=dictionaries.YES_NO_EMOJI[
                                    int(r_target_chat.is_global_ban_whitelisted)
                                ],
                                callback_data="info global_ban_whitelisted",
                            ),
                        ]
                    )
                else:
                    keyboard.append(
                        [
                            pyrogram.types.InlineKeyboardButton(
                                text=_(chat_settings.language, "whitelisted"),
                                callback_data="(i)info whitelisted",
                            ),
                            pyrogram.types.InlineKeyboardButton(
                                text=dictionaries.YES_NO_EMOJI[
                                    int(r_target_chat.is_whitelisted)
                                ],
                                callback_data="info whitelisted",
                            ),
                        ]
                    )

                keyboard.append(
                    [
                        pyrogram.types.InlineKeyboardButton(
                            text=_(chat_settings.language, "decrement"),
                            callback_data="info warns--",
                        ),
                        pyrogram.types.InlineKeyboardButton(
                            text=_(chat_settings.language, "info_warns").format(
                                r_target_chat.warns, chat_settings.max_warns
                            ),
                            callback_data="(i)info warns",
                        ),
                        pyrogram.types.InlineKeyboardButton(
                            text=_(chat_settings.language, "increment"),
                            callback_data="info warns++",
                        ),
                    ]
                )

                keyboard.append(
                    [
                        pyrogram.types.InlineKeyboardButton(
                            text=_(chat_settings.language, "punish").upper(),
                            callback_data="info punishments",
                        )
                    ]
                )
                if selected_setting == "punishments":
                    keyboard.append(
                        [
                            pyrogram.types.InlineKeyboardButton(
                                text=dictionaries.PUNISHMENT_EMOJI[3]
                                + _(
                                    chat_settings.language,
                                    dictionaries.PUNISHMENT_STRING[3],
                                ),
                                callback_data="info punishments selectvalue3",
                            ),
                            pyrogram.types.InlineKeyboardButton(
                                text=dictionaries.PUNISHMENT_EMOJI[4]
                                + _(
                                    chat_settings.language,
                                    dictionaries.PUNISHMENT_STRING[4],
                                ),
                                callback_data="info punishments selectvalue4",
                            ),
                            pyrogram.types.InlineKeyboardButton(
                                text=dictionaries.PUNISHMENT_EMOJI[5]
                                + _(
                                    chat_settings.language,
                                    dictionaries.PUNISHMENT_STRING[5],
                                ),
                                callback_data="info punishments selectvalue5",
                            ),
                        ]
                    )

                    keyboard.append(
                        [
                            pyrogram.types.InlineKeyboardButton(
                                text=dictionaries.PUNISHMENT_EMOJI[6]
                                + _(
                                    chat_settings.language,
                                    dictionaries.PUNISHMENT_STRING[6],
                                ),
                                callback_data="info punishments selectvalue6",
                            ),
                            pyrogram.types.InlineKeyboardButton(
                                text=dictionaries.PUNISHMENT_EMOJI[7]
                                + _(
                                    chat_settings.language,
                                    dictionaries.PUNISHMENT_STRING[7],
                                ),
                                callback_data="info punishments selectvalue7",
                            ),
                        ]
                    )
                elif (
                    selected_setting == "max_temp_restrict"
                    or selected_setting == "max_temp_ban"
                ):
                    keyboard = BuildTempPunishmentMenu(
                        chat_settings=chat_settings,
                        max_temp_punishment_time=int(
                            getattr(chat_settings, selected_setting)
                        ),
                        current_keyboard=f"info {selected_setting}",
                    )
            else:
                # user
                pass
    footer_buttons = list()
    if target > 0 and chat_id < 0:
        # user in chat
        footer_buttons.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "user")
                    + f" {pyrogram.emoji.INFORMATION}",
                    callback_data=f"maininfo {target}",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "chat")
                    + f" {pyrogram.emoji.INFORMATION}",
                    callback_data=f"maininfo {chat_id}",
                ),
            ]
        )

    return BuildKeyboard(
        main_buttons=keyboard,
        header_buttons=header_buttons,
        footer_buttons=footer_buttons,
    )


def BuildTagKeyboard(
    chat: pyrogram.types.Chat,
    message_id: int,
    chat_settings: db_management.ChatSettings,
    is_member: bool = False,
) -> list:
    keyboard = list()
    if chat.type == "supergroup":
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, "link_to_message"),
                    url="t.me/"
                    + (chat.username if chat.username else f"c/{str(chat.id)[4:]}")
                    + f"/{message_id}",
                )
            ]
        )
    if (
        (chat_settings.is_link_public == 1 and is_member)
        or chat_settings.is_link_public == 2
        or chat.username
    ):
        link_to_chat = (
            f"t.me/{chat.username}"
            if chat.username
            else (chat_settings.link if chat_settings.link else None)
        )
        if link_to_chat:
            keyboard.append(
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=_(chat_settings.language, "link_to_chat"),
                        url=link_to_chat,
                    )
                ]
            )

    return BuildKeyboard(main_buttons=keyboard)


def BuildHelpMenu(
    user_settings: db_management.UserSettings,
    page: int = 0,
    selected_setting: str = None,
) -> list:
    if not selected_setting:
        header_buttons = [
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(user_settings.language, "mainhelp").upper(),
                    callback_data=f"uselessmainhelp {page}",
                )
            ]
        ]
        rank = utils.GetRank(user_id=user_settings.user_id)
        user_viewable_plugins = [
            p.name
            for p in db_management.Plugins.select()
            .where(db_management.Plugins.is_enabled)
            .order_by(peewee.fn.LOWER(db_management.Plugins.name))
            if p.name in dictionaries.HELP_DICTIONARY
            and dictionaries.HELP_DICTIONARY[p.name][0].lower()
            in dictionaries.RANK_STRING
            and rank
            >= dictionaries.RANK_STRING[dictionaries.HELP_DICTIONARY[p.name][0].lower()]
        ]
        max_columns = 2
        page = AdjustPage(
            page=page,
            max_n=len(user_viewable_plugins),
            max_items_page=utils.config["max_items_keyboard"],
        )

        keyboard = [list()]
        for i, plugin_name in enumerate(sorted(user_viewable_plugins)):
            if i >= page * utils.config["max_items_keyboard"]:
                if len(keyboard[-1]) >= max_columns:
                    # max_columns buttons per line, then add another row
                    keyboard.append(list())
                keyboard[-1].append(
                    pyrogram.types.InlineKeyboardButton(
                        text=_(user_settings.language, f"{plugin_name}"),
                        callback_data=f"mainhelp {plugin_name}",
                    )
                )
                if (
                    sum([len(row) for row in keyboard])
                    >= utils.config["max_items_keyboard"]
                ):
                    break

        footer_buttons = BuildPager(
            base_callback_data="mainhelp",
            page=page,
            n_items=len(user_viewable_plugins),
            max_items_keyboard=utils.config["max_items_keyboard"],
        )
        footer_buttons.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(user_settings.language, "back_to_main_menu"),
                    callback_data="start",
                )
            ]
        )

        return BuildKeyboard(
            main_buttons=keyboard,
            header_buttons=header_buttons,
            footer_buttons=footer_buttons,
        )
    else:
        keyboard = [
            [
                pyrogram.types.InlineKeyboardButton(
                    text=_(user_settings.language, "back_to_help_menu"),
                    callback_data="mainhelp",
                )
            ]
        ]

        return BuildKeyboard(main_buttons=keyboard)


def BuildBotPluginsMenu(
    user_settings: db_management.UserSettings, page: int = 0
) -> list:
    header_buttons = [
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(user_settings.language, "botplugins").upper(),
                callback_data=f"uselessbotplugins {page}",
            )
        ]
    ]

    keyboard = list()
    query: peewee.ModelSelect = db_management.Plugins.select().order_by(
        peewee.fn.LOWER(db_management.Plugins.name)
    )
    page = AdjustPage(
        page=page, max_n=len(query), max_items_page=utils.config["max_items_keyboard"],
    )
    begin = page * utils.config["max_items_keyboard"]
    end = min(len(query), (page + 1) * utils.config["max_items_keyboard"])

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(user_settings.language, "plugin_name"),
                callback_data="(i)botplugins plugin_name",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(user_settings.language, "is_enabled"),
                callback_data="(i)botplugins is_enabled",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(user_settings.language, "is_optional"),
                callback_data="(i)botplugins is_optional",
            ),
        ]
    )
    for i in range(begin, end):
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=query[i].name, callback_data=f"(i)botplugins {query[i].name}",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=dictionaries.YES_NO_EMOJI[query[i].is_enabled]
                    if query[i].is_optional
                    else dictionaries.YES_NO_EMOJI[1],
                    callback_data=f"botplugins is_enabled {query[i].name}",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=dictionaries.YES_NO_EMOJI[query[i].is_optional],
                    callback_data=f"botplugins is_optional {query[i].name}",
                ),
            ]
        )

    footer_buttons = BuildPager(
        base_callback_data="botplugins",
        page=page,
        n_items=len(query),
        max_items_keyboard=utils.config["max_items_keyboard"],
    )

    return BuildKeyboard(
        main_buttons=keyboard,
        header_buttons=header_buttons,
        footer_buttons=footer_buttons,
    )


def BuildChatPluginsMenu(
    chat_settings: db_management.ChatSettings, page: int = 0
) -> list:
    header_buttons = [
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "chatplugins").upper(),
                callback_data=f"uselesschatplugins {chat_settings.chat_id} {page}",
            )
        ]
    ]

    keyboard = list()
    query: peewee.ModelSelect = (
        chat_settings.plugins.select()
        .join(
            db_management.Plugins,
            on=(db_management.RChatPlugin.plugin == db_management.Plugins.name),
        )
        .where((db_management.Plugins.is_enabled) & (db_management.Plugins.is_optional))
        .order_by(peewee.fn.LOWER(db_management.Plugins.name))
    )
    page = AdjustPage(
        page=page, max_n=len(query), max_items_page=utils.config["max_items_keyboard"],
    )
    begin = page * utils.config["max_items_keyboard"]
    end = min(len(query), (page + 1) * utils.config["max_items_keyboard"])

    keyboard.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "plugin_name"),
                callback_data="(i)botplugins plugin_name",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "is_enabled_on_chat"),
                callback_data="(i)botplugins is_enabled_on_chat",
            ),
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "min_rank"),
                callback_data="(i)botplugins min_rank",
            ),
        ]
    )
    for i in range(begin, end):
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=query[i].plugin,
                    callback_data=f"(i)chatplugins {query[i].plugin}",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=dictionaries.YES_NO_EMOJI[query[i].is_enabled_on_chat],
                    callback_data=f"chatplugins is_enabled_on_chat {query[i].plugin}",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=f"{dictionaries.RANK_STRING[query[i].min_rank]}^",
                    callback_data=f"chatplugins min_rank {query[i].plugin}",
                ),
            ]
        )
    footer_buttons = BuildPager(
        base_callback_data="chatplugins",
        page=page,
        n_items=len(query),
        max_items_keyboard=utils.config["max_items_keyboard"],
    )
    footer_buttons.append(
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "chat")
                + f" {pyrogram.emoji.INFORMATION}",
                callback_data=f"maininfo {chat_settings.chat_id}",
            )
        ]
    )

    return BuildKeyboard(
        main_buttons=keyboard,
        header_buttons=header_buttons,
        footer_buttons=footer_buttons,
    )


def BuildGroupsMenu(
    chat_settings: typing.Union[db_management.ChatSettings, db_management.UserSettings],
    page: int = 0,
) -> list:
    header_buttons = [
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "public_groups").upper(),
                callback_data=f"uselessgroups {page}",
            )
        ]
    ]

    keyboard = list()
    query: peewee.ModelSelect = (
        db_management.ChatSettings.select()
        .join(
            db_management.Chats,
            on=(db_management.ChatSettings.chat == db_management.Chats.id),
        )
        .where(
            (db_management.ChatSettings.is_link_public == 2)
            | (db_management.Chats.username)
        )
        .order_by(peewee.fn.LOWER(db_management.Chats.title))
    )
    page = AdjustPage(
        page=page, max_n=len(query), max_items_page=utils.config["max_items_keyboard"],
    )
    begin = page * utils.config["max_items_keyboard"]
    end = min(len(query), (page + 1) * utils.config["max_items_keyboard"])
    for i in range(begin, end):
        current_chat = query[i].chat
        if current_chat.username or query[i].link:
            keyboard.append(
                [
                    pyrogram.types.InlineKeyboardButton(
                        text=current_chat.title,
                        url=f"t.me/{current_chat.username}"
                        if current_chat.username
                        else query[i].link,
                    ),
                ]
            )
    footer_buttons = BuildPager(
        base_callback_data="groups",
        page=page,
        n_items=len(query),
        max_items_keyboard=utils.config["max_items_keyboard"],
    )

    return BuildKeyboard(
        main_buttons=keyboard,
        header_buttons=header_buttons,
        footer_buttons=footer_buttons,
    )


def BuildLogMenu(chat_settings: db_management.ChatSettings, page: int = 0) -> list:
    header_buttons = [
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, "logs").upper(),
                callback_data=f"uselesslogs {chat_settings.chat_id} {page}",
            )
        ]
    ]
    query: peewee.ModelSelect = (
        db_management.Logs.select()
        .where(db_management.Logs.chat_id == chat_settings.chat_id)
        .order_by(db_management.Logs.timestamp.desc())
    )
    page = AdjustPage(
        page=page, max_n=len(query), max_items_page=utils.config["max_items_keyboard"],
    )
    footer_buttons = BuildPager(
        base_callback_data="logs",
        page=page,
        n_items=len(query),
        max_items_keyboard=utils.config["max_items_keyboard"],
    )

    return BuildKeyboard(header_buttons=header_buttons, footer_buttons=footer_buttons)


def BuildActionOnAddedUsersList(
    chat_settings: db_management.ChatSettings,
    action: str,
    new_chat_members: typing.Union[
        typing.List[pyrogram.types.User], peewee.ModelSelect
    ],
) -> list:
    header_buttons = [
        [
            pyrogram.types.InlineKeyboardButton(
                text=_(chat_settings.language, f"{action}_all").upper(),
                callback_data=f"{action}_all",
            )
        ]
    ]

    keyboard = list()
    for user in new_chat_members:
        keyboard.append(
            [
                pyrogram.types.InlineKeyboardButton(
                    text=f"{user.id} - {user.first_name}",
                    callback_data=f"useless{action} {user.id}",
                ),
                pyrogram.types.InlineKeyboardButton(
                    text=_(chat_settings.language, f"{action}"),
                    callback_data=f"{action} {user.id}",
                ),
            ]
        )

    return BuildKeyboard(main_buttons=keyboard, header_buttons=header_buttons)
