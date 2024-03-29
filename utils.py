import base64
import datetime
import glob
import html
import json
import math
import os
import re
import shutil
import struct
import tarfile
import time
import traceback
import typing

import peewee
import pyrogram
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from pyrogram import errors as pyrogram_errors
from pytz import utc

import db_management
import dictionaries

start_date = datetime.datetime.utcnow()

scheduler = BackgroundScheduler(timezone=utc)
scheduler.start()


with open(file="langs.json", encoding="utf-8") as f:
    langs = json.load(fp=f)


def GetLocalizedDictionary(locale: str) -> str:
    """
    Use this method for langs.json
    locale (``str``): Desired locale.
    SUCCESS Returns ``dict`` of the desired locale.
    FAILURE Returns ``str`` saying there's no such string.
    """
    locale = str(locale)
    if locale in langs:
        return langs[locale]
    else:
        print(f"unknown language '{locale}'")
        return langs["en"]["unknown_language"].format(locale)


def GetLocalizedString(locale: str, string: str) -> str:
    """
    Use this method for langs.json

    locale (``str``): Desired locale.

    string (``str``): Desired string.

    SUCCESS Returns ``str`` in the desired locale.
    NEITHER SUCCESS NOR FAILURE (missing language) Returns ``str`` in English.
    #FAILURE Returns ``str`` saying there's no such string.
    """
    localized_strings = None
    locale = str(locale)
    string = str(string)
    if locale in langs:
        localized_strings = langs[locale]
    else:
        localized_strings = langs["en"]
        print(f"unknown locale '{locale}'")
    if string in localized_strings:
        return localized_strings[string]
    else:
        print(f"unknown string '{locale}' '{string}'")
        # return localized_strings["unknown_string"].format(locale,
        #                                                  string)
        if locale != "en":
            return GetLocalizedString(locale="en", string=string)
        else:
            return localized_strings["unknown_string"].format(locale, string)


_ = GetLocalizedString
RTL_CHARACTER = "‏"
ARABIC_REGEX = re.compile(pattern=r"[\u0621-\u064a\ufb50-\ufdff\ufe70-\ufefc]")
ORIGINAL_LINK_REGEX_PATTERN = (
    r"((telegram\.(me|dog)|t\.me)/(joinchat/|\+)([A-Z0-9_-]+))"
)
ORIGINAL_USERNAME_REGEX_PATTERN = (
    r"((@|((telegram\.(me|dog)|t\.me)/))([A-Z]([A-Z0-9_]){3,30}[A-Z0-9]))"
)
LINK_REGEX = re.compile(pattern=r"(t\.me/(joinchat/|\+)[A-Z0-9_-]+)", flags=re.I)
# remember to not consider t.me/joinchat
USERNAME_REGEX = re.compile(
    pattern=r"(@|t\.me/)([A-Z]([A-Z0-9_]){3,30}[A-Z0-9])", flags=re.I
)
config = None
with open(file="config.json", encoding="utf-8") as f:
    config = json.load(fp=f)


# temp dictionary for commands that requires more than one interaction to complete (e.g. set welcome via keyboard)
tmp_steps = dict(
    # chat_id = generic unspecified data, usually tuple( original_cb_qry, variable )
)


tmp_dicts = dict(
    # to stop automatic punishments of user after kick^ (stopping flood or other things)
    kickedPeople=dict(
        # chat_id = set(user_ids)
    ),
    # to not invite the same user again and again (just once every X minutes or if (s)he is kicked)
    invitedPeople=dict(
        # chat_id = set(user_ids)
    ),
    # to prevent shitstorms using messages hashes
    msgsHashes=dict(
        # chat_id = dict(
        #   msgTextHash or mediaId = list(msg_dates)
        # )
    ),
    # to prevent flooding
    flood=dict(
        # chat_id = dict(
        #   user_id = dict(
        #       cb_qrs_times = list(cb_qry_dates),
        #       cb_qrs_flood_wait_expiry_date = 0,
        #       cb_qrs_previous_flood_wait = 0,
        #       msgs_times = list(msg_dates)
        #   )
        # )
    ),
    punishments=dict(
        # chat_id = dict(
        #   msg.id or cb_qry.id = dict(
        #       punishment = 0,
        #       reasons = list()
        #   )
        # )
    ),
    greetings=dict(
        # chat_id = dict(
        #   counter = 0,
        #   last_welcome = last_welcome_msg_id,
        #   last_goodbye = last_goodbye_msg_id
        # )
    ),
    # to avoid contacting the admins of a group too much times (just once every X minutes)
    staffContacted=set(
        # chat_ids
    ),
    # to avoid flood waits in requesting administrators (just once every X minutes)
    staffUpdated=set(
        # chat_ids
    ),
    # to avoid flood waits in requesting members (just once every X minutes)
    membersUpdated=set(
        # chat_ids
    ),
)


def CleanTempVariable(identifier: str, value: typing.Union[dict, set]):
    tmp_dicts[identifier] = value


# CRON JOBS
# every day at 3:00
scheduler.add_job(
    CleanTempVariable,
    trigger=CronTrigger(hour=3, timezone=utc),
    args=("msgsHashes", dict()),
)
scheduler.add_job(
    CleanTempVariable, trigger=CronTrigger(hour=3, timezone=utc), args=("flood", dict())
)
scheduler.add_job(
    CleanTempVariable,
    trigger=CronTrigger(hour=3, timezone=utc),
    args=("punishments", dict()),
)
scheduler.add_job(
    CleanTempVariable,
    trigger=CronTrigger(hour=3, timezone=utc),
    args=("greetings", dict()),
)
# every sharp hour
scheduler.add_job(
    CleanTempVariable,
    trigger=CronTrigger(minute=0, timezone=utc),
    args=("membersUpdated", set()),
)
# INTERVAL JOBS, see config.json for specific intervals
scheduler.add_job(
    CleanTempVariable,
    trigger=IntervalTrigger(
        seconds=config["tmp_dicts_expiration"]["kickedPeople"], timezone=utc
    ),
    args=("kickedPeople", dict()),
)
scheduler.add_job(
    CleanTempVariable,
    trigger=IntervalTrigger(
        seconds=config["tmp_dicts_expiration"]["invitedPeople"], timezone=utc
    ),
    args=("invitedPeople", dict()),
)
scheduler.add_job(
    CleanTempVariable,
    trigger=IntervalTrigger(
        seconds=config["tmp_dicts_expiration"]["staffContacted"], timezone=utc
    ),
    args=("staffContacted", set()),
)
scheduler.add_job(
    CleanTempVariable,
    trigger=IntervalTrigger(
        seconds=config["tmp_dicts_expiration"]["staffUpdated"], timezone=utc
    ),
    args=("staffUpdated", set()),
)


def InstantiateKickedPeopleDictionary(chat_id: int):
    # if chat_id not registered into the punished people dictionary register it
    if chat_id not in tmp_dicts["kickedPeople"]:
        tmp_dicts["kickedPeople"][chat_id] = set()


def InstantiateInvitedPeopleDictionary(chat_id: int):
    # if chat_id or user_id not registered into the invited people dictionary register it
    if chat_id not in tmp_dicts["invitedPeople"]:
        tmp_dicts["invitedPeople"][chat_id] = set()


def InstantiateMsgsHashesDictionary(chat_id: int, msg_hash: str):
    # if chat_id not registered into the msgsHashes dictionary register it
    if chat_id not in tmp_dicts["msgsHashes"]:
        tmp_dicts["msgsHashes"][chat_id] = dict()
    if msg_hash not in tmp_dicts["msgsHashes"][chat_id]:
        tmp_dicts["msgsHashes"][chat_id][msg_hash] = list()


def InstantiateFloodDictionary(chat_id: int, user_id: int):
    # if chat_id not registered into the flood dictionary register it
    if chat_id not in tmp_dicts["flood"]:
        tmp_dicts["flood"][chat_id] = dict()
    if user_id not in tmp_dicts["flood"][chat_id]:
        tmp_dicts["flood"][chat_id][user_id] = dict(
            cb_qrs_times=list(),
            cb_qrs_flood_wait_expiry_date=0,
            # from 0 to X minutes of wait depending on how much of an idiot is the user
            cb_qrs_previous_flood_wait=0,
            # no warned parameter for callback_queries because they have no limit, just one per query and that's all
            msgs_times=list(),
        )


def InstantiatePunishmentDictionary(chat_id: int, id_: int):
    # if chat_id not registered into the punishments dictionary register it
    if chat_id not in tmp_dicts["punishments"]:
        tmp_dicts["punishments"][chat_id] = dict()
    if id_ not in tmp_dicts["punishments"][chat_id]:
        tmp_dicts["punishments"][chat_id][id_] = dict(punishment=0, reasons=list())


def ChangePunishmentAddReason(chat_id: int, id_: int, punishment: int, reason: str):
    tmp_dicts["punishments"][chat_id][id_]["punishment"] = max(
        punishment, tmp_dicts["punishments"][chat_id][id_]["punishment"]
    )
    tmp_dicts["punishments"][chat_id][id_]["reasons"].append(reason)
    return tmp_dicts["punishments"][chat_id][id_]["punishment"]


def InstantiateGreetingsDictionary(chat_id: int):
    if chat_id not in tmp_dicts["greetings"]:
        tmp_dicts["greetings"][chat_id] = dict(
            counter=0, last_welcome=0, last_goodbye=0
        )


def PrintUser(user: pyrogram.types.User, use_html=False) -> str:
    return (
        (
            html.escape(
                user.first_name + (f" {user.last_name}" if user.last_name else "")
            )
            if use_html
            else (user.first_name + (f" {user.last_name}" if user.last_name else ""))
        )
        + " ("
        + (
            (f"<code>@{user.username}</code> " if use_html else f"@{user.username} ")
            if user.username
            else ""
        )
        + f"#user{user.id})"
    )


def PrintChat(chat: pyrogram.types.Chat, use_html=False) -> str:
    return (
        html.escape(
            chat.title
            + " ("
            + (f"@{chat.username} " if chat.username else "")
            + f"#chat{abs(chat.id)})"
        )
        if use_html
        else (
            chat.title
            + " ("
            + (f"@{chat.username} " if chat.username else "")
            + f"#chat{abs(chat.id)})"
        )
    )


def PrintMessage(msg: pyrogram.types.Message) -> str:
    if msg:
        receiver = ""
        if (
            msg.chat.type == pyrogram.enums.chat_type.ChatType.BOT
            or msg.chat.type == pyrogram.enums.chat_type.ChatType.PRIVATE
        ):
            receiver = PrintUser(user=msg.chat)
        else:
            receiver = PrintChat(chat=msg.chat)

        sender = ""
        if msg.from_user:
            sender = PrintUser(user=msg.from_user)
        else:
            if msg.sender_chat:
                sender = "ANONYMOUS"
            else:
                sender = receiver

        string = ""
        if receiver == sender:
            string = f"[UTC {msg.date} #msg{msg.id}] {sender} >>>"
        else:
            string = f"[UTC {msg.date} #msg{msg.id}] {receiver}, {sender} >>>"
        if msg.edit_date:
            string += " [edited] "
        if msg.forward_from or msg.forward_from_chat:
            tmp = ""
            if msg.forward_from:
                tmp = PrintUser(user=msg.forward_from)
            elif msg.forward_from_chat:
                tmp = PrintChat(chat=msg.forward_from_chat)
            string += f" [forwarded from {tmp}] "
        if msg.reply_to_message:
            string += f" [reply to #msg{msg.reply_to_message.id}] "

        if msg.service:
            tmp = " ERR UNKNOWN SERVICE"
            if msg.new_chat_members:
                tmp = " [added]" + " ".join(
                    PrintUser(user=user) for user in msg.new_chat_members
                )
            elif msg.left_chat_member:
                tmp = f" [removed {PrintUser(user=msg.left_chat_member)}]"
            elif msg.new_chat_title:
                tmp = f" [changed chat title to {msg.new_chat_title}]"
            elif msg.new_chat_photo:
                tmp = f" [changed chat photo to {msg.new_chat_photo.id}]"
            elif msg.delete_chat_photo:
                tmp = " [deleted chat photo]"
            elif msg.group_chat_created:
                tmp = " [created this group]"
            elif msg.supergroup_chat_created:
                tmp = " [created this supergroup]"
            elif msg.channel_chat_created:
                tmp = " [created this channel]"
            elif msg.pinned_message:
                tmp = f" [pinned #msg{msg.pinned_message.id}]"
            elif msg.migrate_to_chat_id:
                tmp = f" [migrating to #chat{abs(msg.migrate_to_chat_id)}]"
            elif msg.migrate_from_chat_id:
                tmp = f" [migrated from #chat{abs(msg.migrate_from_chat_id)}]"
            string += tmp
        elif msg.media:
            media, type_ = ExtractMedia(msg)
            string += f" [{type_}:{media.media_id}]"
            if msg.caption:
                string += f" {msg.caption}"
        elif msg.text:
            string += f" {msg.text}"
        return string
    return str(None)


def PrintCallbackQuery(cb_qry: pyrogram.types.CallbackQuery) -> str:
    if cb_qry:
        date = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        receiver = ""
        if (
            cb_qry.message.chat.type == pyrogram.enums.chat_type.ChatType.BOT
            or cb_qry.message.chat.type == pyrogram.enums.chat_type.ChatType.PRIVATE
        ):
            receiver = PrintUser(user=cb_qry.message.chat)
        else:
            receiver = PrintChat(chat=cb_qry.message.chat)

        sender = ""
        if cb_qry.from_user:
            sender = PrintUser(user=cb_qry.from_user)
        else:
            sender = receiver

        string = ""
        if receiver == sender:
            string = (
                f"[UTC {date} #cbqry{cb_qry.id} #msg{cb_qry.message.id}] {sender} >>>"
            )
        else:
            string = f"[UTC {date} #cbqry{cb_qry.id} #msg{cb_qry.message.id}] {receiver}, {sender} >>>"

        string += f" {cb_qry.data}"
        return string
    return str(None)


def ReloadPlugins(client: pyrogram.Client, msg: pyrogram.types.Message):
    client.restart()
    db_management.LoadPluginsToDB()
    msg.reply_text(_(msg.chat.settings.language, "plugins_config_langs_reloaded"))


def Backup() -> str:
    # empty downloads folder
    for filename in os.listdir("./downloads"):
        file_path = os.path.join("./downloads", filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as ex:
            print(f"Failed to delete {file_path}. Reason: {ex}")
    # remove previous backups
    for filename in glob.glob("./backupAISashaBot*"):
        os.remove(filename)
    # compress db
    db_management.DB.execute_sql("VACUUM")
    db_management.DB.stop()
    backup_name = f"backupAISashaBot{int(time.time())}.tar.xz"
    with tarfile.open(backup_name, mode="w:xz") as f_tar_xz:
        for folder_name, subfolders, filenames in os.walk("./"):
            if not (folder_name.startswith("./.git") or "__pycache__" in folder_name):
                for filename in filenames:
                    if filename != backup_name and not (
                        filename.endswith(".session")
                        or filename.endswith(".session-journal")
                    ):
                        # exclude current backup and session files
                        file_path = os.path.join(folder_name, filename)
                        print(file_path)
                        f_tar_xz.add(file_path)
    db_management.DB.start()

    return backup_name


def RemoveCommand(cmd: list) -> str:
    # remove the actual command
    cmd.pop(0)

    message = ""
    if len(cmd):
        # "/cmd foobar foo bar" reconstruct the path in case there are spaces (pyrogram.filters.command uses spaces as default separator)
        message += " ".join(cmd)
    return message


def IsInt(v) -> bool:
    """
    Check if the parameter can be int.

    v: Variable to check.


    SUCCESS Returns ``True``.

    FAILURE Returns ``False``.
    """
    try:
        int(v)
        return True
    except Exception:
        return False


def CensorPhone(obj: object) -> object:
    if hasattr(obj, "phone_number"):
        obj.phone_number = "CENSORED"
    if hasattr(obj, "from_user"):
        if hasattr(obj.from_user, "phone_number"):
            obj.from_user.phone_number = "CENSORED"
    if hasattr(obj, "reply_to_message"):
        if hasattr(obj, "from_user"):
            if hasattr(obj.reply_to_message.from_user, "phone_number"):
                obj.reply_to_message.from_user.phone_number = "CENSORED"
    return obj


def ExtractMedia(msg: pyrogram.types.Message) -> typing.Tuple[object, str]:
    """Extract the media from a :obj:`Message <pyrogram.types.Message>`.

    msg (:obj:`Message <pyrogram.types.Message>`): Message from which you want to extract the media


    SUCCESS Returns a tuple with the media (``object``) and its type.

    FAILURE Returns (``None``, ``None``).
    """
    media = None
    type_ = None
    if msg and not msg.empty:
        if msg.media == pyrogram.enums.message_media_type.MessageMediaType.ANIMATION:
            media = msg.animation
            type_ = "animation"
            media.media_id = media.file_id
        elif msg.media == pyrogram.enums.message_media_type.MessageMediaType.AUDIO:
            media = msg.audio
            type_ = "audio"
            media.media_id = media.file_id
        elif msg.media == pyrogram.enums.message_media_type.MessageMediaType.CONTACT:
            media = msg.contact
            type_ = "contact"
            media.media_id = media.phone_number
        elif msg.media == pyrogram.enums.message_media_type.MessageMediaType.DOCUMENT:
            media = msg.document
            type_ = "document"
            media.media_id = media.file_id
        elif msg.media == pyrogram.enums.message_media_type.MessageMediaType.GAME:
            media = msg.game
            type_ = "game"
            media.media_id = media.id
        elif msg.media == pyrogram.enums.message_media_type.MessageMediaType.LOCATION:
            media = msg.location
            type_ = "location"
            media.media_id = f"{media.latitude}, {media.longitude}"
        elif msg.media == pyrogram.enums.message_media_type.MessageMediaType.PHOTO:
            media = msg.photo
            type_ = "photo"
            media.media_id = media.file_id
        elif msg.media == pyrogram.enums.message_media_type.MessageMediaType.POLL:
            media = msg.poll
            type_ = "poll"
            media.media_id = media.id
        elif msg.media == pyrogram.enums.message_media_type.MessageMediaType.STICKER:
            media = msg.sticker
            type_ = "sticker"
            media.media_id = media.file_id
        elif msg.media == pyrogram.enums.message_media_type.MessageMediaType.VENUE:
            media = msg.venue
            type_ = "venue"
            media.media_id = f"{media.location.latitude}, {media.location.longitude}"
        elif msg.media == pyrogram.enums.message_media_type.MessageMediaType.VIDEO:
            media = msg.video
            type_ = "video"
            media.media_id = media.file_id
        elif msg.media == pyrogram.enums.message_media_type.MessageMediaType.VIDEO_NOTE:
            media = msg.video_note
            type_ = "video_note"
            media.media_id = media.file_id
        elif msg.media == pyrogram.enums.message_media_type.MessageMediaType.VOICE:
            media = msg.voice
            type_ = "voice"
            media.media_id = media.file_id
    return media, type_


def SizeFormatter(b: int, human_readable: bool = False) -> str:
    """
    Adjust the size from bits to the right measure.

    b (``int``): Number of bits.


    SUCCESS Returns the adjusted measure (``str``).
    """
    if human_readable:
        B = float(b / 8)
        KB = float(1024)
        MB = float(pow(KB, 2))
        GB = float(pow(KB, 3))
        TB = float(pow(KB, 4))

        if B < KB:
            return f"{B} B"
        elif KB <= B < MB:
            return f"{B/KB:.2f} KB"
        elif MB <= B < GB:
            return f"{B/MB:.2f} MB"
        elif GB <= B < TB:
            return f"{B/GB:.2f} GB"
        elif TB <= B:
            return f"{B/TB:.2f} TB"
    else:
        B, b = divmod(int(b), 8)
        KB, B = divmod(B, 1024)
        MB, KB = divmod(KB, 1024)
        GB, MB = divmod(MB, 1024)
        TB, GB = divmod(GB, 1024)
        tmp = (
            ((f"{TB}TB, ") if TB else "")
            + ((f"{GB}GB, ") if GB else "")
            + ((f"{MB}MB, ") if MB else "")
            + ((f"{KB}KB, ") if KB else "")
            + ((f"{B}B, ") if B else "")
            + ((f"{b}b, ") if b else "")
        )
        return tmp[:-2]


def TimeFormatter(milliseconds: int) -> str:
    """
    Adjust the time from milliseconds to the right measure.

    milliseconds (``int``): Number of milliseconds.


    SUCCESS Returns the adjusted measure (``str``).
    """
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((f"{days}d, ") if days else "")
        + ((f"{hours}h, ") if hours else "")
        + ((f"{minutes}m, ") if minutes else "")
        + ((f"{seconds}s, ") if seconds else "")
        + ((f"{milliseconds}ms, ") if milliseconds else "")
    )
    return tmp[:-2]


def DFromUToTelegramProgress(
    current: int,
    total: int,
    msg: pyrogram.types.Message,
    text: str,
    start: float,
) -> None:
    """
    Use this method to update the progress of a download from/an upload to Telegram, this method is called every 512KB.
    Update message every ~4 seconds.

    current (``int``): Currently downloaded/uploaded bytes.

    total (``int``): File size in bytes.

    msg (:class:`Message <pyrogram.types.Message>`): The Message to update while downloading/uploading the file.

    text (``str``): Text to put into the update.

    start (``float``): Time when the operation started.


    Returns ``None``.
    """
    # 1048576 is 1 MB in bytes
    now = time.time()
    diff = now - start
    if round(diff % 4.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)
        # 0% = [░░░░░░░░░░░░░░░░░░░░]
        # 100% = [████████████████████]
        progress = "[{0}{1}] {2}%\n".format(
            "".join("█" for i in range(math.floor(percentage / 5))),
            "".join("░" for i in range(20 - math.floor(percentage / 5))),
            round(percentage, 2),
        )
        tmp = progress + "{0}/{1}\n{2}/s {3}/{4}\n".format(
            SizeFormatter(b=current * 8, human_readable=True),
            SizeFormatter(b=total * 8, human_readable=True),
            SizeFormatter(b=speed * 8, human_readable=True),
            elapsed_time if elapsed_time != "" else "0 s",
            estimated_total_time if estimated_total_time != "" else "0 s",
        )

        msg.edit_text(text=text + tmp)


def CleanLink(url: str) -> str:
    url = re.sub(pattern=r"https?://", repl="", string=url, flags=re.I)
    url = re.sub(pattern=r"www\.", repl="", string=url, flags=re.I)
    url = re.sub(pattern=r"telegram.dog", repl="t.me", string=url, flags=re.I)
    url = re.sub(pattern=r"telegram.me", repl="t.me", string=url, flags=re.I)
    return url


def CleanUsername(username: str) -> str:
    username = CleanLink(url=username)
    username = re.sub(pattern=r"t.me/", repl="@", string=username, flags=re.I)
    return username


def ConvertTimedModeToTime(value: int) -> str:
    value = f"{value / 4:.2f}"
    hour, minute = value.split(".")
    return f"{int(hour):02d}:{int(int(minute) / 25 * 15):02d}"


def ConvertUnixToDuration(timestamp: int) -> tuple:
    remainder, weeks, days, hours, minutes, seconds = 0, 0, 0, 0, 0, 0
    weeks = math.floor(timestamp / 604800)
    remainder = timestamp % 604800
    days = math.floor(remainder / 86400)
    remainder = remainder % 86400
    hours = math.floor(remainder / 3600)
    remainder = remainder % 3600
    minutes = math.floor(remainder / 60)
    seconds = remainder % 60
    return weeks, days, hours, minutes, seconds


def ConvertDurationToUnix(
    seconds: int = 0, minutes: int = 0, hours: int = 0, days: int = 0, weeks: int = 0
) -> int:
    time = (
        weeks * 7 * 24 * 60 * 60
        + days * 24 * 60 * 60
        + hours * 60 * 60
        + minutes * 60
        + seconds
    )
    return time


def ResolveCommandToId(
    client: pyrogram.Client,
    value: typing.Union[str, int],
    msg: pyrogram.types.Message = None,
) -> typing.Union[str, int]:
    language = None
    if msg and msg.chat and msg.chat.settings:
        language = msg.chat.settings.language

    if msg and msg.reply_to_message:
        return msg.reply_to_message.from_user.id
    elif value:
        if IsInt(value):
            # if already id return
            return int(value)
        else:
            # either text_mention or username
            if msg and msg.entities:
                text_to_use = msg.text or msg.caption
                for entity in msg.entities:
                    if (
                        entity.type
                        == pyrogram.enums.message_entity_type.MessageEntityType.TEXT_MENTION
                        and text_to_use[entity.offset : entity.offset + entity.length]
                        == value
                    ):
                        # if text_mention and the substring of the entity is equal to value then return id
                        return entity.user.id

            tmp = str(CleanLink(url=value))
            if LINK_REGEX.findall(string=tmp):
                # t.me/joinchat/<blablabla>
                link_parameters = (None, None, None)
                try:
                    link_parameters = ResolveInviteLink(link=tmp)
                    return link_parameters[1]
                except Exception as ex:
                    print(ex)
                    traceback.print_exc()
                    return f"{value}: " + _(language, "error_try_again")
            else:
                # t.me/username or @username or username
                value = CleanUsername(username=tmp)
                value = f"@{value}" if not value.startswith("@") else value
                query: peewee.ModelSelect = (
                    db_management.ResolvedObjects.select()
                    .where(db_management.ResolvedObjects.username == value[1:].lower())
                    .order_by(db_management.ResolvedObjects.timestamp.desc())
                )
                try:
                    resolved_obj = query.get()
                    # if already resolved object return saved id
                    return resolved_obj.id
                except db_management.ResolvedObjects.DoesNotExist:
                    # else try to resolve the username with Telegram
                    # if success return id, else return error
                    try:
                        tmp = client.get_chat(chat_id=value)
                        tmp = db_management.DBObject(obj=tmp, client=client)
                        return tmp.id
                    except pyrogram_errors.FloodWait as ex:
                        print(ex)
                        traceback.print_exc()
                        return f"{value}: " + _(language, "tg_flood_wait_X").format(
                            ex.value
                        )
                    except pyrogram_errors.RPCError as ex:
                        print(ex)
                        traceback.print_exc()
                        return f"{value}: " + _(language, "tg_error_X").format(ex)
    return f"{value}: " + _(language, "error_try_again")


def GetCommandsVariants(commands: list, del_: bool = False, pvt: bool = False) -> list:
    tmp = list()
    for cmd in commands:
        if del_ and pvt:
            tmp.append(f"del{cmd}pvt")
        if del_:
            tmp.append(f"del{cmd}")
        if pvt:
            tmp.append(f"{cmd}pvt")
    tmp.extend(commands)
    return tmp


def AdjustMarkers(
    value: str, msg: pyrogram.types.Message, welcome: bool = False
) -> str:
    # chat
    value = AdjustChatMarkers(value=value, chat=msg.chat)

    if msg.new_chat_members:
        # if welcoming users use filtered list excluding bots and kicked people, otherwise use normal list
        new_chat_members = (
            [
                x
                for x in msg.new_chat_members
                if not x.is_bot and x.id not in tmp_dicts["kickedPeople"][msg.chat.id]
            ]
            if welcome
            else msg.new_chat_members
        )
        if new_chat_members:
            if len(new_chat_members) == 1:
                # joined/invited user
                value = AdjustUserMarkers(value=value, user=new_chat_members[0])
            else:
                # invited users
                value = value.replace(
                    "$user_id",
                    ", ".join([str(x.id) for x in new_chat_members]),
                )
                value = value.replace(
                    "$first_name",
                    ", ".join([html.escape(x.first_name) for x in new_chat_members]),
                )
                value = value.replace(
                    "$last_name",
                    ", ".join(
                        [
                            html.escape(x.last_name) if x.last_name else ""
                            for x in new_chat_members
                        ]
                    ),
                )
                value = value.replace(
                    "$full_name",
                    ", ".join(
                        [
                            html.escape(x.first_name)
                            + (f" {html.escape(x.last_name)}" if x.last_name else "")
                            for x in new_chat_members
                        ]
                    ),
                )
                value = value.replace(
                    "$reversed_full_name",
                    ", ".join(
                        [
                            (f"{html.escape(x.last_name)} " if x.last_name else "")
                            + html.escape(x.first_name)
                            for x in new_chat_members
                        ]
                    ),
                )
                value = value.replace(
                    "$username",
                    ", ".join(
                        [
                            f"@{x.username}" if x.username else "@USERNAME"
                            for x in new_chat_members
                        ]
                    ),
                )
                value = value.replace(
                    "$mention",
                    ", ".join(
                        [
                            f'<a href="tg://user?id={x.id}">{html.escape(x.first_name)}</a>'
                            for x in new_chat_members
                        ]
                    ),
                )
    elif msg.left_chat_member:
        # leaving/kicked user
        if msg.left_chat_member.is_bot:
            return None
        else:
            value = AdjustUserMarkers(value=value, user=msg.left_chat_member)
    else:
        # user
        value = AdjustUserMarkers(value=value, user=msg.from_user)
    if msg.forward_from or msg.forward_from_chat:
        value = value.replace("$forward_", "$")
        if msg.forward_from_chat:
            # forward chat
            value = AdjustChatMarkers(value=value, chat=msg.forward_from_chat)
        if msg.forward_from:
            # forward user
            value = AdjustUserMarkers(value=value, user=msg.from_user)

    if msg.reply_to_message:
        # reply
        value = value.replace("$reply_", "$")
        value = AdjustMarkers(value=value, msg=msg.reply_to_message, welcome=welcome)

    if len(value) > 4096:
        value = value[:4096]
    return value


