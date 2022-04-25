import pyrogram

bot_api_key = "543383188:AAHiR8VOAvm8IQb3BQ9_g9FR3L_wLqS7yXw"
api_id = "98484"
api_hash = "c9de26abc080f233b81ef63aac870a65"

BOT_CLIENT = pyrogram.Client(
    name="AISashaBot",
    api_id=api_id,
    api_hash=api_hash,
    bot_token=bot_api_key,
    workers=4,
    plugins=dict(root="plugins"),
    parse_mode=pyrogram.enums.parse_mode.ParseMode.DISABLED,
)

BOT_CLIENT.start()
BOT_CLIENT.ME = BOT_CLIENT.get_me()
pyrogram.idle()
BOT_CLIENT.stop()
