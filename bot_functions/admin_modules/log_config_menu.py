import nextcord
import sys
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
    
from keys_and_codes import default_embed_footer
from admin_modules import bot_config_menu
from database import log_channel_db
import channel_selection
import log_messages

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Functions                                                *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
def template_embed(intx_data):
    em = nextcord.Embed(title=intx_data['title'],description=intx_data['descr'],color=nextcord.Colour.random())

    if 'change' not in intx_data or intx_data['change'] is None:
        em.add_field(name="What would you like to configure?", value=f"** **", inline=False)
    elif 'selected_channels' not in intx_data or intx_data['selected_channels'] is None:
        em.add_field(name="Log Channel", value=f"{intx_data['log_channel'].name}", inline=False)
        
    else:
        channels = intx_data['selected_channels']
        channel_name = list(channels.keys())[0]
        log_channel = channels[channel_name]

        if intx_data['change']['type'] == 'edit_log_channel':
            em.add_field(name="Old Log Channel", value=f"{intx_data['log_channel'].name}", inline=False)
        em.add_field(name="New Log Channel", value=f"{log_channel.name}", inline=False)

    if 'embed_footer' in intx_data:
        embed_footer_text=intx_data['embed_footer']
    else:
        embed_footer_text=default_embed_footer['text']
    em.set_footer(text = embed_footer_text, icon_url = default_embed_footer['icon_url'])

    return(em)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Views                                                    *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
class admin_setup_view(nextcord.ui.View):
    def __init__(self,client,intx_data): 
        self.intx_data = intx_data
        self.client = client
        super().__init__() 

    @nextcord.ui.button(label='Setup Log Channel', style=nextcord.ButtonStyle.blurple)
    async def setup(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['change'] = {
            'type': 'create_log_channel',
        }
        self.intx_data['intx'] = interaction
        self.intx_data['em'] = template_embed(self.intx_data)
        await channel_selection.guild_channel_search_or_select(self.client,self.intx_data)

class entrypoint_view(nextcord.ui.View):

    def __init__(self,client,intx_data): 
        self.intx_data = intx_data
        self.client = client
        super().__init__() 

    @nextcord.ui.button(label='Channel', style=nextcord.ButtonStyle.blurple)
    async def logchannel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['change'] = {
            'type': 'edit_log_channel',
        }
        self.intx_data['intx'] = interaction
        self.intx_data['em'] = template_embed(self.intx_data)
        await channel_selection.guild_channel_search_or_select(self.client,self.intx_data)

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.em = bot_config_menu.template_embed(self.intx_data)
        await interaction.response.edit_message(embed=self.em, view=bot_config_menu.entrypoint_view(self.client,self.intx_data))

class confirm_changes_view(nextcord.ui.View):

    def __init__(self,client,intx_data): 
        self.intx_data = intx_data
        self.client = client
        super().__init__() 

    @nextcord.ui.button(label='Confirm', style=nextcord.ButtonStyle.green)
    async def logchannel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):

        channels = self.intx_data['selected_channels']
        channel_name = list(channels.keys())[0]
        log_channel = channels[channel_name]
        log_channel_id = str(log_channel.id)

        if self.intx_data['change']['type'] == 'create_log_channel':
            success,output=log_channel_db.save_log_channel(self.intx_data['intx'].guild.id,log_channel_id,init=True)
        elif self.intx_data['change']['type'] == 'edit_log_channel':
            success,output=log_channel_db.save_log_channel(self.intx_data['intx'].guild.id,log_channel_id,init=False)

        em = template_embed(self.intx_data)
        if success:
            output=f"Log channel saved!"
            emoji='✅'
            self.intx_data['selected_channels']=None
            self.intx_data['log_channel']=log_channel
            log_message={
                'title':"Log Channel Setup",
                'description':self.intx_data['intx'].guild.name,
                'fields' : {
                    'Channel': log_channel.name,
                }
            }
            await log_messages.send(self.intx_data,log_message)
        else:
            emoji='❌'
        em.add_field(name="** **", value=f"{emoji} {output}", inline=False)

        await interaction.response.edit_message(embed=em, view=entrypoint_view(self.client,self.intx_data))

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.em = bot_config_menu.template_embed(self.intx_data)
        await interaction.response.edit_message(embed=self.em, view=bot_config_menu.entrypoint_view(self.client,self.intx_data))
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Modals                                                   *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *