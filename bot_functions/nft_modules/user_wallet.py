import nextcord
import sys
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
import re

import requests
from database import nft_db

def init_template_wallet_embed(intx_data):
    intx_data['em']=nextcord.Embed(title=intx_data['title'], description=intx_data['descr'])
    if intx_data['user_wallets'] is not None:
        wallet_list_string=""
        noted_wallet=False
        for wallet_data in intx_data['user_wallets']:
            if wallet_data['wallet_note'] not in ['None','']:
                intx_data['em'].add_field(name=wallet_data['wallet_note'],value=f"```{wallet_data['wallet_input']}```",inline=False)
                noted_wallet=True    
            else:
                wallet_list_string=f"{wallet_list_string}{wallet_data['wallet_input']}\n"

        if len(wallet_list_string) != 0:
            if noted_wallet:
                embed_name="Other Wallets"
            else:
                embed_name="** **"
            intx_data['em'].add_field(name=embed_name,value=f"```\n{wallet_list_string}```",inline=False)
    return(intx_data)


# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Functions                                                *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
class wallet_add_or_cancel(nextcord.ui.View):

    def __init__(self,client,intx_data):
        super().__init__()
        self.client = client
        self.intx_data = intx_data
        print(f"__INIT__ wallet_add_or_cancel RUN - \nintx_data\n: {intx_data}")
        
    @nextcord.ui.button(label='Add', style=nextcord.ButtonStyle.green)
    async def timescale(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['operation']='add'
        modal=inputWalletAndNote(self.client,self.intx_data)
        await interaction.response.send_modal(modal)
        
    @nextcord.ui.button(label='Cancel', style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['em'].add_field(name="Cancelled",value="** **")
        await interaction.response.edit_message(embed=self.intx_data['em'], view=None, delete_after=5)
class wallet_edit_menu(nextcord.ui.View):
    
    def __init__(self,client,intx_data):
        super().__init__()
        self.client = client
        self.intx_data = intx_data
        print(f"__INIT__ wallet_edit_menu RUN - \nintx_data\n: {intx_data}")
        
    @nextcord.ui.button(label='Add', style=nextcord.ButtonStyle.green)
    async def add(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['operation']='add'
        self.intx_data['descr']=f"{self.intx_data['operation'].replace('_',' ').title()} Wallet"
        self.intx_data['em'] = nextcord.Embed(title=self.intx_data['title'],description=self.intx_data['descr'],color=nextcord.Colour.random())
        
        modal=inputWalletAndNote(self.client,self.intx_data)
        await interaction.response.send_modal(modal)
        
        
    @nextcord.ui.button(label='Remove', style=nextcord.ButtonStyle.red)
    async def remove(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        wallet_count=len(self.intx_data['user_wallets'])
        self.intx_data['next_view']=None
        self.intx_data['operation']='remove'
        self.intx_data['descr']=f"{self.intx_data['operation'].replace('_',' ').title()} Wallet"
        self.intx_data['em'] = nextcord.Embed(title=self.intx_data['title'],description=self.intx_data['descr'],color=nextcord.Colour.random())
                
        if wallet_count == 0: # nothing to remove
            self.intx_data['operation']=None
            self.intx_data['em'].add_field(name="Nothing to remove!",value="** **",inline=False)
            await interaction.response.edit_message(embed=self.intx_data['em'], view=wallet_edit_menu(self.client,self.intx_data) )
            
        elif wallet_count == 1: # one wallet, edit it
            self.intx_data['wallet_input']=self.intx_data['user_wallets'][0]['wallet_input']
            self.intx_data['next_view']=wallet_confirm_changes(self.client,self.intx_data)
        elif wallet_count > 1: # select a wallet to edit
            self.intx_data['em'].add_field(name="Select a wallet",value="** **",inline=False)
            self.intx_data['next_view']=wallet_dropdown_or_cancel(self.client,self.intx_data)
        
        await interaction.response.edit_message(embed=self.intx_data['em'], view=self.intx_data['next_view'])
        
        
    @nextcord.ui.button(label='Cancel', style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['em'].add_field(name="Cancelled",value="** **")
        await interaction.response.edit_message(embed=self.intx_data['em'], view=None, delete_after=5)
            
class wallet_edit_button(nextcord.ui.View):
    
    def __init__(self,client,intx_data):
        super().__init__()
        self.client = client
        self.intx_data = intx_data
        print(f"__INIT__ wallet_edit_button RUN - \nintx_data\n: {intx_data}")
        
    @nextcord.ui.button(label='Manage Saved Wallets', style=nextcord.ButtonStyle.blurple)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.edit_message(embed=self.intx_data['em'], view=wallet_edit_menu(self.client,self.intx_data) )
    
    @nextcord.ui.button(label='Cancel', style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['em'].add_field(name="Cancelled",value="** **")
        await interaction.response.edit_message(embed=self.intx_data['em'], view=None, delete_after=5)

class wallet_confirm_changes(nextcord.ui.View):
    
    def __init__(self,client,intx_data):
        super().__init__()
        self.client = client
        self.intx_data = intx_data
        print(f"__INIT__ wallet_confirm_changes RUN - \nintx_data\n: {intx_data}")
        
    @nextcord.ui.button(label='Confirm', style=nextcord.ButtonStyle.green)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if self.intx_data['operation'] in ['add','remove','edit']:
            outcome=nft_db.edit_user_wallet(self.intx_data)
            self.intx_data['user_wallets']=nft_db.get_user_wallets(self.intx_data['guild_id'],user_id=self.intx_data['user_id'])
            self.intx_data=init_template_wallet_embed(self.intx_data)
            self.intx_data['em'].add_field(name=outcome,value="** **",inline=False)
            await interaction.response.edit_message(embed=self.intx_data['em'],view=wallet_edit_menu(self.client,self.intx_data))
            
    @nextcord.ui.button(label='Cancel', style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['em'].add_field(name="Cancelled",value="** **")
        await interaction.response.edit_message(embed=self.intx_data['em'], view=None, delete_after=5)


class wallet_dropdown(nextcord.ui.Select):
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        print(f"\n__INIT__ wallet_dropdown\nintx_data:\n{intx_data}\n")

        options = []
        for wallet_data in intx_data['user_wallets']:
            options.append(nextcord.SelectOption(label=wallet_data['wallet_input'], description=" ", emoji=None),)

        super().__init__(placeholder=f"Select wallet...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        self.intx_data['em'] = nextcord.Embed(title=self.intx_data['title'],description=self.intx_data['descr'],color=nextcord.Colour.random())
        self.intx_data['wallet_input']=self.values[0]
        self.intx_data['em'].add_field(name="Selected Wallet",value=f"```{self.intx_data['wallet_input']}```")
        if self.intx_data['operation']=='remove':
            self.intx_data['em'].add_field(name=f"Confirm {self.intx_data['operation'].title()}?",value=f"** **",inline=False)
            self.intx_data['next_view']=wallet_confirm_changes(self.client,self.intx_data)
            await interaction.response.edit_message(embed=self.intx_data['em'], view=self.intx_data['next_view'])
        elif self.intx_data['operation']=='edit':
            self.intx_data['selected_edit_wallet']=self.values[0]
            modal=inputWalletAndNote(self.client,self.intx_data)
            await interaction.response.send_modal(modal)
            


class wallet_dropdown_or_cancel(nextcord.ui.View):
    def __init__(self,client,intx_data):
        super().__init__()
        self.add_item(wallet_dropdown(client,intx_data))

    @nextcord.ui.button(label='Cancel', style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['em'].add_field(name="Cancelled",value="** **")
        await interaction.response.edit_message(embed=self.intx_data['em'], view=None, delete_after=5)




# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#
#                                                                               Modals
#
# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


class inputWalletAndNote(nextcord.ui.Modal):
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        print(f"\n__INIT__ inputWalletAndNote\nintx_data:\n{intx_data}\n")
        
        super().__init__(
            self.intx_data['descr'],
            timeout=5 * 60,  # 5 minutes
        )
        
        default_wallet_input = ''
        default_note_input = ''
        if self.intx_data['operation'] == 'edit':
            default_wallet_input = intx_data['selected_edit_wallet']
            default_note_input = intx_data['user_wallets'][intx_data['selected_edit_wallet']]['note']

        self.wallet_input = nextcord.ui.TextInput(
            label="Wallet address or ENS",
            required=True,
            max_length=255,
            default_value=default_wallet_input
        )
        
        self.add_item(self.wallet_input)
        
        label="Wallet Note / Description (Optional)"

        self.wallet_note = nextcord.ui.TextInput(
            label=label,
            required=False,
            default_value=default_note_input,
            max_length=255
        )
        self.add_item(self.wallet_note)

    async def callback(self, interaction: nextcord.Interaction) -> None:        
        self.intx_data['wallet_input']=self.wallet_input.value
        self.intx_data['wallet_note']=self.wallet_note.value
        self.intx_data['em'] = nextcord.Embed(title=self.intx_data['title'],description=self.intx_data['descr'],color=nextcord.Colour.random())
        print(f"self.intx_data['wallet_input'] {type(self.intx_data['wallet_input'])}: {self.intx_data['wallet_input']}")
        self.intx_data['em'].add_field(name="Wallet Input",value=f"```{self.intx_data['wallet_input']}```",inline=False)
        if self.intx_data['wallet_note'] != '':
            self.intx_data['em'].add_field(name="Wallet Note",value=f"```{self.intx_data['wallet_note']}```",inline=False)
        self.intx_data['validation']=validate_wallet_input(self.intx_data)
        
        if self.intx_data['validation']['passed']:
            self.intx_data['em'].add_field(name=f"Confirm {self.intx_data['operation'].replace('_',' ').title() }?",value="** **",inline=False)
            self.intx_data['next_view'] = wallet_confirm_changes(self.client,self.intx_data)
        else:
            self.intx_data['user_wallets']=nft_db.get_user_wallets(self.intx_data['guild_id'],user_id=self.intx_data['user_id'])
            self.intx_data=init_template_wallet_embed(self.intx_data)
            self.intx_data['em'].add_field(name="Validation Failed",value=self.intx_data['validation']['fail_reason'],inline=False)
            
            self.intx_data['next_view'] =wallet_edit_menu(self.client,self.intx_data)
            
        await interaction.response.edit_message(embed=self.intx_data['em'], view=self.intx_data['next_view'])
        

def validate_wallet_input(intx_data, skip_embed=False):
    guild_registered_wallets=nft_db.get_user_wallets(intx_data['guild_id'], all_users=True)
    if guild_registered_wallets is None:
        guild_registered_wallets={}
    intx_data['validation']={}
    intx_data['validation']['passed']=True
    def wallet_already_registered(intx_data):
        wallet_owner_id = nft_db.get_wallet_owner_id(intx_data['guild_id'],intx_data['wallet_address'].lower())
        if wallet_owner_id is not None:
            intx_data['validation']['passed'] = False
            wallet_owner_mention=f"<@{wallet_owner_id}>"
            if wallet_owner_id != intx_data['user_id']:
                intx_data['validation']['fail_reason']=f"Wallet has already been registered by {wallet_owner_mention}"
            else:
                intx_data['validation']['fail_reason']=f"{wallet_owner_mention}, You have already registered this wallet"
        return(intx_data)

    if "." in intx_data['wallet_input']:
        re_search=re.search(r"([^\s]+\.[^\s]+)", intx_data['wallet_input'])
        print(f"re_search: {re_search}")
        if re_search:
            intx_data['wallet_input']=re_search.group(0).lower()
            if intx_data['validation']['passed']:
                url=f"https://api3.loopring.io/api/wallet/v3/resolveEns?fullName={intx_data['wallet_input']}"
                print(url)
                r = requests.get(url)
                
                if r.status_code != 200:
                    # ens did not resolve
                    intx_data['validation']['passed']=False
                    intx_data['validation']['fail_reason']=f"Could not resolve ENS to a wallet! \nStatus Code: `{r.status_code}`"
                elif 'data' not in r.json() or r.json()['data'] == "":
                    intx_data['validation']['passed']=False
                    print(r.json())
                    intx_data['validation']['fail_reason']=f"Could not resolve ENS `{intx_data['wallet_input']} `to a wallet!"
                else:
                    intx_data['wallet_address']=r.json()['data']
                    if not skip_embed:
                        intx_data['em'].add_field(name=f"ENS Resolved to:",value=f"```{intx_data['wallet_address']}```",inline=False)
        else:
            intx_data['validation']['passed']=False
            print(r.json())
            intx_data['validation']['fail_reason']=f"Could not find an ENS in your message!"
    else:
        # if input is an address is it valid?
        re_search=re.search(r"0x[0-9a-fA-F]+", intx_data['wallet_input'])
        print(f"re_search: {re_search}")
        if re_search:
            intx_data['wallet_input']=re_search.group(0).lower()
            if intx_data['validation']['passed']:
                intx_data['wallet_address'] = intx_data['wallet_input']
        else:
            intx_data['validation']['passed']=False
            intx_data['validation']['fail_reason']=f"Input is invalid!\nEnter an ENS or Wallet address only"
    if intx_data['validation']['passed']:
        intx_data = wallet_already_registered(intx_data)
    return(intx_data['validation'])
    
#  '{intx_data['guild_id']}'
#  '{intx_data['user_id']}'
#  '{intx_data['wallet_input']}'
#  '{intx_data['wallet_address']}'
#  '{intx_data['wallet_note']}'
#  '{intx_data['loopring_account']}'