def AdjustUserMarkers(value: str, user: pyrogram.types.User) -> str:
    # joined/invited user
    value = value.replace("$user_id", str(user.id))
    value = value.replace("$first_name", html.escape(user.first_name))
    value = value.replace(
        "$last_name", html.escape(user.last_name) if user.last_name else ""
    )
    value = value.replace(
        "$full_name",
        html.escape(user.first_name)
        + (f" {html.escape(user.last_name)}" if user.last_name else ""),
    )
    value = value.replace(
        "$reversed_full_name",
        ((html.escape(user.last_name) + " ") if user.last_name else "")
        + html.escape(user.first_name),
    )
    value = value.replace(
        "$username", f"@{user.username}" if user.username else "@USERNAME"
    )
    value = value.replace(
        "$mention",
        f'<a href="tg://user?id={user.id}">{html.escape(user.first_name)}</a>',
    )
    return value


def AdjustChatMarkers(value: str, chat: pyrogram.types.Chat) -> str:
    # chat
    value = value.replace("$chat_id", str(chat.id))
    value = value.replace("$chat_title", html.escape(chat.title))
    value = value.replace(
        "$chat_username", f"@{chat.username}" if chat.username else "@USERNAME"
    )
    if hasattr(chat, "settings") and chat.settings:
        value = value.replace(
            "$link",
            chat.settings.link
            if chat.settings.link
            else GetLocalizedString(chat.settings.language, "no_chat_link"),
        )
        rules = chat.settings.extras.where(
            (db_management.ChatExtras.key == "rules")
            & (db_management.ChatExtras.is_group_data)
        ).get()
        value = value.replace(
            "$rules",
            html.escape(
                rules.value
                if rules.value
                else GetLocalizedString(chat.settings.language, "no_chat_rules")
            ),
        )
    return value


def IsTelegramAdministrator(
    user_id: int,
    chat_id: int = 0,
    r_user_chat: db_management.RUserChat = None,
) -> bool:
    if chat_id < 0:
        relationship: db_management.RUserChat = (
            r_user_chat
            if r_user_chat
            else db_management.RUserChat.get_or_none(user_id=user_id, chat_id=chat_id)
        )
        if relationship and relationship.is_admin:
            # includes telegram admins
            return True
    else:
        return any(
            x.is_admin
            for x in db_management.RUserChat.select().where(
                db_management.RUserChat.user_id == user_id
            )
        )


def IsMasterOrBot(user_id: int) -> bool:
    return bool(user_id in config["masters"])


# TODO IMPLEMENT CHECKS FOR NETWORKS AND BOT ADMINISTRATORS


def IsOwnerOrHigher(
    user_id: int,
    chat_id: int = 0,
    r_user_chat: db_management.RUserChat = None,
) -> bool:
    if IsMasterOrBot(user_id=user_id):
        return True
    else:
        if chat_id < 0:
            relationship: db_management.RUserChat = (
                r_user_chat
                if r_user_chat
                else db_management.RUserChat.get_or_none(
                    user_id=user_id, chat_id=chat_id
                )
            )
            if relationship and relationship.rank > 3:
                # includes owner
                return True
        else:
            return any(
                x.rank > 3
                for x in db_management.RUserChat.select().where(
                    db_management.RUserChat.user_id == user_id
                )
            )
    return False


def IsSeniorModOrHigher(
    user_id: int,
    chat_id: int = 0,
    r_user_chat: db_management.RUserChat = None,
) -> bool:
    if IsMasterOrBot(user_id=user_id):
        return True
    else:
        if chat_id < 0:
            relationship: db_management.RUserChat = (
                r_user_chat
                if r_user_chat
                else db_management.RUserChat.get_or_none(
                    user_id=user_id, chat_id=chat_id
                )
            )
            if relationship and relationship.rank > 2:
                # includes senior mods and owner
                return True
        else:
            return any(
                x.rank > 2
                for x in db_management.RUserChat.select().where(
                    db_management.RUserChat.user_id == user_id
                )
            )
    return False


def IsJuniorModOrHigher(
    user_id: int,
    chat_id: int = 0,
    r_user_chat: db_management.RUserChat = None,
) -> bool:
    if IsMasterOrBot(user_id=user_id):
        return True
    else:
        if chat_id < 0:
            relationship: db_management.RUserChat = (
                r_user_chat
                if r_user_chat
                else db_management.RUserChat.get_or_none(
                    user_id=user_id, chat_id=chat_id
                )
            )
            if relationship and relationship.rank > 1:
                # includes junior mods, senior mods and owner
                return True
        else:
            return any(
                x.rank > 1
                for x in db_management.RUserChat.select().where(
                    db_management.RUserChat.user_id == user_id
                )
            )
    return False


