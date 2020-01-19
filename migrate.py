import json
import time

import peewee
import pyrogram

import db_management
import utils

# when using this use peewee.SqliteDatabase as DB and not sqliteq.SqliteQueueDatabase
app = pyrogram.Client(
    session_name="MIGRATION",
    api_id=utils.config["telegram"]["api_id"],
    api_hash=utils.config["telegram"]["api_hash"],
    bot_token=utils.config["telegram"]["bot_api_key"],
    no_updates=True,
)

app.start()


def DBChatAdmins(chat_id: int):
    settings: db_management.ChatSettings = db_management.ChatSettings.get(
        chat_id=chat_id
    )
    for member in app.iter_chat_members(chat_id=chat_id, filter="administrators"):
        db_management.DBUser(user=member.user)
        creator = member.status == "creator"
        if db_management.RUserChat.get_or_none(user_id=member.user.id, chat_id=chat_id):
            db_management.RUserChat.update(
                rank=4
                if creator
                else (
                    3
                    if bool(member.can_promote_members)
                    else (2 if bool(member.can_restrict_members) else 1)
                ),
                is_admin=True,
                can_be_edited=bool(member.can_be_edited),
                can_change_info=creator or bool(member.can_change_info),
                can_delete_messages=creator or bool(member.can_delete_messages),
                can_invite_users=creator or bool(member.can_invite_users),
                can_pin_messages=creator or bool(member.can_pin_messages),
                can_promote_members=creator or bool(member.can_promote_members),
                can_restrict_members=creator or bool(member.can_restrict_members),
            ).where(
                (db_management.RUserChat.user_id == member.user.id)
                & (db_management.RUserChat.chat_id == chat_id)
            ).execute()
        else:
            db_management.RUserChat.create(
                user_id=member.user.id,
                chat_id=chat_id,
                rank=4
                if creator
                else (
                    3
                    if bool(member.can_promote_members)
                    else (2 if bool(member.can_restrict_members) else 1)
                ),
                is_admin=True,
                can_be_edited=bool(member.can_be_edited),
                can_change_info=creator or bool(member.can_change_info),
                can_delete_messages=creator or bool(member.can_delete_messages),
                can_invite_users=creator or bool(member.can_invite_users),
                can_pin_messages=creator or bool(member.can_pin_messages),
                can_promote_members=creator or bool(member.can_promote_members),
                can_restrict_members=creator or bool(member.can_restrict_members),
            )
        if creator:
            settings.owner_id = member.user.id
            settings.save()


def DBChatSettings(chat_id: int, chat_settings: dict):
    db_management.ChatSettings.create(
        chat_id=chat_id,
        language=chat_settings["lang"]
        if "lang" in chat_settings
        and chat_settings["lang"] in utils.config["available_languages"]
        else "en",
        link=chat_settings["link"] if "link" in chat_settings else None,
        welcome_members=int(chat_settings["welcomemembers"])
        if "welcomemembers" in chat_settings
        else 0,
        is_link_public=int(not chat_settings["settings"]["lock_grouplink"])
        if "lock_grouplink" in chat_settings["settings"]
        else 0,
        max_flood=int(chat_settings["settings"]["max_flood"])
        if "max_flood" in chat_settings["settings"]
        else 5,
        max_warns=int(chat_settings["settings"]["max_warns"])
        if "max_warns" in chat_settings["settings"]
        else 3,
        max_temp_restrict=int(chat_settings["settings"]["time_restrict"])
        if "time_restrict" in chat_settings["settings"]
        else 86400,
        max_temp_ban=int(chat_settings["settings"]["time_ban"])
        if "time_ban" in chat_settings["settings"]
        else 86400,
        group_notices=2 if "groupnotices" in chat_settings["settings"] else 0,
        has_tag_alerts=int(chat_settings["settings"]["tagalert"])
        if "tagalert" in chat_settings["settings"]
        else 0,
        max_warns_punishment=int(chat_settings["settings"]["warns_punishment"])
        if "warns_punishment" in chat_settings["settings"]
        and int(chat_settings["settings"]["warns_punishment"]) >= 4
        else 7,
        allow_service_messages=int(chat_settings["settings"]["mutes"]["tgservices"])
        if "tgservices" in chat_settings["settings"]["mutes"]
        else 1,
        anti_everything=int(chat_settings["settings"]["mutes"]["all"])
        if "all" in chat_settings["settings"]["mutes"]
        else 0,
        anti_animation=int(chat_settings["settings"]["mutes"]["gifs"])
        if "gifs" in chat_settings["settings"]["mutes"]
        else 0,
        anti_audio=int(chat_settings["settings"]["mutes"]["audios"])
        if "audios" in chat_settings["settings"]["mutes"]
        else 0,
        anti_contact=int(chat_settings["settings"]["mutes"]["contacts"])
        if "contacts" in chat_settings["settings"]["mutes"]
        else 0,
        anti_document=int(chat_settings["settings"]["mutes"]["documents"])
        if "documents" in chat_settings["settings"]["mutes"]
        else 0,
        anti_game=int(chat_settings["settings"]["mutes"]["games"])
        if "games" in chat_settings["settings"]["mutes"]
        else 0,
        anti_location=int(chat_settings["settings"]["mutes"]["locations"])
        if "locations" in chat_settings["settings"]["mutes"]
        else 0,
        anti_photo=int(chat_settings["settings"]["mutes"]["photos"])
        if "photos" in chat_settings["settings"]["mutes"]
        else 0,
        anti_sticker=int(chat_settings["settings"]["mutes"]["stickers"])
        if "stickers" in chat_settings["settings"]["mutes"]
        else 0,
        anti_text=int(chat_settings["settings"]["mutes"]["text"])
        if "text" in chat_settings["settings"]["mutes"]
        else 0,
        anti_venue=int(chat_settings["settings"]["mutes"]["locations"])
        if "locations" in chat_settings["settings"]["mutes"]
        and chat_settings["settings"]["mutes"]["locations"]
        else 0,
        anti_video=int(chat_settings["settings"]["mutes"]["videos"])
        if "videos" in chat_settings["settings"]["mutes"]
        else 0,
        anti_video_note=int(chat_settings["settings"]["mutes"]["video_notes"])
        if "video_notes" in chat_settings["settings"]["mutes"]
        else 0,
        anti_voice=int(chat_settings["settings"]["mutes"]["voice_notes"])
        if "voice_notes" in chat_settings["settings"]["mutes"]
        else 0,
        add_punishment=int(chat_settings["settings"]["locks"]["members"])
        if "members" in chat_settings["settings"]["locks"]
        and int(chat_settings["settings"]["locks"]["members"]) >= 4
        else 5,
        arabic_punishment=int(chat_settings["settings"]["locks"]["arabic"])
        if "arabic" in chat_settings["settings"]["locks"]
        else 0,
        bot_punishment=int(chat_settings["settings"]["locks"]["bots"])
        if "bots" in chat_settings["settings"]["locks"]
        and chat_settings["settings"]["locks"]["bots"]
        and int(chat_settings["settings"]["locks"]["bots"]) >= 3
        else 3,
        censorships_punishment=int(chat_settings["settings"]["locks"]["delword"])
        if "delword" in chat_settings["settings"]["locks"]
        else 1,
        flood_punishment=int(chat_settings["settings"]["locks"]["flood"])
        if "flood" in chat_settings["settings"]["locks"]
        else 2,
        forward_punishment=int(chat_settings["settings"]["locks"]["forward"])
        if "forward" in chat_settings["settings"]["locks"]
        and int(chat_settings["settings"]["locks"]["forward"]) >= 2
        else 0,
        globally_banned_punishment=int(
            chat_settings["settings"]["locks"]["gbanned"]
        )
        if "gbanned" in chat_settings["settings"]["locks"]
        and int(chat_settings["settings"]["locks"]["gbanned"]) >= 4
        else 5,
        join_punishment=int(chat_settings["settings"]["locks"]["members"])
        if "members" in chat_settings["settings"]["locks"]
        and int(chat_settings["settings"]["locks"]["members"]) >= 4
        else 0,
        link_spam_punishment=int(chat_settings["settings"]["locks"]["links"])
        if "links" in chat_settings["settings"]["locks"]
        else 2,
        rtl_punishment=int(chat_settings["settings"]["locks"]["rtl"])
        if "rtl" in chat_settings["settings"]["locks"]
        and int(chat_settings["settings"]["locks"]["rtl"]) >= 4
        else 1,
        shitstorm_punishment=7,
        text_spam_punishment=int(chat_settings["settings"]["locks"]["spam"])
        if "spam" in chat_settings["settings"]["locks"]
        else 0,
    )
    # extras
    db_management.ChatExtras.bulk_create(
        [
            db_management.ChatExtras(
                chat_id=chat_id,
                key="goodbye",
                value=chat_settings["goodbye"]
                if "goodbye" in chat_settings and chat_settings["goodbye"]
                else "",
                is_group_data=True,
            ),
            db_management.ChatExtras(
                chat_id=chat_id,
                key="rules",
                value=chat_settings["rules"]
                if "rules" in chat_settings and chat_settings["rules"]
                else "",
                is_group_data=True,
            ),
            db_management.ChatExtras(
                chat_id=chat_id,
                key="welcome",
                value=chat_settings["welcome"]
                if "welcome" in chat_settings and chat_settings["welcome"]
                else "",
                is_group_data=True,
            ),
            db_management.ChatExtras(
                chat_id=chat_id,
                key="welcome_buttons",
                value="",
                is_group_data=True,
            ),
        ]
    )
    # whitelist
    db_management.ChatWhitelistedChats.create(
        chat_id=chat_id, whitelisted_chat=-1001066197625
    )
    if utils.config["settings"]["channel"]:
        db_management.ChatWhitelistedChats.create(
            chat_id=chat_id, whitelisted_chat=utils.config["settings"]["channel"]
        )
    for item in chat_settings["whitelist"]["links"]:
        if item.startswith("@"):
            if item != "@username":
                item = item.replace("@", "")
                res = app.get_chat(item)
                if res:
                    if not db_management.ChatWhitelistedChats.get_or_none(
                        chat_id=chat_id, whitelisted_chat=res.id
                    ):
                        db_management.ChatWhitelistedChats.create(
                            chat_id=chat_id, whitelisted_chat=res.id
                        )
                time.sleep(5)
        else:
            try:
                res = utils.ResolveInviteLink(link=item)
            except Exception as ex:
                print(ex)
            else:
                if res and len(res) == 3:
                    if not db_management.ChatWhitelistedChats.get_or_none(
                        chat_id=chat_id, whitelisted_chat=res[1]
                    ):
                        db_management.ChatWhitelistedChats.create(
                            chat_id=chat_id, whitelisted_chat=res[1]
                        )
    # plugins
    query: peewee.ModelSelect = db_management.Plugins.select().where(
        db_management.Plugins.is_optional
    ).order_by(db_management.Plugins.name)
    for plugin in query:
        if not db_management.RChatPlugin.get_or_none(
            chat=chat_id, plugin=plugin.name
        ):
            db_management.RChatPlugin.create(
                chat=chat_id,
                plugin=plugin.name,
                min_rank=0,
                is_enabled_on_chat=True,
            )
    # import disabled plugins
    tmp: dict = json.load(open("old_config.json", "r", encoding="utf-8"))
    if str(chat_id) in tmp["disabled_plugin_on_chat"]:
        dis_on_chat = tmp["disabled_plugin_on_chat"][str(chat_id)]
        for old_name in dis_on_chat:
            new_name = old_name
            if new_name == "getsetunset":
                new_name = "extras"
            elif new_name == "qr":
                new_name = "qrify"
            elif new_name == "tex":
                new_name = "latex"
            elif new_name == "urbandictionary":
                new_name = "urban_dictionary"
            r_chat_plugin: db_management.RChatPlugin = db_management.RChatPlugin.get_or_none(
                chat=chat_id, plugin=new_name
            )
            if r_chat_plugin:
                r_chat_plugin.is_enabled_on_chat = bool(dis_on_chat[old_name])
                r_chat_plugin.save()
    # owner and mods
    try:
        DBChatAdmins(chat_id)
    except Exception as ex:
        print(ex)
    if "moderators" in chat_settings and chat_settings["moderators"]:
        for user_id in chat_settings["moderators"]:
            if not db_management.Users.get_or_none(id=user_id):
                r_user_chat: db_management.RUserChat = db_management.RUserChat.get_or_none(
                    chat_id=chat_id, user_id=user_id
                )
                if not r_user_chat:
                    try:
                        r_user_chat = db_management.RUserChat.create(
                            chat_id=chat_id, user_id=user_id
                        )
                    except Exception as ex:
                        print(ex)
                        continue
                if r_user_chat.rank < 2:
                    r_user_chat.rank = 2
                    r_user_chat.save()
    if "owner" in chat_settings and chat_settings["owner"]:
        if not db_management.Users.get_or_none(id=chat_settings["owner"]):
            r_user_chat: db_management.RUserChat = db_management.RUserChat.get_or_none(
                chat_id=chat_id, user_id=chat_settings["owner"]
            )
            if not r_user_chat:
                r_user_chat = db_management.RUserChat.create(
                    chat_id=chat_id, user_id=chat_settings["owner"]
                )
            if r_user_chat.rank < 3:
                r_user_chat.rank = 3
                r_user_chat.save()


