import datetime
import json
import logging
import os
import traceback
import typing

import peewee
import pyrogram
from playhouse.sqliteq import SqliteQueueDatabase

DB = None
local_config = None
with open(file="config.json", encoding="utf-8") as f:
    local_config = json.load(fp=f)

if not local_config:
    logging.log(logging.FATAL, "Missing config.json")
    exit()

DB = SqliteQueueDatabase(
    database=local_config["database"],
    pragmas=[
        ("foreign_keys", 1),
        ("journal_mode", "wal"),
        ("ignore_check_constraints", 0),
        ("synchronous", "normal"),
    ],
)


class Users(peewee.Model):
    id = peewee.IntegerField(
        primary_key=True, constraints=[peewee.Check(constraint="id > 0")]
    )

    first_name = peewee.CharField(null=False)
    last_name = peewee.CharField(default=None, null=True)
    username = peewee.CharField(default=None, null=True)
    is_bot = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="is_bot BETWEEN 0 AND 1")],
    )
    timestamp = peewee.DateTimeField(default=datetime.datetime.utcnow, null=False)

    class Meta:
        database = DB


class UserSettings(peewee.Model):
    user = peewee.ForeignKeyField(
        primary_key=True,
        model=Users,
        backref="settings",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )
    # 2 CHARACTERS
    language = peewee.CharField(default="en", null=False)
    shitstorm_counter = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="shitstorm_counter >= 0")],
    )
    # date of global ban
    global_ban_date = peewee.DateField(default=datetime.date.min, null=False)
    # expiration date of global ban
    global_ban_expiration = peewee.DateField(default=datetime.date.min, null=False)
    global_ban_counter = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="global_ban_counter >= 0")],
    )
    private_flood_counter = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="private_flood_counter >= 0")],
    )
    # datetime of block in private with bot
    block_datetime = peewee.DateTimeField(default=datetime.datetime.min, null=False)
    # expiration date of block in private with bot
    block_expiration = peewee.DateTimeField(default=datetime.datetime.min, null=False)
    block_counter = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="block_counter >= 0")],
    )
    # how the user is called by others, used to alert the user < 128 CHARACTERS
    nickname = peewee.CharField(default=None, null=True)
    # POSSIBLE VALUES   #
    # 0 = No            #
    # 1 = Only my groups#
    # 2 = Yes           #
    # does the user want to be alerted when tagged (username/nickname)?
    wants_tag_alerts = peewee.IntegerField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="wants_tag_alerts BETWEEN 0 AND 2")],
    )
    # did the user start the bot?
    has_blocked_bot = peewee.BooleanField(
        default=True,
        null=False,
        constraints=[peewee.Check(constraint="has_blocked_bot BETWEEN 0 AND 1")],
    )
    # can the user use advanced keyboards?
    advanced_mode = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="advanced_mode BETWEEN 0 AND 1")],
    )

    class Meta:
        database = DB


class Networks(peewee.Model):
    link = peewee.CharField(primary_key=True)

    name = peewee.CharField(unique=True, null=False)
    # who owns the network
    owner = peewee.ForeignKeyField(
        model=Users, backref="networks_owned", on_update="CASCADE", null=False
    )
    # is the network public?
    is_public = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="is_public BETWEEN 0 AND 1")],
    )

    class Meta:
        database = DB


class Chats(peewee.Model):
    id = peewee.IntegerField(
        primary_key=True, constraints=[peewee.Check(constraint="id < 0")]
    )

    title = peewee.CharField(null=False)
    username = peewee.CharField(default=None, null=True)
    is_channel = peewee.BooleanField(null=False)
    timestamp = peewee.DateTimeField(default=datetime.datetime.utcnow, null=False)

    class Meta:
        database = DB


class ChatSettings(peewee.Model):
    chat = peewee.ForeignKeyField(
        primary_key=True,
        model=Chats,
        backref="settings",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )
    # who owns the chat
    owner = peewee.ForeignKeyField(
        model=Users, backref="chats_owned", on_update="CASCADE", null=True
    )
    # 2 CHARACTERS
    language = peewee.CharField(default="en", null=False)
    # link of the chat < 512 CHARACTERS
    link = peewee.CharField(default=None, null=True)
    # number of members necessary before sending welcome message BETWEEN 0 AND 10
    welcome_members = peewee.IntegerField(default=0, null=False)
    # is bot enabled on chat?
    is_bot_on = peewee.BooleanField(
        default=True,
        null=False,
        constraints=[peewee.Check(constraint="is_bot_on BETWEEN 0 AND 1")],
    )
    # should bot stay in this chat?
    is_banned = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="is_banned BETWEEN 0 AND 1")],
    )
    # are settings locked by the owner?
    are_locked = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="are_locked BETWEEN 0 AND 1")],
    )
    # where to send logs
    log_channel = peewee.IntegerField(default=None, null=True)
    # should inform user about tags (with username and nickname if set) in chat?
    has_pin_markers = peewee.BooleanField(
        default=True,
        null=False,
        constraints=[peewee.Check(constraint="has_pin_markers BETWEEN 0 AND 1")],
    )
    # POSSIBLE VALUES               #
    # 0 = No                        #
    # 1 = Only my groups/in group   #
    # 2 = Yes                       #
    # should inform user about tags (with username and nickname if set) in chat?
    has_tag_alerts = peewee.IntegerField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="has_tag_alerts BETWEEN 0 AND 2")],
    )
    # can users access the link freely?
    is_link_public = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="is_link_public BETWEEN 0 AND 2")],
    )

    # maximum number of messages per user in X seconds BETWEEN 3 AND 10
    max_flood = peewee.IntegerField(default=5, null=False)
    # time interval in which messages increment flood counter BETWEEN 3 AND 10
    max_flood_time = peewee.IntegerField(default=8, null=False)
    # maximum number of warns a user can receive BETWEEN 1 AND 10
    max_warns = peewee.IntegerField(
        default=3, null=False, constraints=[peewee.Check(constraint="max_warns > 0")]
    )
    # measured in seconds, 24h default BETWEEN 30 AND 31622400 but it's better to take some seconds so BETWEEN X AND Y
    max_temp_restrict = peewee.IntegerField(
        default=local_config["default_temp_restrict"], null=False
    )
    # measured in seconds, 24h default BETWEEN 30 AND 31622400 but it's better to take some seconds so BETWEEN X AND Y
    max_temp_ban = peewee.IntegerField(
        default=local_config["default_temp_ban"], null=False
    )
    # how many users can be added by someone at the same time BETWEEN 1 AND 20
    max_invites = peewee.IntegerField(
        default=5, null=False, constraints=[peewee.Check(constraint="max_invites >= 1")]
    )
    # region locks and mutes
    # POSSIBLE VALUES   #
    # 0 = allowed       #
    # 1 = delete        #
    # 2 = warn          #
    # 3 = kick          #
    # 4 = temprestrict  #
    # 5 = restrict      #
    # 6 = tempban       #
    # 7 = ban           #
    # should inform chat about automatic actions? 0 = no
    group_notices = peewee.IntegerField(
        default=2,
        null=False,
        constraints=[
            peewee.Check(constraint="group_notices == 0 OR group_notices >= 2")
        ],
    )
    # why times BETWEEN 0 AND 95?
    # 2 variables => hours and minutes
    # hours have 23 alternatives => 00, 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23
    # minutes have 4 alternatives => 00, 15, 30, 45 (alternatives 0, 1, 2, 3)
    # hours * 4 + minutes (alternatives) < 96
    # to retrieve the exact time the formula is: value / 4 = hour.minutes
    # where minutes can be .00(0)(0), .25(15)(1), .50(30)(2), .75(45)(3)
    # is the night mode enabled?
    night_mode_punishment = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="night_mode_punishment >= 0")],
    )
    # what time should the night mode start? BETWEEN 0 AND 95
    night_mode_from = peewee.IntegerField(
        default=90,  # 22:30
        null=False,
        constraints=[peewee.Check(constraint="night_mode_from BETWEEN 0 AND 95")],
    )
    # what time should the night mode stop? BETWEEN 0 AND 95
    night_mode_to = peewee.IntegerField(
        default=28,  # 07:00
        null=False,
        constraints=[peewee.Check(constraint="night_mode_to BETWEEN 0 AND 95")],
    )
    # why times BETWEEN 0 AND 95?
    # 2 variables => hours and minutes
    # hours have 23 alternatives => 00, 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23
    # minutes have 4 alternatives => 00, 15, 30, 45 (alternatives 0, 1, 2, 3)
    # hours * 4 + minutes (alternatives) < 96
    # to retrieve the exact time the formula is: value / 4 = hour.minutes_alternatives
    # where minutes can be .00(0)(0), .25(15)(1), .50(30)(2), .75(45)(3)
    # is the slow mode enabled?
    slow_mode_value = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="slow_mode_value >= 0")],
    )
    # what time should the slow mode start? BETWEEN 0 AND 95
    slow_mode_from = peewee.IntegerField(
        default=90,  # 22:30
        null=False,
        constraints=[peewee.Check(constraint="slow_mode_from BETWEEN 0 AND 95")],
    )
    # what time should the slow mode stop? BETWEEN 0 AND 95
    slow_mode_to = peewee.IntegerField(
        default=28,  # 07:00
        null=False,
        constraints=[peewee.Check(constraint="slow_mode_to BETWEEN 0 AND 95")],
    )
    # when max_warns is reached
    max_warns_punishment = peewee.IntegerField(
        default=7,
        null=False,
        constraints=[
            peewee.Check(
                constraint="max_warns_punishment == 0 OR max_warns_punishment >= 4"
            )
        ],
    )
    # should show temporary punishments as possible punishments?
    allow_temporary_punishments = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[
            peewee.Check(constraint="allow_temporary_punishments BETWEEN 0 AND 1")
        ],
    )
    # should flood_process multiple audios/documents/photos/videos/ sent as an album?
    allow_media_group = peewee.BooleanField(
        default=True,
        null=False,
        constraints=[peewee.Check(constraint="allow_media_group BETWEEN 0 AND 1")],
    )
    allow_service_messages = peewee.BooleanField(
        default=True,
        null=False,
        constraints=[peewee.Check(constraint="allow_service_messages BETWEEN 0 AND 1")],
    )
    # MUTES
    # mute everything in the chat
    anti_everything = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="anti_everything >= 0")],
    )
    # gifs
    anti_animation = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="anti_animation >= 0")],
    )
    anti_audio = peewee.IntegerField(
        default=0, null=False, constraints=[peewee.Check(constraint="anti_audio >= 0")]
    )
    anti_contact = peewee.IntegerField(
        default=1,
        null=False,
        constraints=[peewee.Check(constraint="anti_contact >= 0")],
    )
    # generic file
    anti_document = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="anti_document >= 0")],
    )
    anti_game = peewee.IntegerField(
        default=0, null=False, constraints=[peewee.Check(constraint="anti_game >= 0")]
    )
    anti_location = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="anti_location >= 0")],
    )
    anti_photo = peewee.IntegerField(
        default=0, null=False, constraints=[peewee.Check(constraint="anti_photo >= 0")]
    )
    anti_sticker = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="anti_sticker >= 0")],
    )
    anti_text = peewee.IntegerField(
        default=0, null=False, constraints=[peewee.Check(constraint="anti_text >= 0")]
    )
    # type of location
    anti_venue = peewee.IntegerField(
        default=0, null=False, constraints=[peewee.Check(constraint="anti_venue >= 0")]
    )
    anti_video = peewee.IntegerField(
        default=0, null=False, constraints=[peewee.Check(constraint="anti_video >= 0")]
    )
    anti_video_note = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="anti_video_note >= 0")],
    )
    anti_voice = peewee.IntegerField(
        default=0, null=False, constraints=[peewee.Check(constraint="anti_voice >= 0")]
    )
    # LOCKS
    # add users/bots
    add_punishment = peewee.IntegerField(
        default=5,
        null=False,
        constraints=[
            peewee.Check(constraint="add_punishment == 0 OR add_punishment >= 4")
        ],
    )
    # arabic characters
    arabic_punishment = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="arabic_punishment >= 0")],
    )
    # punishment for bots in chat
    bot_punishment = peewee.IntegerField(
        default=3,
        null=False,
        constraints=[
            peewee.Check(constraint="bot_punishment == 0 OR bot_punishment >= 3")
        ],
    )
    # censorship on words/medias
    censorships_punishment = peewee.IntegerField(
        default=1,
        null=False,
        constraints=[peewee.Check(constraint="censorships_punishment >= 0")],
    )
    # more than X messages in Y seconds
    flood_punishment = peewee.IntegerField(
        default=2,
        null=False,
        constraints=[
            peewee.Check(constraint="flood_punishment == 0 OR flood_punishment >= 2")
        ],
    )
    # forwarded messages from channels
    forward_punishment = peewee.IntegerField(
        default=2,
        null=False,
        constraints=[peewee.Check(constraint="forward_punishment >= 0")],
    )
    globally_banned_punishment = peewee.IntegerField(
        default=5,
        null=False,
        constraints=[
            peewee.Check(
                constraint="globally_banned_punishment == 0 OR globally_banned_punishment >= 4"
            )
        ],
    )
    # people who join the chat
    join_punishment = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[
            peewee.Check(constraint="join_punishment == 0 OR join_punishment >= 4")
        ],
    )
    # links to chats and channels
    link_spam_punishment = peewee.IntegerField(
        default=2,
        null=False,
        constraints=[peewee.Check(constraint="link_spam_punishment >= 0")],
    )
    # RightToLeft characters
    rtl_punishment = peewee.IntegerField(
        default=1,
        null=False,
        constraints=[peewee.Check(constraint="rtl_punishment >= 0")],
    )
    # lots of equal messages
    shitstorm_punishment = peewee.IntegerField(
        default=7,
        null=False,
        constraints=[
            peewee.Check(
                constraint="shitstorm_punishment == 0 OR shitstorm_punishment >= 4"
            )
        ],
    )
    # messages longer than 2048 OR messages/names with more than 40 non-printable characters
    text_spam_punishment = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="text_spam_punishment >= 0")],
    )
    # endregion
    # at 5 messages that the bot could not write it leaves the chat
    forbidden_writing_counter = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="forbidden_writing_counter >= 0")],
    )

    class Meta:
        database = DB


class ChatPreActionList(peewee.Model):
    chat = peewee.ForeignKeyField(
        model=ChatSettings,
        backref="preactioned_users",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )
    user_id = peewee.IntegerField(
        null=False, constraints=[peewee.Check(constraint="user_id > 0")]
    )

    action = peewee.CharField(null=False)

    class Meta:
        database = DB
        primary_key = peewee.CompositeKey("chat", "user_id")


class ChatWhitelistedChats(peewee.Model):
    chat = peewee.ForeignKeyField(
        model=ChatSettings,
        backref="whitelisted_chats",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )
    # whitelisted chat id, can be positive (resolved by link, will be addressed both in -id and -100id) or negative (-id or -100id)
    whitelisted_chat = peewee.IntegerField(null=False)

    class Meta:
        database = DB
        primary_key = peewee.CompositeKey("chat", "whitelisted_chat")


class ChatCensorships(peewee.Model):
    chat = peewee.ForeignKeyField(
        model=ChatSettings,
        backref="censorships",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )
    # thing to be censored < 512 CHARACTERS
    value = peewee.CharField(null=False)

    # is thing a regex?
    is_regex = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="is_regex BETWEEN 0 AND 1")],
    )
    # is thing a media?
    is_media = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="is_media BETWEEN 0 AND 1")],
    )
    # if value is media then the original message is necessary in order to fetch again the file_ref once expired
    # DEPRECATED SINCE PYROGRAM 1.1
    original_chat_id = peewee.IntegerField(default=None, null=True)
    original_message_id = peewee.IntegerField(default=None, null=True)

    class Meta:
        database = DB
        primary_key = peewee.CompositeKey("chat", "value")


class ChatExtras(peewee.Model):
    chat = peewee.ForeignKeyField(
        model=ChatSettings,
        backref="extras",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )
    # keyword found in text < 50 CHARACTERS
    key = peewee.CharField(null=False)
    # WELCOME_BUTTONS is composed in the following way
    # text1 | link1 && text2 | link2
    # text3 | link3
    # | separates button_text from link
    # && separates buttons
    # \n separates rows
    # thing with which the bot has to reply < 2048 CHARACTERS, if media then ###file_id$caption
    value = peewee.CharField(null=False)
    # is it goodbye/rules/welcome/welcome_buttons?
    is_group_data = peewee.BooleanField(null=False, default=False)

    # is key a regex?
    is_regex = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="is_regex BETWEEN 0 AND 1")],
    )
    # is value a media?
    is_media = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="is_media BETWEEN 0 AND 1")],
    )
    # if value is media then the original message is necessary in order to fetch again the file_ref once expired
    # DEPRECATED SINCE PYROGRAM 1.1
    original_chat_id = peewee.IntegerField(default=None, null=True)
    original_message_id = peewee.IntegerField(default=None, null=True)

    class Meta:
        database = DB
        primary_key = peewee.CompositeKey("chat", "key", "value", "is_group_data")


class ChatAlternatives(peewee.Model):
    chat = peewee.ForeignKeyField(
        model=ChatSettings,
        backref="alternative_commands",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )
    # original command that is used by bot < 50 CHARACTERS
    original = peewee.CharField(
        null=False, constraints=[peewee.Check(constraint="original != ''")]
    )
    # alternative command < 512 CHARACTERS
    alternative = peewee.CharField(
        null=False, constraints=[peewee.Check(constraint="alternative != ''")]
    )

    # is thing a media?
    is_media = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="is_media BETWEEN 0 AND 1")],
    )
    # if value is media then the original message is necessary in order to fetch again the file_ref once expired
    # DEPRECATED SINCE PYROGRAM 1.1
    original_chat_id = peewee.IntegerField(default=None, null=True)
    original_message_id = peewee.IntegerField(default=None, null=True)

    class Meta:
        database = DB
        primary_key = peewee.CompositeKey("chat", "original", "alternative")


class RUserChat(peewee.Model):
    user = peewee.ForeignKeyField(
        model=Users,
        backref="chats",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )
    chat = peewee.ForeignKeyField(
        model=Chats,
        backref="users",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )

    # rank of the user
    # POSSIBLE VALUES       #
    # 0 = normal            #
    # 1 = privileged        #
    # 2 = junior moderator  #
    # 3 = senior moderator  #
    # 4 = owner             #
    rank = peewee.IntegerField(
        default=0, null=False, constraints=[peewee.Check(constraint="rank >= 0")]
    )
    # is member of group? (used for commands requiring a quite accurate member's list, not a reliable indicator on the long run)
    is_member = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="is_member BETWEEN 0 AND 1")],
    )
    # is user administrator on telegram?
    is_admin = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="is_admin BETWEEN 0 AND 1")],
    )
    # is user anonymous on telegram?
    is_anonymous = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="is_anonymous BETWEEN 0 AND 1")],
    )
    # TELEGRAM PERMISSIONS
    # Applicable to administrators only. True, if you are allowed to edit administrator privileges of the user.
    can_be_edited = peewee.BooleanField(
        default=False,
        constraints=[peewee.Check(constraint="can_be_edited BETWEEN 0 AND 1")],
    )
    # Applicable to default chat permissions in private groups and administrators in public groups only. True, if the chat title, photo and other settings can be changed.
    can_change_info = peewee.BooleanField(
        default=False,
        constraints=[peewee.Check(constraint="can_change_info BETWEEN 0 AND 1")],
    )
    # Applicable to administrators only. True, if the administrator can delete messages of other users.
    can_delete_messages = peewee.BooleanField(
        default=False,
        constraints=[peewee.Check(constraint="can_delete_messages BETWEEN 0 AND 1")],
    )
    # Applicable to default chat permissions and administrators only. True, if new users can be invited to the chat.
    can_invite_users = peewee.BooleanField(
        default=False,
        constraints=[peewee.Check(constraint="can_invite_users BETWEEN 0 AND 1")],
    )
    # Applicable to administrators only. True, if the administrator can access the chat event log, chat statistics, message statistics in channels, see channel members, see anonymous administrators in supergroups and ignore slow mode. Implied by any other administrator privilege.
    can_manage_chat = peewee.BooleanField(
        default=False,
        constraints=[peewee.Check(constraint="can_manage_chat BETWEEN 0 AND 1")],
    )
    # Applicable to administrators only. True, if the administrator can manage video chats (also called group calls).
    can_manage_video_chats = peewee.BooleanField(
        default=False,
        constraints=[peewee.Check(constraint="can_manage_video_chats BETWEEN 0 AND 1")],
    )
    # Applicable to default chat permissions in private groups and administrators in public groups only. True, if messages can be pinned, supergroups only.
    can_pin_messages = peewee.BooleanField(
        default=False,
        constraints=[peewee.Check(constraint="can_pin_messages BETWEEN 0 AND 1")],
    )
    # Applicable to administrators only. True, if the administrator can add new administrators with a subset of his own privileges or demote administrators that he has promoted, directly or indirectly (promoted by administrators that were appointed by the user).
    can_promote_members = peewee.BooleanField(
        default=False,
        constraints=[peewee.Check(constraint="can_promote_members BETWEEN 0 AND 1")],
    )
    # Applicable to administrators only. True, if the administrator can restrict, ban or unban chat members.
    can_restrict_members = peewee.BooleanField(
        default=False,
        constraints=[peewee.Check(constraint="can_restrict_members BETWEEN 0 AND 1")],
    )

    # is user safe from locks/mutes checks in the chat?
    is_whitelisted = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="is_whitelisted BETWEEN 0 AND 1")],
    )
    # is user safe from global ban check in the chat?
    is_global_ban_whitelisted = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[
            peewee.Check(constraint="is_global_ban_whitelisted BETWEEN 0 AND 1")
        ],
    )
    # user's number of warns in chat >= 0
    warns = peewee.IntegerField(default=0, null=False)
    # how many messages did the user write in the chat?
    message_counter = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="message_counter >= 0")],
    )
    timestamp = peewee.DateTimeField(default=datetime.datetime.utcnow, null=False)

    class Meta:
        database = DB
        primary_key = peewee.CompositeKey("user", "chat")


class RFlamedUserChat(peewee.Model):
    flamed_user = peewee.ForeignKeyField(
        model=Users,
        backref="flamed_in",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )
    chat = peewee.ForeignKeyField(
        model=Chats,
        backref="flamed_users",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )

    counter = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="counter >= 0")],
    )
    max_flame = peewee.IntegerField(
        default=10,
        null=False,
        constraints=[peewee.Check(constraint="max_flame >= 1")],
    )

    class Meta:
        database = DB
        primary_key = peewee.CompositeKey("flamed_user", "chat")


class RNetworkChat(peewee.Model):
    network = peewee.ForeignKeyField(
        model=Networks,
        backref="chats",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )
    chat = peewee.ForeignKeyField(
        model=ChatSettings,
        backref="network",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )
    # are chat settings locked to network's ones?
    are_settings_locked = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="are_settings_locked BETWEEN 0 AND 1")],
    )
    # are chat plugins locked to network's ones?
    are_plugins_locked = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="are_plugins_locked BETWEEN 0 AND 1")],
    )

    class Meta:
        database = DB
        primary_key = peewee.CompositeKey("network", "chat")


class Plugins(peewee.Model):
    name = peewee.CharField(primary_key=True)

    # is plugin enabled globally?
    is_enabled = peewee.BooleanField(
        default=True,
        null=False,
        constraints=[peewee.Check(constraint="is_enabled BETWEEN 0 AND 1")],
    )
    # is plugin optional?
    is_optional = peewee.BooleanField(
        default=True,
        null=False,
        constraints=[peewee.Check(constraint="is_optional BETWEEN 0 AND 1")],
    )

    class Meta:
        database = DB


class RChatPlugin(peewee.Model):
    chat = peewee.ForeignKeyField(
        model=ChatSettings,
        backref="plugins",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )
    plugin = peewee.ForeignKeyField(
        model=Plugins, on_delete="CASCADE", on_update="CASCADE", null=False
    )

    # is plugin just for rank^?
    min_rank = peewee.IntegerField(
        default=0, null=False, constraints=[peewee.Check(constraint="min_rank >= 0")]
    )
    # is plugin enabled on chat?
    is_enabled_on_chat = peewee.BooleanField(
        default=True,
        null=False,
        constraints=[peewee.Check(constraint="is_enabled_on_chat BETWEEN 0 AND 1")],
    )

    class Meta:
        database = DB
        primary_key = peewee.CompositeKey("chat", "plugin")


class RuletaUsers(peewee.Model):
    user = peewee.ForeignKeyField(
        primary_key=True,
        model=Users,
        backref="ruleta_data",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )

    score = peewee.IntegerField(default=0, null=False)
    attempts = peewee.IntegerField(
        default=0, null=False, constraints=[peewee.Check(constraint="attempts >= 0")]
    )
    deaths = peewee.IntegerField(
        default=0, null=False, constraints=[peewee.Check(constraint="deaths >= 0")]
    )
    duels = peewee.IntegerField(
        default=0, null=False, constraints=[peewee.Check(constraint="duels >= 0")]
    )
    victories = peewee.IntegerField(
        default=0, null=False, constraints=[peewee.Check(constraint="victories >= 0")]
    )
    defeats = peewee.IntegerField(
        default=0, null=False, constraints=[peewee.Check(constraint="defeats >= 0")]
    )
    surrenders = peewee.IntegerField(
        default=0, null=False, constraints=[peewee.Check(constraint="surrenders >= 0")]
    )
    streak = peewee.IntegerField(
        default=0, null=False, constraints=[peewee.Check(constraint="streak >= 0")]
    )
    longest_streak = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="longest_streak >= 0")],
    )
    # is the user clickable in the leaderboards?
    is_clickable = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="is_clickable BETWEEN 0 AND 1")],
    )
    # user alternative name?
    alias = peewee.CharField(default=None, null=True)

    class Meta:
        database = DB


class RuletaChats(peewee.Model):
    chat = peewee.ForeignKeyField(
        primary_key=True,
        model=ChatSettings,
        backref="ruleta_settings",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )

    # normal cylinder BETWEEN 5 AND 10
    cylinder = peewee.IntegerField(default=6, null=False)
    # duel cylinder BETWEEN 5 AND 10
    duel_cylinder = peewee.IntegerField(default=6, null=False)
    # normal cylinder's bullets BETWEEN 1 AND cylinder
    bullets = peewee.IntegerField(
        default=1,
        null=False,
        constraints=[peewee.Check(constraint="bullets BETWEEN 1 AND cylinder")],
    )
    # duel cylinder's bullets BETWEEN 1 AND duel_cylinder
    duel_bullets = peewee.IntegerField(
        default=1,
        null=False,
        constraints=[
            peewee.Check(constraint="duel_bullets BETWEEN 1 AND duel_cylinder")
        ],
    )

    class Meta:
        database = DB


class RuletaDuels(peewee.Model):
    challenger = peewee.ForeignKeyField(
        model=RuletaUsers,
        backref="challenger_of",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )
    challenged = peewee.ForeignKeyField(
        model=RuletaUsers,
        backref="challenged_by",
        on_delete="CASCADE",
        on_update="CASCADE",
        null=False,
    )

    cylinder = peewee.IntegerField(default=6, null=False)
    bullets = peewee.IntegerField(
        default=1,
        null=False,
        constraints=[peewee.Check(constraint="bullets BETWEEN 1 AND cylinder")],
    )
    rounds = peewee.IntegerField(
        default=0,
        null=False,
        constraints=[peewee.Check(constraint="rounds BETWEEN 0 AND cylinder")],
    )
    begin_date = peewee.DateTimeField(default=datetime.datetime.utcnow, null=False)
    is_accepted = peewee.BooleanField(
        default=False,
        null=False,
        constraints=[peewee.Check(constraint="is_accepted BETWEEN 0 AND 1")],
    )

    class Meta:
        database = DB
        primary_key = peewee.CompositeKey("challenger", "challenged")
        constraints = [peewee.Check(constraint="challenger_id != challenged_id")]


class ResolvedObjects(peewee.Model):
    id = peewee.IntegerField(primary_key=True, null=False)

    username = peewee.CharField(default=None, null=True)
    timestamp = peewee.DateTimeField(default=datetime.datetime.utcnow, null=False)
    type = peewee.CharField(null=False)

    class Meta:
        database = DB


class Logs(peewee.Model):
    timestamp = peewee.DateTimeField(default=datetime.datetime.utcnow, null=False)
    chat_id = peewee.IntegerField(null=False)
    executer = peewee.IntegerField(null=False)
    action = peewee.CharField(null=False)
    target = peewee.IntegerField(null=True, default=None)

    class Meta:
        database = DB


