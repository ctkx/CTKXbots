import nextcord
import sys
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
    
from keys_and_codes import default_embed_footer
import admin_main_menu
from database import nft_db
from nft_modules import nft_pools_menu,nfts_menu # nft_roles,nft_pools,nfts,bot_wallet

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Functions                                                *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
def template_embed(intx_data):
    em = nextcord.Embed(title=intx_data['title'],description=intx_data['descr'],color=nextcord.Colour.random())
    em.add_field(name="What would you like to configure?", value="** **", inline=False)

    if 'embed_footer' in intx_data:
        embed_footer_text=intx_data['embed_footer']
    else:
        embed_footer_text=default_embed_footer['text']
    em.set_footer(text = embed_footer_text, icon_url = default_embed_footer['icon_url'])

    return(em)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Views                                                    *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class entrypoint_view(nextcord.ui.View):

    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        intx_data['nft_pools'] = nft_db.get_nft_pools(intx_data['intx'].guild.id)
        super().__init__() 

    @nextcord.ui.button(label='NFTs', style=nextcord.ButtonStyle.blurple)
    async def nfts(self, button: nextcord.ui.Button, interaction: nextcord.Interaction): 
        if len(self.intx_data['nft_pools']) == 0: # If there are no nft pools, then we can't add nfts
            em = template_embed(self.intx_data)
            em.add_field(name="No NFT Pools Found!", value="Please create an NFT Pool first.", inline=False)
            await interaction.response.edit_message(embed=em, view=entrypoint_view(self.client,self.intx_data))
            return
        self.intx_data['next_view']='nfts_menu'
        self.intx_data['intx']=interaction
        await nft_pools_menu.nft_pool_search_or_select(self.client,self.intx_data)
    @nextcord.ui.button(label='NFT Pools', style=nextcord.ButtonStyle.blurple)
    async def nftpools(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        # Send NFT pools menu
        em = nft_pools_menu.template_embed(self.intx_data)
        em.add_field(name="What would you like to configure?", value="** **", inline=False)
        await interaction.response.edit_message(embed=em, view=nft_pools_menu.entrypoint_view(self.client,self.intx_data))

    @nextcord.ui.button(label='NFT Roles', style=nextcord.ButtonStyle.blurple)
    async def nftroles(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if len(self.intx_data['nft_pools']) == 0: # If there are no nft pools, then we can't add roles
            em = template_embed(self.intx_data)
            em.add_field(name="No NFT Pools Found!", value="Please create an NFT Pool first.", inline=False)
            await interaction.response.edit_message(embed=em, view=entrypoint_view(self.client,self.intx_data))
            return

    @nextcord.ui.button(label='Wallets', style=nextcord.ButtonStyle.blurple)
    async def wallets(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        # Send Wallets menu
        pass

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['em'] = admin_main_menu.template_embed(self.intx_data)
        await interaction.response.edit_message(embed=self.intx_data['em'], view=admin_main_menu.entrypoint_view(self.client,self.intx_data))
        
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Modals                                                   *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *