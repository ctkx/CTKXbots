import nextcord
from nextcord.ext import commands
from nextcord import Interaction

import sys
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")

from keys_and_codes import default_embed_footer

def cog_ping_template_embed(intx_data):
    em = nextcord.Embed(title=intx_data['title'],description=intx_data['descr'],color=nextcord.Colour.random())
    em.add_field(name="Response",value="Pong!",inline=False)

    if 'embed_footer' in intx_data:
        embed_footer_text=intx_data['embed_footer']['text']
    else:
        embed_footer_text=default_embed_footer['text']

    em.set_footer(text = embed_footer_text, icon_url = default_embed_footer['icon_url'])
    return em

class cog_ping(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Events 
    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog Loaded : "+__file__)

    # Commands 
    @nextcord.slash_command(name="ping",description="Ping the bot")
    async def ping_command(self, interaction: Interaction):
        await interaction.response.defer(ephemeral=False, with_message=False)
        intx_data={
            'guild_id' : f"{interaction.guild.id}",
            'title' : f"Ping",
            'descr' : f"** **"
        }
        intx_data['em']=cog_ping_template_embed(intx_data)
        await interaction.edit_original_message(embed=intx_data['em'])

def setup(client):
    client.add_cog(cog_ping(client))
