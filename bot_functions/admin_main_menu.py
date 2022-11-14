import nextcord
import sys
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
    
from keys_and_codes import default_embed_footer
# from admin_modules import bot_config_menu
import nft_main_menu
from database import nft_db

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Functions                                                *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
def template_embed(intx_data):
    intx_data['em'] = nextcord.Embed(title=intx_data['title'],description=intx_data['descr'],color=nextcord.Colour.random())
    if 'log_channel' in intx_data:
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

    @nextcord.ui.button(label='NFT', style=nextcord.ButtonStyle.blurple)
    async def nfts(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['title'] = "Admin - NFTs"
        self.intx_data['em'] = nft_main_menu.template_embed(self.intx_data)
        await interaction.response.edit_message(embed=self.intx_data['em'],view=nft_main_menu.entrypoint_view(self.client,self.intx_data))

    # @nextcord.ui.button(label='Bot', style=nextcord.ButtonStyle.blurple)
    # async def bots(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
    #     self.intx_data['title'] = "Admin - Bot Config"
    #     self.intx_data['em'] = bot_config_menu.template_embed(self.intx_data)
    #     await interaction.response.edit_message(embed=self.intx_data['em'],view=bot_config_menu.entrypoint_view(self.client,self.intx_data))

    @nextcord.ui.button(label='Exit', style=nextcord.ButtonStyle.grey)
    async def exit(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['em'] = nextcord.Embed(title=self.intx_data['title'],description=self.intx_data['descr'],color=nextcord.Colour.random())
        await interaction.response.edit_message(embed=self.intx_data['em'],view=None)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Modals                                                   *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *