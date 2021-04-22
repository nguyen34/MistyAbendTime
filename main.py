# For debugging
# from pprint import pprint

import asyncio
import os
import pytz
from datetime import datetime, timedelta
from threading import Thread

import discord
from flask import Flask
from twitchAPI.twitch import Twitch

# Comma separated list of Twitch usernames for which to retrieve stream information
user_logins = ["sarryuu", "sakaiichigo", "ZenNoKiseki", "makupurata", "allie_hope", "lavifarseille", "walkersunrise", "zane_kazuki", "domiwoof", "cleoontwitch", "deltanine13vt", "archmagestower", "xellius", "AltinaAngelfire"]
known_streams = { login : None for login in user_logins }


app = Flask('')

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

twitch = Twitch(os.environ.get("TWITCH_BOT_APP_ID"), os.environ.get("TWITCH_BOT_SECRET"))
twitch.authenticate_app([])

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
  token = os.environ.get("DISCORD_BOT_SECRET")
  client.run(token)

async def refresh_notification():
  while True:
    streams = twitch.get_streams(user_login=user_logins)['data']
    stream_map = { stream['user_name'] : stream for stream in streams }

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

  guild = client.get_guild(779072021866610748)

  # For initialization

  await refresh_notification()

async def notify_discord(stream):
  tz_LA = pytz.timezone('America/Los_Angeles')
  threshold = (datetime.now() - timedelta(seconds=300)).astimezone(tz_LA) 
  timestamp = datetime.strptime(stream['started_at'], "%Y-%m-%dT%H:%M:%SZ").astimezone(tz_LA)
  if (timestamp < threshold):
    return

  game = twitch.get_games(game_ids=[stream["game_id"]])['data'][0]
  user = twitch.get_users(logins=[stream["user_name"]])['data'][0]

  channel = client.get_channel(803702005750693948)
  message = "Hey, <@&806061880526635059>! Welcome to Abend Time. I'm your host, Misty, here to let you know that " + stream["user_name"] + " is streaming right now! Come check them out!"
  embed = discord.Embed(
    title=f"https://www.twitch.tv/{stream['user_name']}",
    colour=discord.Colour(0x9146FF),
    url=f"https://www.twitch.tv/{stream['user_name']}",
    description=stream['title'],
  )

  # embed.set_image(
  #  url=stream["thumbnail_url"].replace("{width}", "640").replace("{height}", "360")
  # )
  embed.set_thumbnail(
    url=user["profile_image_url"]
  )
  embed.add_field(name="Now Playing", value=game["name"], inline=False)

  embed.set_footer(text=timestamp.strftime("%B %d, %Y at %-I:%M%p"))
  await channel.send(message, embed=embed)

main()