DB.create_tables(
    models=[
        Users,
        UserSettings,
        Networks,
        Chats,
        ChatSettings,
        ChatPreActionList,
        ChatWhitelistedChats,
        ChatCensorships,
        ChatExtras,
        ChatAlternatives,
        RUserChat,
        RFlamedUserChat,
        RNetworkChat,
        Plugins,
        RChatPlugin,
        RuletaUsers,
        RuletaChats,
        RuletaDuels,
        ResolvedObjects,
        Logs,
    ],
    safe=True,
)
DB.close()
DB.connect()


def LoadPluginsToDB():
    for p in os.listdir("./plugins/mandatory"):
        p = os.path.splitext(p)[0]
        if p != "__init__" and p != "__pycache__":
            if Plugins.get_or_none(name=p):
                Plugins.update(is_optional=False).where(Plugins.name == p).execute()
            else:
                Plugins.create(name=p, is_optional=False)
    for p in os.listdir("./plugins/optional"):
        p = os.path.splitext(p)[0]
        if p != "__init__" and p != "__pycache__":
            if Plugins.get_or_none(name=p):
                Plugins.update(is_optional=True).where(Plugins.name == p).execute()
            else:
                Plugins.create(name=p, is_optional=True)


def DBUser(user: typing.Union[pyrogram.types.Chat, pyrogram.types.User]):
    if Users.get_or_none(id=user.id):
        Users.update(
            first_name=user.first_name if user.first_name else "",
            last_name=user.last_name,
            username=user.username,
            is_bot=user.is_bot
            if isinstance(user, pyrogram.types.User)
            else (
                user.type == pyrogram.enums.chat_type.ChatType.BOT
                if isinstance(user, pyrogram.types.Chat)
                else False
            ),
            timestamp=datetime.datetime.utcnow(),
        ).where(Users.id == user.id).execute()
    else:
        Users.create(
            id=user.id,
            first_name=user.first_name if user.first_name else "",
            last_name=user.last_name,
            username=user.username,
            is_bot=user.is_bot
            if isinstance(user, pyrogram.types.User)
            else (
                user.type == pyrogram.enums.chat_type.ChatType.BOT
                if isinstance(user, pyrogram.types.Chat)
                else False
            ),
        )

    settings: UserSettings = UserSettings.get_or_none(user_id=user.id)
    if not settings:
        settings: UserSettings = UserSettings.create(user_id=user.id)

    ResolvedObjects.replace(
        id=user.id,
        username=user.username.lower() if user.username else None,
        timestamp=datetime.datetime.utcnow(),
        type="bot"
        if isinstance(user, pyrogram.types.User) and user.is_bot
        else (
            "bot"
            if isinstance(user, pyrogram.types.Chat)
            and user.type == pyrogram.enums.chat_type.ChatType.BOT
            else "private"
        ),
    ).execute()


def DBChat(chat: pyrogram.types.Chat) -> bool:
    created = False
    if Chats.get_or_none(id=chat.id):
        Chats.update(
            title=chat.title,
            username=chat.username,
            is_channel=chat.type == pyrogram.enums.chat_type.ChatType.CHANNEL,
            timestamp=datetime.datetime.utcnow(),
        ).where(Chats.id == chat.id).execute()
    else:
        created = True
        Chats.create(
            id=chat.id,
            title=chat.title,
            username=chat.username,
            is_channel=chat.type == pyrogram.enums.chat_type.ChatType.CHANNEL,
        )
    if (
        chat.type == pyrogram.enums.chat_type.ChatType.GROUP
        or chat.type == pyrogram.enums.chat_type.ChatType.SUPERGROUP
    ):
        DBChatSettings(chat=chat)

    ResolvedObjects.replace(
        id=chat.id,
        username=chat.username.lower() if chat.username else None,
        timestamp=datetime.datetime.utcnow(),
        type=chat.type.value,
    ).execute()
    return created


def DBChatSettings(chat: pyrogram.types.Chat):
    settings: ChatSettings = ChatSettings.get_or_none(chat_id=chat.id)
    if not settings:
        settings: ChatSettings = ChatSettings.create(chat_id=chat.id)
        ChatExtras.bulk_create(
            [
                ChatExtras(
                    chat_id=chat.id, key="goodbye", value="", is_group_data=True
                ),
                ChatExtras(chat_id=chat.id, key="rules", value="", is_group_data=True),
                ChatExtras(
                    chat_id=chat.id, key="welcome", value="", is_group_data=True
                ),
                ChatExtras(
                    chat_id=chat.id,
                    key="welcome_buttons",
                    value="",
                    is_group_data=True,
                ),
            ]
        )
        if local_config["channel"]["id"]:
            # bot's channel
            ChatWhitelistedChats.create(
                chat_id=chat.id, whitelisted_chat=local_config["channel"]["id"]
            )
        # @username
        ChatWhitelistedChats.create(chat_id=chat.id, whitelisted_chat=-1001066197625)

    query: peewee.ModelSelect = (
        Plugins.select().where(Plugins.is_optional).order_by(Plugins.name)
    )
    try:
        RChatPlugin.bulk_create(
            RChatPlugin(
                chat=chat.id,
                plugin=plugin.name,
                min_rank=1,
                is_enabled_on_chat=False,
            )
            for plugin in query
        )
    except peewee.IntegrityError:
        pass
    except Exception as ex:
        print(ex)
        traceback.print_exc()


def DBUserChat(
    user: typing.Union[pyrogram.types.Chat, pyrogram.types.User],
    chat: pyrogram.types.Chat,
):
    if (
        chat.type == pyrogram.enums.chat_type.ChatType.GROUP
        or chat.type == pyrogram.enums.chat_type.ChatType.SUPERGROUP
    ):
        relationship: RUserChat = RUserChat.get_or_none(
            user_id=user.id, chat_id=chat.id
        )
        if not relationship:
            RUserChat.create(user_id=user.id, chat_id=chat.id)


def DBChatAdmins(client: pyrogram.Client, chat_id: int, clean_up=False):
    settings: ChatSettings = ChatSettings.get(chat_id=chat_id)
    if clean_up:
        RUserChat.update(
            rank=0,
            is_admin=False,
            can_be_edited=True,
            can_change_info=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_manage_chat=False,
            can_manage_video_chats=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_restrict_members=False,
        ).where((RUserChat.chat_id == chat_id) & (RUserChat.is_admin)).execute()
    for member in client.get_chat_members(
        chat_id=chat_id,
        filter=pyrogram.enums.chat_members_filter.ChatMembersFilter.ADMINISTRATORS,
    ):
        DBUser(user=member.user)
        creator = (
            member.status == pyrogram.enums.chat_member_status.ChatMemberStatus.OWNER
        )
        if RUserChat.get_or_none(user_id=member.user.id, chat_id=chat_id):
            RUserChat.update(
                rank=4
                if creator
                else (
                    3
                    if bool(member.privileges.can_promote_members)
                    else (2 if bool(member.privileges.can_restrict_members) else 1)
                ),
                is_member=True,
                is_admin=True,
                can_be_edited=bool(member.can_be_edited),
                can_change_info=creator or bool(member.privileges.can_change_info),
                can_delete_messages=creator
                or bool(member.privileges.can_delete_messages),
                can_invite_users=creator or bool(member.privileges.can_invite_users),
                can_manage_chat=creator or bool(member.privileges.can_manage_chat),
                can_manage_video_chats=creator
                or bool(member.privileges.can_manage_video_chats),
                can_pin_messages=creator or bool(member.privileges.can_pin_messages),
                can_promote_members=creator
                or bool(member.privileges.can_promote_members),
                can_restrict_members=creator
                or bool(member.privileges.can_restrict_members),
            ).where(
                (RUserChat.user_id == member.user.id) & (RUserChat.chat_id == chat_id)
            ).execute()
        else:
            RUserChat.create(
                user_id=member.user.id,
                chat_id=chat_id,
                rank=4
                if creator
                else (
                    3
                    if bool(member.privileges.can_promote_members)
                    else (2 if bool(member.privileges.can_restrict_members) else 1)
                ),
                is_member=True,
                is_admin=True,
                can_be_edited=bool(member.can_be_edited),
                can_change_info=creator or bool(member.privileges.can_change_info),
                can_delete_messages=creator
                or bool(member.privileges.can_delete_messages),
                can_invite_users=creator or bool(member.privileges.can_invite_users),
                can_manage_chat=creator or bool(member.privileges.can_manage_chat),
                can_manage_video_chats=creator
                or bool(member.privileges.can_manage_video_chats),
                can_pin_messages=creator or bool(member.privileges.can_pin_messages),
                can_promote_members=creator
                or bool(member.privileges.can_promote_members),
                can_restrict_members=creator
                or bool(member.privileges.can_restrict_members),
            )
        if creator:
            settings.owner_id = member.user.id
            settings.save()


def DBChatMembers(client: pyrogram.Client, chat_id: int, clean_up=True):
    if clean_up:
        RUserChat.update(is_member=False).where(
            (RUserChat.chat_id == chat_id) & (RUserChat.is_member)
        ).execute()
    # check restricted members
    for member in client.get_chat_members(
        chat_id=chat_id,
        filter=pyrogram.enums.chat_members_filter.ChatMembersFilter.RESTRICTED,
    ):
        DBUser(user=member.user)
        if RUserChat.get_or_none(user_id=member.user.id, chat_id=chat_id):
            RUserChat.update(is_member=member.is_member).where(
                (RUserChat.user_id == member.user.id) & (RUserChat.chat_id == chat_id)
            ).execute()
        else:
            RUserChat.create(
                user_id=member.user.id,
                chat_id=chat_id,
                is_member=member.is_member,
            )
    # check members, admins and creator
    for member in client.get_chat_members(
        chat_id=chat_id,
        filter=pyrogram.enums.chat_members_filter.ChatMembersFilter.SEARCH,
    ):
        DBUser(user=member.user)
        if RUserChat.get_or_none(user_id=member.user.id, chat_id=chat_id):
            RUserChat.update(is_member=True).where(
                (RUserChat.user_id == member.user.id) & (RUserChat.chat_id == chat_id)
            ).execute()
        else:
            RUserChat.create(
                user_id=member.user.id,
                chat_id=chat_id,
                is_member=True,
            )


