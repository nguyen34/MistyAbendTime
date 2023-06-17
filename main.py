# For debugging
# from pprint import pprint
import asyncio
import os
import pytz
from datetime import datetime, timedelta
from threading import Thread
from dotenv.main import load_dotenv

import discord
from flask import Flask
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first

# Comma separated list of Twitch usernames for which to retrieve stream information
user_logins = [
    'ZenNoKiseki', 'ChibiNo1', 'VileYuzu', 'TheHonkinator', 'Lonnolan',
    'Candy_VT', 'Belldanndys_tea_house', 'ZaneDase', 'Sheekiyomi',
    'MimiArmelle', 'Zer0Senpa1', 'HinagikuNezuchi', 'maplemaple_ch',
    'DinoNuggetVT', 'Bazinski', 'jbn29', 'exia23', 'RevBrucifer', 'Omaruyuu',
    'Makupurata', 'Dragonmoon26', 'Pirushiroinu', 'sagikiihori', 'laphipi',
    'MoonfoxxTiho', 'sagikiihori', 'IkkeZen', 'Zeroni_vt', 'Venenofgc',
    'DocDresden', 'RyujinHayato'
]

load_dotenv()

## COPY EVERYTHING FROM HERE DOWNWARDS FOR REPL.IT
DISCORD_BOT_SECRET = os.environ['DISCORD_BOT_SECRET']
TWITCH_BOT_APP_ID = os.environ['TWITCH_BOT_APP_ID']
TWITCH_BOT_SECRET = os.environ['TWITCH_BOT_SECRET']

DISCORD_ID = 814658322236964904
DISCORD_CHANNEL_ID_FRIENDS = 877078280820375582
DISCORD_CHANNEL_ID_MAIN = 877043070749802516
STREAM_PING_ROLE_ID = 877620295882661918

known_streams = {login: None for login in user_logins}
app = Flask('')

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

twitch = Twitch(TWITCH_BOT_APP_ID, TWITCH_BOT_SECRET)
asyncio.run(twitch.authenticate_app([]))


@app.route('/')
def home():
    return "Hello world"


def run():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    run_thread = Thread(target=run)
    run_thread.start()


def main():
    keep_alive()
    token = DISCORD_BOT_SECRET
    client.run(token)


async def refresh_notification():
    while True:
        streams = twitch.get_streams(user_login=user_logins)
        stream_map = {stream.user_name: stream async for stream in streams}
        stream_list = list(stream_map.keys())
        print(f'Active Streamers: {stream_list}')
        for key in stream_map:
            if key not in known_streams or known_streams[key] is None:
                known_streams[key] = stream_map[key]
                await notify_discord(stream_map[key])

        for key in known_streams:
            if key not in stream_map:
                known_streams[key] = None

        await asyncio.sleep(60)


@client.event
async def on_ready():
    global guild
    print("I'm in")
    print(client.user)

    guild = client.get_guild(DISCORD_ID)
    # For initialization
    #await edit_message()
    # await add_reactions()
    await refresh_notification()


async def notify_discord(stream):
    tz_LA = pytz.timezone('America/Los_Angeles')
    timestamp = stream.started_at.astimezone(tz_LA)
    threshold = (datetime.now() - timedelta(seconds=300)).astimezone(tz_LA)
    print(
        f'{stream.user_name} started streaming on {timestamp.strftime("%B %d, %Y at %-I:%M%p")}'
    )
    if (timestamp < threshold):
        return
    game = await (first(twitch.get_games(game_ids=[stream.game_id])))
    user = await (first(twitch.get_users(logins=[stream.user_name])))

    if stream.user_name == "ZenNoKiseki":
        channel = client.get_channel(DISCORD_CHANNEL_ID_MAIN)
        message = f"Hey, <@&{STREAM_PING_ROLE_ID}>! Welcome to Abend Time. I'm your host, Misty, here to let you know that the Kiseki Cafe is open for business today! Come on in and relax for a while with a nice cup of coffee and a meal to unwind after a long day!"
        embed = discord.Embed(
            title=f"https://www.twitch.tv/{stream.user_name}",
            colour=discord.Colour(0x9146FF),
            url=f"https://www.twitch.tv/{stream.user_name}",
            description=stream.title,
        )
    else:
        channel = client.get_channel(DISCORD_CHANNEL_ID_FRIENDS)
        message = "Hey, <@&{STREAM_PING_ROLE_ID}>! Welcome to Abend Time. I'm your host, Misty, here to let you know that " + stream.user_name + " is streaming right now! Come check them out!"
        embed = discord.Embed(
            title=f"https://www.twitch.tv/{stream.user_name}",
            colour=discord.Colour(0x9146FF),
            url=f"https://www.twitch.tv/{stream.user_name}",
            description=stream.title,
        )
    # embed.set_image(
    #  url=stream["thumbnail_url"].replace("{width}", "640").replace("{height}", "360")
    # )
    print(message)
    embed.set_thumbnail(url=user.profile_image_url)
    embed.add_field(name="Now Playing", value=game.name, inline=False)

    embed.set_footer(text=timestamp.strftime("%B %d, %Y at %-I:%M%p"))
    await channel.send(message, embed=embed)


main()