def IsPrivilegedOrHigher(
    user_id: int,
    chat_id: int = 0,
    r_user_chat: db_management.RUserChat = None,
) -> bool:
    if IsMasterOrBot(user_id=user_id):
        return True
    else:
        if chat_id < 0:
            relationship: db_management.RUserChat = (
                r_user_chat
                if r_user_chat
                else db_management.RUserChat.get_or_none(
                    user_id=user_id, chat_id=chat_id
                )
            )
            if relationship and relationship.rank > 0:
                # includes privileged, junior mods, senior mods and owner
                return True
        else:
            return any(
                x.rank > 0
                for x in db_management.RUserChat.select().where(
                    db_management.RUserChat.user_id == user_id
                )
            )
    return False


def GetRank(
    user_id: int,
    chat_id: int = 0,
    r_user_chat: db_management.RUserChat = None,
) -> int:
    # TODO IMPLEMENT NETWORK CHECKS
    if IsPrivilegedOrHigher(user_id=user_id, chat_id=chat_id, r_user_chat=r_user_chat):
        if IsJuniorModOrHigher(
            user_id=user_id,
            chat_id=chat_id,
            r_user_chat=r_user_chat,
        ):
            if IsSeniorModOrHigher(
                user_id=user_id,
                chat_id=chat_id,
                r_user_chat=r_user_chat,
            ):
                if IsOwnerOrHigher(
                    user_id=user_id,
                    chat_id=chat_id,
                    r_user_chat=r_user_chat,
                ):
                    if IsMasterOrBot(user_id=user_id):
                        return dictionaries.RANK_STRING["master"]
                    else:
                        return dictionaries.RANK_STRING["owner"]
                else:
                    return dictionaries.RANK_STRING["senior_mod"]
            else:
                return dictionaries.RANK_STRING["junior_mod"]
        else:
            return dictionaries.RANK_STRING["privileged_user"]
    else:
        return dictionaries.RANK_STRING["user"]


def CompareRanks(
    executer: int,
    target: int,
    chat_id: int = 0,
    r_executer_chat: db_management.RUserChat = None,
    r_target_chat: db_management.RUserChat = None,
    min_rank: int = 0,
) -> bool:
    executer_rank = GetRank(
        user_id=executer,
        chat_id=chat_id,
        r_user_chat=r_executer_chat,
    )
    target_rank = GetRank(user_id=target, chat_id=chat_id, r_user_chat=r_target_chat)
    if executer_rank > target_rank and executer_rank >= min_rank:
        return True
    else:
        return False


def IsInNightMode(
    chat_settings: db_management.ChatSettings, time_tup: typing.Tuple[int, int] = None
) -> bool:
    if chat_settings.night_mode_punishment:
        if not time_tup:
            tmp = datetime.datetime.utcnow()
            time_tup = (tmp.hour, tmp.minute)
        converted_time = (time_tup[0] + time_tup[1] / 60) * 4
        if (
            converted_time >= chat_settings.night_mode_from
            or converted_time < chat_settings.night_mode_to
        ):
            return True
        else:
            return False
    else:
        return False


def ResolveInviteLink(link: str):
    """Converts Invite Link to Tuple with inviter_id, chat_id, random_hash

    Arguments:
        link {str} -- Link in "t.me/joinchat/INTERESTING_PART" or "t.me/+INTERESTING_PART" formats.

    Returns:
        [tuple] -- inviter_id, chat_id, random_hash
    """
    # from: https://github.com/ColinTheShark/Pyrogram-Snippets/blob/master/Snippets/resolve_invite_link.py
    interesting_part = link.split("/")[-1]
    if interesting_part.startswith("+"):
        interesting_part = interesting_part[1:]
    return struct.unpack(">iiq", base64.urlsafe_b64decode(interesting_part + "=="))


def Log(
    client: pyrogram.Client,
    chat_id: int,
    executer: int,
    action: str,
    target: int = None,
    chat_settings: db_management.ChatSettings = None,
    log_channel_notice: bool = True,
):
    chat_settings = chat_settings or (
        db_management.ChatSettings.get_or_none(chat_id=chat_id)
    )
    db_management.Logs.create(
        chat_id=chat_id,
        executer=executer,
        action=action,
        target=target,
    )
    if chat_settings and chat_settings.log_channel:
        chat_str = PrintChat(chat_settings.chat)
        executer_str = PrintUser(db_management.Users.get_or_none(id=executer))
        target_str = (
            (
                PrintChat(db_management.Chats.get_or_none(id=target))
                if target < 0
                else PrintUser(db_management.Users.get_or_none(id=target))
            )
            if IsInt(target)
            else ""
        )
        if log_channel_notice:
            scheduler.add_job(
                func=client.send_message,
                trigger=DateTrigger(
                    run_date=datetime.datetime.utcnow()
                    + datetime.timedelta(seconds=config["delay_log_channel"]),
                    timezone=utc,
                ),
                kwargs=dict(
                    chat_id=chat_settings.log_channel,
                    text=_(chat_settings.language, "log_string").format(
                        chat_str or f"#chat{abs(chat_id)}",
                        executer_str or f"#user{executer}",
                        action,
                        (
                            target_str
                            or (
                                (
                                    f"#chat{abs(target)}"
                                    if target < 0
                                    else f"#user{target}"
                                )
                            )
                        )
                        if IsInt(target)
                        else "",
                    ),
                    disable_notification=True,
                ),
            )
