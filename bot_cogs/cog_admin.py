import nextcord
from nextcord.ext import commands
import inspect

import sys

if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")

from database import log_channel_db
from keys_and_codes import default_embed_footer
import admin_main_menu, role_auth

class admin(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog Loaded : "+__file__)

    # Commands
    @nextcord.slash_command(name="admin",description="restricted")
    async def admin_command(self, interaction: nextcord.Interaction):

        # Create intx_data - Simple Assignments
        intx_data = {}
        intx_data['intx'] = interaction
        intx_data['title'] = "Admin"
        intx_data['descr'] = intx_data['intx'].guild.name

        # Create intx_data - guild_channels
        guild_channels = await interaction.guild.fetch_channels()
        intx_data['guild_channels']={}
        for channel in guild_channels:
            if isinstance(channel, nextcord.channel.TextChannel):
                intx_data['guild_channels'][channel.name] = channel

        # guild_members Members List
        guild_members = interaction.guild.fetch_members()
        intx_data['guild_members']=[]
        for member in await interaction.guild.fetch_members().flatten():
            if not member.bot:
                intx_data['guild_members'].append(member)

        # guild_roles Role List
        guild_roles = interaction.guild.roles
        intx_data['guild_roles']={}
        for role in guild_roles:
            if role.is_integration() or role.is_bot_managed():
                pass
            elif role.name != '@everyone':
                intx_data['guild_roles'][role.name] = role

        intx_data['pending_changes'] = []
        intx_data['made_changes'] = []

        # Authenticate User
        authenticated, auth_output = await role_auth.command_auth(intx_data,auth_command="/admin")

        # Check for Log channel in DB
        log_channel_id=log_channel_db.get_guild_log_channel_id(intx_data['intx'].guild.id)
        print(f"Log Channel ID: {log_channel_id}")
        if log_channel_id is None: # Force Log channel Selection
            # Get template embed
            intx_data['em'] = admin_main_menu.template_embed(intx_data)
            if authenticated:
                intx_data['em'].add_field(name="Admin functionality has not been set up.",value=f"A log channel is required for bot alerts.\nIt is recommended to use a restricted channel",inline=False)
                intx_data['descr']=f"Select a Log Channel"
                intx_data['target_func']=f"log_channel"
                await intx_data['intx'].response.send_message(embed=intx_data['em'],view=log_channel_config.entrypoint_view(self.client,intx_data))
                return
            else:
                intx_data['em'].add_field(name="Admin functionality has not been set up.",value=f"The server owner must run this command and perform setup",inline=False)
                intx_data['em'].set_footer(text = auth_output, icon_url = default_embed_footer['icon_url'])
                await intx_data['intx'].response.send_message(embed=intx_data['em'])
                return

        intx_data['log_channel']=interaction.guild.get_channel(log_channel_id)
        intx_data['em'] = admin_main_menu.template_embed(intx_data)

        if not authenticated:
            intx_data['em'] = nextcord.Embed(title="Admin",description="Failed Authentication!",color=nextcord.Colour.random())
            intx_data['em'].add_field(name="Auth Roles",value=f"```\n{auth_output}```",inline=False)
            await intx_data['intx'].response.send_message(embed=intx_data['em'])
            return

        await intx_data['intx'].response.send_message(embed=intx_data['em'],view=admin_main_menu.entrypoint_view(self.client,intx_data)) 

def setup(client):
    client.add_cog(admin(client))