# database
print("database")
chats = []
users = []
ruserchats = []
tmp: dict = json.load(open("old_db.json", "r", encoding="utf-8"))
for k, v in tmp.items():
    if utils.IsInt(k):
        k = int(k)
        if k < 0:
            chats.append(
                dict(
                    id=k,
                    title=v["print_name"],
                    username=v["username"].replace("@", "")
                    if "username" in v and v["username"] and v["username"] != "NOUSER"
                    else None,
                )
            )
        elif k > 0:
            users.append(
                dict(
                    id=k,
                    first_name=v["print_name"]
                    if "print_name" in v and v["print_name"]
                    else "",
                    username=v["username"].replace("@", "")
                    if "username" in v and v["username"] and v["username"] != "NOUSER"
                    else None,
                    is_bot=v["type"] == "bot" if "type" in v and v["type"] else False,
                )
            )
            if "groups" in v and v["groups"]:
                for group_id in v["groups"]:
                    if int(group_id) < 0:
                        ruserchats.append(dict(user_id=k, chat_id=group_id))
# chats
for row in db_management.DB.batch_commit(chats, 240):
    try:
        db_management.Chats.create(**row)
    except Exception as ex:
        print(ex)
# users
for row in db_management.DB.batch_commit(users, 150):
    try:
        db_management.Users.create(**row)
    except Exception as ex:
        print(ex)
# ruserchats
for row in db_management.DB.batch_commit(ruserchats, 50):
    try:
        db_management.RUserChat.create(**row)
    except Exception as ex:
        print(ex)
# user_settings
for row in db_management.DB.batch_commit(users, 50):
    try:
        db_management.UserSettings.create(user_id=row["id"])
    except Exception as ex:
        print(ex)
# chat_settings
print("moderation")
tmp: dict = json.load(open("old_moderation.json", "r", encoding="utf-8"))
for k, v in tmp.items():
    if utils.IsInt(k):
        k = int(k)
        print(f"gp_data: {k}")
        try:
            DBChatSettings(k, v)
        except Exception as ex:
            print(ex)
        time.sleep(5)
# miscellaneous
print("rdb")
tmp: dict = json.load(open("old_rdb.json", "r", encoding="utf-8"))
# censorships
print("censorships")
censorships = []
censorships_keys = filter(
    lambda k: (k.startswith("group:") or k.startswith("supergroup:"))
    and k.endswith(":censorships"),
    tmp.keys(),
)
for k in censorships_keys:
    t = k.split(":")
    if len(t) == 3 and utils.IsInt(t[1]) and int(t[1]) < 0:
        ch_set: db_management.ChatSettings = db_management.ChatSettings.get_or_none(
            chat_id=int(t[1])
        )
        if ch_set:
            for cens in tmp[k].keys():
                if not cens.startswith("media:"):
                    censorships.append(dict(chat_id=int(t[1]), value=cens))
for row in db_management.DB.batch_commit(censorships, 150):
    try:
        db_management.ChatCensorships.create(**row)
    except Exception as ex:
        print(ex)
# extras
print("extras")
extras = []
extras_keys = filter(
    lambda k: (k.startswith("group:") or k.startswith("supergroup:"))
    and k.endswith(":variables"),
    tmp.keys(),
)
for k in extras_keys:
    t = k.split(":")
    if len(t) == 3 and utils.IsInt(t[1]) and int(t[1]) < 0:
        ch_set: db_management.ChatSettings = db_management.ChatSettings.get_or_none(
            chat_id=int(t[1])
        )
        if ch_set:
            for key, value in tmp[k].items():
                if not key.startswith("media:"):
                    extras.append(dict(chat_id=int(t[1]), key=key, value=value))
for row in db_management.DB.batch_commit(extras, 120):
    try:
        db_management.ChatExtras.create(**row)
    except Exception as ex:
        print(ex)
# langs
print("langs")
langs = []
lang_keys = filter(lambda k: k.startswith("lang:"), tmp.keys())
for k in lang_keys:
    t = k.split(":")
    if len(t) == 2 and utils.IsInt(t[1]) and int(t[1]) > 0:
        langs.append(dict(user_id=int(t[1]), lang=tmp[k]))
for row in db_management.DB.batch_commit(langs, 50):
    try:
        db_management.UserSettings.update(
            {db_management.UserSettings.language: row["lang"]}
        ).where(db_management.UserSettings.user == row["user_id"]).execute()
    except Exception as ex:
        print(ex)
# tagalerts
print("tagalerts")
us_set_set = set()
for k in tmp["tagalert:usernames"].keys():
    us_set_set.add(int(k))
for k in tmp["tagalert:nicknames"].keys():
    us_set_set.add(int(k))
for row in db_management.DB.batch_commit(us_set_set, 50):
    try:
        db_management.UserSettings.update(
            {
                db_management.UserSettings.wants_tag_alerts: 2,
                db_management.UserSettings.nickname: tmp["tagalert:nicknames"][str(k)]
                if str(k) in tmp["tagalert:nicknames"]
                else None,
            }
        ).where(db_management.UserSettings.user == k).execute()
    except Exception as ex:
        print(ex)
# warns
print("warns")
warns = []
missing_ruserchats = []
warn_keys = filter(lambda k: ":warn:" in k, tmp.keys())
for k in sorted(warn_keys):
    t = k.split(":")
    if (
        len(t) == 3
        and utils.IsInt(t[0])
        and utils.IsInt(t[2])
        and int(t[0]) < 0
        and int(t[2]) > 0
    ):
        ch: db_management.Chats = db_management.Chats.get_or_none(id=int(t[0]))
        us: db_management.Users = db_management.Users.get_or_none(id=int(t[2]))
        if ch and us:
            if not db_management.RUserChat.get_or_none(chat_id=ch.id, user_id=us.id):
                missing_ruserchats.append(dict(chat_id=ch.id, user_id=us.id))
            warns.append(dict(chat_id=ch.id, user_id=us.id, warns=int(tmp[k])))
for row in db_management.DB.batch_commit(missing_ruserchats, 50):
    try:
        db_management.RUserChat.create(**row)
    except Exception as ex:
        print(ex)
for row in db_management.DB.batch_commit(warns, 50):
    try:
        db_management.RUserChat.update(
            {db_management.RUserChat.warns: row["warns"]}
        ).where(
            (db_management.RUserChat.chat == row["chat_id"])
            & (db_management.RUserChat.user == row["user_id"])
        ).execute()
    except Exception as ex:
        print(ex)
# msgs
print("msgs")
msgs = []
missing_ruserchats = []
msgs_keys = filter(lambda k: k.startswith("msgs:"), tmp.keys())
for k in sorted(msgs_keys):
    t = k.split(":")
    if (
        len(t) == 3
        and utils.IsInt(t[1])
        and utils.IsInt(t[2])
        and int(t[1]) > 0
        and int(t[2]) < 0
    ):
        us: db_management.Users = db_management.Users.get_or_none(id=int(t[1]))
        ch: db_management.Chats = db_management.Chats.get_or_none(id=int(t[2]))
        if ch and us:
            if not db_management.RUserChat.get_or_none(chat_id=ch.id, user_id=us.id):
                missing_ruserchats.append(dict(chat_id=ch.id, user_id=us.id))
            msgs.append(dict(chat_id=ch.id, user_id=us.id, message_counter=int(tmp[k])))
for row in db_management.DB.batch_commit(missing_ruserchats, 50):
    try:
        db_management.RUserChat.create(**row)
    except Exception as ex:
        print(ex)
for row in db_management.DB.batch_commit(msgs, 50):
    try:
        db_management.RUserChat.update(
            {db_management.RUserChat.message_counter: row["message_counter"]}
        ).where(
            (db_management.RUserChat.chat == row["chat_id"])
            & (db_management.RUserChat.user == row["user_id"])
        ).execute()
    except Exception as ex:
        print(ex)

db_management.DB.execute_sql("VACUUM")

app.stop()