def DBObject(
    obj: typing.Union[
        pyrogram.types.Message,
        pyrogram.types.CallbackQuery,
        pyrogram.types.User,
        pyrogram.types.Chat,
    ],
    client: pyrogram.Client,
    old_seen_message: bool = False,
) -> dict:
    """
    Unpack the given object to save them inside the DB

    Args:
        obj (typing.Union[pyrogram.types.Message, pyrogram.types.CallbackQuery, pyrogram.types.User, pyrogram.types.Chat]): One of the types here
        client (pyrogram.Client): Pyrogram Client

    Returns:
        obj (typing.Union[pyrogram.types.Message, pyrogram.types.CallbackQuery, pyrogram.types.User, pyrogram.types.Chat]): One of the types here modified accordingly
    """
    if isinstance(obj, pyrogram.types.Message):
        if not obj.empty:
            if obj.from_user:
                DBUser(user=obj.from_user)
                obj.from_user.settings = UserSettings.get_or_none(
                    user_id=obj.from_user.id
                )

            if obj.chat.type == pyrogram.enums.chat_type.ChatType.PRIVATE:
                DBUser(user=obj.chat)
                if not client.ME.is_bot:
                    obj.chat.settings = UserSettings.get_or_none(user_id=obj.chat.id)
                    obj.chat.settings.has_blocked_bot = False
                    obj.chat.settings.save()
                else:
                    obj.chat.settings = UserSettings.get_or_none(
                        user_id=obj.from_user.id
                    )
                    obj.chat.settings.has_blocked_bot = False
                    obj.chat.settings.save()
            else:
                created = DBChat(chat=obj.chat)
                obj.chat.settings = ChatSettings.get_or_none(chat_id=obj.chat.id)
                if (
                    obj.chat.type == pyrogram.enums.chat_type.ChatType.GROUP
                    or obj.chat.type == pyrogram.enums.chat_type.ChatType.SUPERGROUP
                ):
                    if created:
                        try:
                            DBChatAdmins(
                                client=client, chat_id=obj.chat.id, clean_up=False
                            )
                        except Exception as ex:
                            print(ex)
                            traceback.print_exc()
                    DBUserChat(user=client.ME, chat=obj.chat)
                    obj.r_bot_chat = RUserChat.get_or_none(
                        user_id=client.ME.id, chat_id=obj.chat.id
                    )
                    obj.r_bot_chat.timestamp = datetime.datetime.utcnow()
                    obj.r_bot_chat.save()

            if obj.sender_chat:
                obj.sender_chat.settings = obj.chat.settings

            if obj.from_user and (
                obj.chat.type == pyrogram.enums.chat_type.ChatType.GROUP
                or obj.chat.type == pyrogram.enums.chat_type.ChatType.SUPERGROUP
            ):
                DBUserChat(user=obj.from_user, chat=obj.chat)
                if not old_seen_message:
                    # atomic update
                    RUserChat.update(
                        {
                            RUserChat.message_counter: RUserChat.message_counter + 1,
                            RUserChat.timestamp: datetime.datetime.utcnow(),
                        }
                    ).where(
                        (RUserChat.user == obj.from_user.id)
                        & (RUserChat.chat == obj.chat.id)
                    ).execute()
                obj.r_user_chat = RUserChat.get_or_none(
                    user_id=obj.from_user.id, chat_id=obj.chat.id
                )

            if obj.forward_from:
                DBUser(user=obj.forward_from)
                obj.forward_from.settings = UserSettings.get_or_none(
                    user_id=obj.forward_from.id
                )
            elif obj.forward_from_chat:
                DBChat(chat=obj.forward_from_chat)

            if (
                obj.service
                == pyrogram.enums.message_service_type.MessageServiceType.NEW_CHAT_MEMBERS
            ):
                for i, user in enumerate(obj.new_chat_members):
                    DBUser(user=user)
                    DBUserChat(user=user, chat=obj.chat)
                    obj.new_chat_members[i].settings = UserSettings.get_or_none(
                        user_id=user.id
                    )
            elif (
                obj.service
                == pyrogram.enums.message_service_type.MessageServiceType.LEFT_CHAT_MEMBERS
            ):
                DBUser(user=obj.left_chat_member)
                DBUserChat(user=obj.left_chat_member, chat=obj.chat)
                obj.left_chat_member.settings = UserSettings.get_or_none(
                    user_id=obj.left_chat_member.id
                )

            if obj.entities:
                for i, entity in enumerate(obj.entities):
                    if (
                        entity.type
                        == pyrogram.enums.message_entity_type.MessageEntityType.TEXT_MENTION
                    ):
                        DBUser(user=entity.user)
                        obj.entities[i].user.settings = UserSettings.get_or_none(
                            user_id=entity.user.id
                        )

            if obj.caption_entities:
                for i, entity in enumerate(obj.caption_entities):
                    if (
                        entity.type
                        == pyrogram.enums.message_entity_type.MessageEntityType.TEXT_MENTION
                    ):
                        DBUser(user=entity.user)
                        obj.caption_entities[
                            i
                        ].user.settings = UserSettings.get_or_none(
                            user_id=entity.user.id
                        )

            if obj.reply_to_message:
                obj.reply_to_message = DBObject(
                    obj=obj.reply_to_message, client=client, old_seen_message=True
                )
    elif isinstance(obj, pyrogram.types.CallbackQuery):
        if obj.from_user:
            DBUser(user=obj.from_user)
            obj.from_user.settings = UserSettings.get_or_none(user_id=obj.from_user.id)

        if obj.message:
            obj.message = DBObject(
                obj=obj.message, client=client, old_seen_message=True
            )

        if (
            obj.message.chat.type == pyrogram.enums.chat_type.ChatType.GROUP
            or obj.message.chat.type == pyrogram.enums.chat_type.ChatType.SUPERGROUP
        ):
            DBUserChat(user=obj.from_user, chat=obj.message.chat)
            obj.r_user_chat = RUserChat.get_or_none(
                user_id=obj.from_user.id, chat_id=obj.message.chat.id
            )
            obj.r_user_chat.timestamp = datetime.datetime.utcnow()
            obj.r_user_chat.save()

            obj.r_bot_chat = RUserChat.get_or_none(
                user_id=client.ME.id, chat_id=obj.message.chat.id
            )
            obj.r_bot_chat.timestamp = datetime.datetime.utcnow()
            obj.r_bot_chat.save()
    elif isinstance(obj, pyrogram.types.User):
        DBUser(user=obj)
        obj.settings = UserSettings.get_or_none(user_id=obj.id)
    elif isinstance(obj, pyrogram.types.Chat):
        if (
            obj.type == pyrogram.enums.chat_type.ChatType.PRIVATE
            or obj.type == pyrogram.enums.chat_type.ChatType.BOT
        ):
            DBUser(user=obj)
            obj.settings = UserSettings.get_or_none(user_id=obj.id)
        else:
            DBChat(chat=obj)
            obj.settings = ChatSettings.get_or_none(chat_id=obj.id)
    return obj
