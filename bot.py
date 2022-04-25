# PREPROCESS ORDER MESSAGES
# pre_process_post(-11, -7, -1)
# help (-10)
# check_msg(-9, -8, -1)
# alternatives(-6)
# chat_management(-5)
# user_management(-4)
# extra_variables(-3)
# flame(-2)

# PREPROCESS ORDER CALLBACK QUERIES
# pre_process_post(-11, -8)
# check_msg(-9)
# chat_management(-1)
import datetime
import logging
import os
import time

import pyrogram
from apscheduler.triggers.cron import CronTrigger
from pyrogram import errors as pyrogram_errors
from pytz import utc

import db_management
import methods
import utils

start_string = "{bot_version}\n{bot_data}"
_ = utils.GetLocalizedString

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.ERROR
)

if not (utils.config and utils.langs):
    logging.log(logging.FATAL, "Missing config.json or langs.json")
    exit()

plugins = dict(root="plugins")
# wait one second to have tables created
time.sleep(1)
db_management.LoadPluginsToDB()

BOT_CLIENT = pyrogram.Client(
    name="AISashaBot",
    workers=4,
    plugins=plugins,
    parse_mode=pyrogram.enums.parse_mode.ParseMode.DISABLED,
)

BOT_CLIENT.start()
BOT_CLIENT.ME = BOT_CLIENT.get_me()
db_management.DBUser(user=BOT_CLIENT.ME)
print(
    start_string.format(
        bot_version=f"Pyrogram {BOT_CLIENT.ME.first_name}",
        bot_data=utils.PrintUser(user=BOT_CLIENT.ME),
    )
)

loaded_plugins = list()
for dirpath, dirnames, filenames in os.walk(BOT_CLIENT.plugins["root"]):
    # filter out __pycache__ folders
    if "__pycache__" not in dirpath:
        loaded_plugins.extend(
            # filter out __init__.py
            filter(lambda x: x != "__init__.py", filenames)
        )

for x in utils.config["masters"][1:]:
    try:
        BOT_CLIENT.send_message(
            chat_id=x,
            text=f"<b>Bot started!</b>\n<b>Pyrogram: {pyrogram.__version__}</b>\n<b>{datetime.datetime.utcnow()}</b>\n"
            + "\n".join(
                sorted(
                    # put html and take only file_name
                    map(
                        lambda x: f"<code>{os.path.splitext(x)[0]}</code>",
                        loaded_plugins,
                    )
                )
            )
            + f"\n\n<b>{len(loaded_plugins)} plugins loaded</b>",
            parse_mode=pyrogram.enums.parse_mode.ParseMode.HTML,
        )
    except pyrogram_errors.RPCError as ex:
        print(ex)

utils.Log(
    client=BOT_CLIENT,
    chat_id=BOT_CLIENT.ME.id,
    executer=BOT_CLIENT.ME.id,
    action="start",
    target=BOT_CLIENT.ME.id,
)
# schedule backup at UTC 02:30 with a random delay between ± 10 minutes
utils.scheduler.add_job(
    methods.SendBackup,
    trigger=CronTrigger(hour=2, minute=30, jitter=600, timezone=utc),
    args=(BOT_CLIENT,),
)
pyrogram.idle()
BOT_CLIENT.stop()

db_management.DB.close()
