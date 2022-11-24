import nextcord
import sys
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
    
from keys_and_codes import default_embed_footer
from admin_modules import command_config_menu, log_config_menu
import admin_main_menu
from database import nft_db

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Functions                                                *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
def template_embed(intx_data):
    intx_data['em'] = nextcord.Embed(title=intx_data['title'],description=intx_data['descr'],color=nextcord.Colour.random())
    intx_data['em'].add_field(name="What would you like to configure?", value=f"** **", inline=False)

    if 'embed_footer' in intx_data:
        embed_footer_text=intx_data['embed_footer']
    else:
        embed_footer_text=default_embed_footer['text']
    intx_data['em'].set_footer(text = embed_footer_text, icon_url = default_embed_footer['icon_url'])

    return(intx_data['em'])

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Views                                                    *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class entrypoint_view(nextcord.ui.View):

    def __init__(self,client,intx_data): 
        self.intx_data = intx_data
        self.client = client
        super().__init__() 

    @nextcord.ui.button(label='Commands', style=nextcord.ButtonStyle.blurple)
    async def cmds(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['title'] = "Admin - Bot Commands"
        self.intx_data['em'] = command_config_menu.template_embed(self.intx_data)
        await interaction.response.edit_message(embed=self.intx_data['em'],view=command_config_menu.entrypoint_view(self.client,self.intx_data))

    @nextcord.ui.button(label='Logs', style=nextcord.ButtonStyle.blurple)
    async def logs(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['title'] = "Admin - Bot Logs"
        self.intx_data['em'] = log_config_menu.template_embed(self.intx_data)
        await interaction.response.edit_message(embed=self.intx_data['em'],view=log_config_menu.entrypoint_view(self.client,self.intx_data))

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['em'] = admin_main_menu.template_embed(self.intx_data)
        await interaction.response.edit_message(embed=self.intx_data['em'], view=admin_main_menu.entrypoint_view(self.client,self.intx_data))
        

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Modals                                                   *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *