import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import sys
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
    
from keys_and_codes import debug
from nft_modules import user_wallet
from database import nft_db

class wallet(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Events ----------------------------------------------------------------------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog Loaded : "+__file__)

    # Commands ---------------------------------------------------------------------------------------------------------------------------------

    @nextcord.slash_command(
        name="wallet",
        description="register your wallet Address or ENS"
    )
    
    async def wallet_command(
        self,
        interaction: Interaction,
        member: nextcord.Member = SlashOption(
            name="user",
            description="Show a user's wallets",
            required=False,
        )
    ): 
        if debug:
            print("Wallet command init begin")
        intx_data={}
        intx_data['guild_id'] = f"{interaction.guild.id}"
        intx_data['guild_name']=interaction.guild.name
        intx_data['user_id'] = f"{interaction.user.id}"
        intx_data['wallet_input'] = None
        intx_data['wallet_address']= None
        intx_data['wallet_note']= None
        intx_data['loopring_account']= None
        intx_data['selected_edit_wallet'] = None
        consoleOutput=f'/wallet - '
        intx_data['title']=f"Wallet"
        intx_data['descr']=f""
        ephemeral = False
        member_is_self = False
        intx_data['guild_member_id_name']={}
        for xmember in await interaction.guild.fetch_members().flatten():
            if not xmember.bot:
                intx_data['guild_member_id_name'][f"{xmember.id}"]=xmember.name
        intx_data['descr']=f"{interaction.user.name}'s wallet" # own wallet
        intx_data['user_wallets']=nft_db.get_user_wallets(intx_data['guild_id'],user_id=f"{interaction.user.id}")
        if debug:
            print("Wallet command init complete")
        if member:
            if interaction.user.id == member.id:
                member_is_self = True

            intx_data['descr']=f"{member.name}'s wallet" # own wallet
            consoleOutput=f'{consoleOutput} Targeted User {member}'
            intx_data['user_id']=f"{member.id}"

            intx_data['next_view']=None
            intx_data['user_wallets']=nft_db.get_user_wallets(intx_data['guild_id'],user_id=intx_data['user_id'])
            intx_data=user_wallet.init_template_wallet_embed(intx_data)

            if intx_data['user_wallets'] is None:
                intx_data['em'].add_field(name=f"{member.name} has no wallets registered",value="** **",inline=False)

        if not member or member_is_self:
            intx_data=user_wallet.init_template_wallet_embed(intx_data)
            intx_data['next_view']=None

            if intx_data['user_wallets'] is None:
                # send ephemeral setup
                intx_data['em'].add_field(name=f"{interaction.user.name}, You have no wallets registered",value=f"Would you like to add one now?",inline=False)
                intx_data['next_view']=user_wallet.wallet_add_or_cancel(self.client,intx_data)
                ephemeral = True
            else:
                intx_data['next_view']=user_wallet.wallet_edit_button(self.client,intx_data)
                ephemeral = True

        if intx_data['next_view'] is None:
            await interaction.response.send_message(embed=intx_data['em'])
        else:
            await interaction.response.send_message(embed=intx_data['em'],ephemeral=True,view=intx_data['next_view'])
                
        consoleOutput=f'{consoleOutput} No target User specified'

        print(consoleOutput)

def setup(client):
    client.add_cog(wallet(client))



