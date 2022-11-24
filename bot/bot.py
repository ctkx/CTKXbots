import nextcord
from nextcord.ext import commands
import os
import sys
for path in ["/bot_cogs","/bot_functions"]:
    if path not in sys.path:
        sys.path.append(path)

from keys_and_codes import discord_token

activity = nextcord.Activity(type=nextcord.ActivityType.listening, name="Waiting for commands")

client = commands.Bot(command_prefix = '/',activity=activity, status=nextcord.Status.idle,help_command=None,intents = nextcord.Intents.all())

cog_dir = '/bot_cogs'

bot_cogs=[
    'cog_ping',
    'cog_admin',
    'cog_wallet',
    'cog_auto_nft_role',
]

for filename in os.listdir(cog_dir):
    if filename.endswith('.py') and filename.replace(".py","") in bot_cogs :
        print ("Loading Cog: "+filename)
        client.load_extension(f'{filename[:-3]}')

print(f"Completed Cog Loading. Activating Bot")

client.run (discord_token)
