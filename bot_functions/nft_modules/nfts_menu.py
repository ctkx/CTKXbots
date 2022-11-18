import nextcord
import sys
from tabulate import tabulate
import re
import requests
import gspread

if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")

from keys_and_codes import default_embed_footer
import nft_main_menu
from database import nft_db
from google import sheets
# # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
# #                                      Functions                                                *
# # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

def get_random_word():
    response = requests.get('https://random-word-api.herokuapp.com/word')
    return response.json()[0]

def create_new_bulk_import_sheet(nft_name):
    import_code=get_random_word()
    spreadsheet_name=f"CTKXBot Bulk NFT Import {import_code}"
    url,worksheet=sheets.create_spreadsheet(spreadsheet_name)
    url,worksheet=sheets.deploy_template('bulk_nft_import',url,import_code)
    return import_code,url

def validate_nft(nft):
    validation_fail_reason=False

    # Valid addresses check
    def is_address(input_address):
        pattern = re.compile("0x[0-9a-fA-F]+")
        if pattern.match(input_address):
            return True
        else:
            return False

    for address_type in ['nft_id','minter_address','token_address']:
        if nft[address_type] is not None:
            if not is_address(nft[address_type]):
                validation_fail_reason=f"Invalid {address_type}"

    if not validation_fail_reason:
        return "Passed"
    else:
        return f"Failed! {validation_fail_reason}"


def template_embed(intx_data,pool_stats=True):
    if 'nft_pools' not in intx_data:
        intx_data['nft_pools'] = nft_db.get_nft_pools(intx_data['intx'].guild.id)

    em = nextcord.Embed(title=intx_data['title'],description=intx_data['descr'],color=nextcord.Colour.random())

    if pool_stats:
        pools_table_rows=[]
        intx_data['target_nft_pool']['nft_list'],intx_data['target_nft_pool']['nft_quantity'],intx_data['target_nft_pool']['unique_nfts'] = nft_db.get_pool_nfts(intx_data['intx'].guild.id,intx_data['target_nft_pool']['id'])
        em.add_field(name="Target Pool",value=f"```\n{intx_data['target_nft_pool']['name']}```",inline=True)
        em.add_field(name="NFT Count",value=f"```\n{intx_data['target_nft_pool']['unique_nfts']}```",inline=True)
        em.add_field(name="Total Quantity",value=f"```\n{intx_data['target_nft_pool']['nft_quantity']}```",inline=True)


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
        super().__init__() 

    @nextcord.ui.button(label='Add NFTs to Pool', style=nextcord.ButtonStyle.green)
    async def create(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['change'] = {
            'type': 'add_nft',
        }
        em=template_embed(self.intx_data)
        await interaction.response.edit_message(embed=em, view=nft_input_again_or_finish_view(self.client,self.intx_data))

    @nextcord.ui.button(label='Edit NFT', style=nextcord.ButtonStyle.grey)
    async def edit(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['intx']=interaction
        self.intx_data['change'] = {
            'type': 'edit_nft',
        }
        em=template_embed(self.intx_data)
        # get nfts in pool
        self.intx_data['target_nft_pool']['nft_list'],self.intx_data['target_nft_pool']['nft_quantity'],self.intx_data['target_nft_pool']['unique_nfts'] = nft_db.get_pool_nfts(self.intx_data['intx'].guild.id,self.intx_data['target_nft_pool']['id'])

        if len(self.intx_data['nft_pools']) == 0: # If there are no nfts
            em.add_field(name="No NFTs Found!", value="Please add some NFTs first.", inline=False)
            await self.intx_data['intx'].response.edit_message(embed=em, view=entrypoint_view(self.client,self.intx_data))
            return
        elif 1<= len(self.intx_data['target_nft_pool']['nft_list']) <= 25: # Select Pool
            em.add_field(name="Select an NFT", value="** **", inline=False)
            await self.intx_data['intx'].response.edit_message(embed=em, view=pool_nft_dropdown(self.client,self.intx_data)) 
            return
        elif len(self.intx_data['target_nft_pool']['nft_list']) > 25:
            # Maximum elements in a select menu is 25, send nft_name modal and search
            await self.intx_data['intx'].response.send_modal(nft_name_search_modal(self.client,self.intx_data))
            return
        
    @nextcord.ui.button(label='Delete NFT', style=nextcord.ButtonStyle.grey)
    async def delete(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['change'] = {
            'type': 'delete_nft',
        }
        self.intx_data['intx']=interaction
        em=template_embed(self.intx_data)
        # get nfts in pool
        self.intx_data['target_nft_pool']['nft_list'],self.intx_data['target_nft_pool']['nft_quantity'],self.intx_data['target_nft_pool']['unique_nfts'] = nft_db.get_pool_nfts(self.intx_data['intx'].guild.id,self.intx_data['target_nft_pool']['id'])

        if len(self.intx_data['nft_pools']) == 0: # If there are no nfts
            em.add_field(name="No NFTs Found!", value="Please add some NFTs first.", inline=False)
            await self.intx_data['intx'].response.edit_message(embed=em, view=entrypoint_view(self.client,self.intx_data))
            return
        elif 1<= len(self.intx_data['target_nft_pool']['nft_list']) <= 25: # Select Pool
            em.add_field(name="Select an NFT", value="** **", inline=False)
            await self.intx_data['intx'].response.edit_message(embed=em, view=pool_nft_dropdown(self.client,self.intx_data)) 
            return
        elif len(self.intx_data['target_nft_pool']['nft_list']) > 25:
            # Maximum elements in a select menu is 25, send nft_name modal and search
            await self.intx_data['intx'].response.send_modal(nft_name_search_modal(self.client,self.intx_data))
            return

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def back(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        em = nft_main_menu.template_embed(self.intx_data)
        await interaction.response.edit_message(embed=em, view=nft_main_menu.entrypoint_view(self.client,self.intx_data))

class nft_edit_confirm_view(nextcord.ui.View):

    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        super().__init__() 


    @nextcord.ui.button(label='Save', style=nextcord.ButtonStyle.green)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        success,output=False,None
        if 'change' not in self.intx_data:
            output="No change requested!"

        elif self.intx_data['change']['type'] == 'edit_nft':
            success,output = nft_db.edit_pool_nft(self.intx_data['intx'].guild.id,self.intx_data['change']['nft'])
            if success:
                output=f"NFT Edit Saved!"
        elif self.intx_data['change']['type'] == 'delete_nft':
            success,output = nft_db.delete_pool_nft(self.intx_data['intx'].guild.id,self.intx_data['change']['nft'])
            if success:
                output=f"NFT Deleted!"


        if success:
            emoji='✅'
        else:
            emoji='❌'
        self.intx_data['change']=None
        em=template_embed(self.intx_data)
        em.add_field(name="Change Outcome", value=f"{emoji} {output}", inline=False)
        await interaction.response.edit_message(embed=em, view=entrypoint_view(self.client,self.intx_data))

    @nextcord.ui.button(label='Cancel', style=nextcord.ButtonStyle.red)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        em = nft_main_menu.template_embed(self.intx_data)
        self.intx_data['change'] = None
        await interaction.response.edit_message(embed=em, view=nft_main_menu.entrypoint_view(self.client,self.intx_data))

class nft_input_again_or_finish_view(nextcord.ui.View):
    
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        super().__init__() 

    @nextcord.ui.button(label='Input NFT', style=nextcord.ButtonStyle.green)
    async def create(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(add_nft_modal(self.client,self.intx_data))

    @nextcord.ui.button(label='Bulk Import', style=nextcord.ButtonStyle.blurple)
    async def bulk_import(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        em = template_embed(self.intx_data)
        await interaction.response.edit_message(embed=em, view=bulk_import_view(self.client,self.intx_data))

    @nextcord.ui.button(label='Save NFTs', style=nextcord.ButtonStyle.green)
    async def save_nfts(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if self.intx_data['change']['type'] == 'add_nft':
            success,output=nft_db.add_nfts_to_pool(self.intx_data['intx'].guild.id,self.intx_data['target_nft_pool']['id'],self.intx_data['input_nfts'])
            if success:
                output=f"{len(self.intx_data['input_nfts'])} NFTs added to {self.intx_data['target_nft_pool']['name']}!"
                
        if success:
            emoji='✅'
        else:
            emoji='❌'
        self.intx_data['change']=None
        em=template_embed(self.intx_data)
        em.add_field(name="Save NFTs", value=f"{emoji} {output}", inline=False)
        await interaction.response.edit_message(embed=em, view=nft_main_menu.entrypoint_view(self.client,self.intx_data))
        
    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def back(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        em = nft_main_menu.template_embed(self.intx_data)
        await interaction.response.edit_message(embed=em, view=nft_main_menu.entrypoint_view(self.client,self.intx_data))

class bulk_import_view(nextcord.ui.View):
    
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        super().__init__() 

    @nextcord.ui.button(label='Create New Import Sheet', style=nextcord.ButtonStyle.blurple)
    async def create(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.channel.send("Creating bulk import sheet...",delete_after=10)
        self.intx_data['em'] = nextcord.Embed(title=self.intx_data['title'],description=self.intx_data['descr'],color=nextcord.Colour.random())
        await interaction.response.defer(ephemeral=False, with_message=False) 

        import_code,sheet_url=create_new_bulk_import_sheet(nft_name=self.intx_data['target_nft_pool']['name'])
        nft_db.add_bulk_import_sheet(self.intx_data['intx'].guild.id,import_code,sheet_url)

        await interaction.channel.send(sheet_url)#,delete_after=10)
        message=f"Your import code is ```\n{import_code}```\n**Please fill out that sheet with your NFTs and then use the 'Import Sheet' Option in the Bulk Import Menu.**"
        self.intx_data['em'].add_field(name="New sheet created!", value=message, inline=False)

        await interaction.edit_original_message(embed=self.intx_data['em'], view=None) # Can't return to menus now because we can't use modals after deferring a response

    @nextcord.ui.button(label='Import NFTs from Sheet', style=nextcord.ButtonStyle.green)
    async def bulkimport(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['operation']='add_nft'
        await interaction.response.send_modal(import_nfts_from_code_input(self.client,self.intx_data))

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['em'] = template_embed(self.intx_data)
        await interaction.response.edit_message(embed=self.intx_data['em'], view=nft_input_again_or_finish_view(self.client,self.intx_data))

class pool_nft_dropdown_select(nextcord.ui.Select):
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client

        options = []

        if 'nft_name_search_results' in self.intx_data:
            nft_list = self.intx_data['nft_name_search_results']
        else:
            nft_list = self.intx_data['target_nft_pool']['nft_list']

        for nft in nft_list:
            options.append(nextcord.SelectOption(label=nft['nft_name'], description=f"", emoji=None),)

        super().__init__(placeholder='Select an NFT ...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        em = template_embed(self.intx_data)
        nft_name = self.values[0]

        for nft in self.intx_data['target_nft_pool']['nft_list']:
            if nft_name == nft['nft_name']:
                self.intx_data['change']['nft'] = nft
                break
        if self.intx_data['change']['type'] == 'edit_nft':
            await interaction.response.send_modal(add_nft_modal(self.client,self.intx_data))
        elif self.intx_data['change']['type'] == 'delete_nft':
            await interaction.response.edit_message(embed=self.intx_data['em'], view=nft_edit_confirm_view(self.client,self.intx_data))
            

# Define a simple View that gives us a counter button
class pool_nft_dropdown(nextcord.ui.View):
    # Discord disabled selects in modals, we'll use a view for now TODO
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        super().__init__()
        self.add_item(pool_nft_dropdown_select(self.client,intx_data))

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        em = template_embed(self.intx_data)
        await interaction.response.edit_message(embed=em, view=nft_main_menu.entrypoint_view(self.client,self.intx_data))


# # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
# #                                      Modals                                                   *
# # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *


class nft_name_search_modal(nextcord.ui.Modal):
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client

        super().__init__(
            "NFT Search",
            timeout=5 * 60,  # 5 minutes
        )

        self.nft_name_input = nextcord.ui.TextInput(
            label="Name",
            min_length=2,
            max_length=50,
        )
        self.add_item(self.nft_name_input)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        em = template_embed(self.intx_data)

        self.intx_data['nft_name_search_results'] = []
        search_string = self.nft_name_input.value.lower().replace(' ','')
        for nft in self.intx_data['target_nft_pool']['nft_list']:
            print(nft)
            if search_string in nft['nft_name'].lower().replace(' ',''):
                self.intx_data['nft_name_search_results'].append(nft)
        if len(self.intx_data['nft_name_search_results']) == 0:
            em.add_field(name=f"No NFTs found!", value=f"Searched: {self.nft_pool.value}", inline=False)
            em = template_embed(self.intx_data)
            await interaction.response.edit_message(embed=em, view=entrypoint_view(self.client,self.intx_data))
            return
        em.add_field(name="Select an NFT", value="** **", inline=False)
        await interaction.response.edit_message(embed=em, view=pool_nft_dropdown(self.client,self.intx_data)) 
        return

class add_nft_modal(nextcord.ui.Modal):
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        self.edit = False

        if 'change' in self.intx_data and self.intx_data['change']['type'] == 'edit_nft':
            self.nft_name_default_input       = self.intx_data['change']['nft']['nft_name']
            self.nft_id_default_input         = self.intx_data['change']['nft']['nft_id']
            self.minter_address_default_input = self.intx_data['change']['nft']['minter_address']
            self.token_address_default_input  = self.intx_data['change']['nft']['token_address']
            self.quantity_default_input       = self.intx_data['change']['nft']['quantity']
            self.edit=True
        else:
            self.nft_name_default_input=''
            self.nft_id_default_input=''
            self.minter_address_default_input=''
            self.token_address_default_input=''
            self.quantity_default_input=''
        super().__init__(
            "Add NFT",
            timeout=5 * 60,  # 5 minutes
        )
        self.nft_name = nextcord.ui.TextInput(
            label="NFT Name",
            required=True,
            max_length=256,
            default_value=self.nft_name_default_input
        )
        self.add_item(self.nft_name)

        self.nft_id = nextcord.ui.TextInput(
            label="NFT ID",
            required=True,
            max_length=256,
            default_value=self.nft_id_default_input
        )
        self.add_item(self.nft_id)

        self.minter_address = nextcord.ui.TextInput(
            label="Minter Address",
            required=True,
            max_length=256,
            default_value=self.minter_address_default_input
        )
        self.add_item(self.minter_address)

        self.token_address = nextcord.ui.TextInput(
            label="Token Address",
            required=True,
            max_length=256,
            default_value=self.token_address_default_input
        )
        self.add_item(self.token_address)

        self.quantity = nextcord.ui.TextInput(
            label="Quantity",
            required=True,
            max_length=256,
            default_value=self.quantity_default_input
        )
        self.add_item(self.quantity)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        nft={}
        nft['nft_name'] = self.nft_name.value
        nft['nft_id'] = self.nft_id.value
        nft['minter_address'] = self.minter_address.value
        nft['token_address'] = self.token_address.value
        nft['quantity'] = self.quantity.value
        self.intx_data['last_minter_address_input']=nft['minter_address']
        self.intx_data['em'] = nextcord.Embed(title=self.intx_data['title'],description=self.intx_data['descr'],color=nextcord.Colour.random())
        if self.edit:
            changes = []
            if self.nft_name_default_input != nft['nft_name']:
                changes.append(f"Name: {self.nft_name_default_input} -> {nft['nft_name']}")
            if self.nft_id_default_input != nft['nft_id']:
                changes.append(f"ID: {self.nft_id_default_input} -> {nft['nft_id']}")
            if self.minter_address_default_input != nft['minter_address']:
                changes.append(f"Minter Address: {self.minter_address_default_input} -> {nft['minter_address']}")
            if self.token_address_default_input != nft['token_address']:
                changes.append(f"Token Address: {self.token_address_default_input} -> {nft['token_address']}")
            if self.quantity_default_input != nft['quantity']:
                changes.append(f"Quantity: {self.quantity_default_input} -> {nft['quantity']}")
            changes = '\n'.join(changes)
            self.intx_data['em'].add_field(name=f"Edit NFT: {self.nft_name_default_input}",value=f"```\n{changes}```",inline=False)
        else:
            self.intx_data['em'].add_field(name="Last NFT Input",value=f"```\n" + \
                                    f"Name           : {nft['nft_name']}\n" + \
                                    f"NFT ID         : {nft['nft_id']}\n" + \
                                    f"Minter Address : {nft['minter_address']}\n" + \
                                    f"Token Address  : {nft['token_address']}\n" + \
                                    f"Quantity       : {nft['quantity']}\n```",inline=False)
        if nft['quantity'].isdecimal():
            validation_output = validate_nft(nft)
        else:
            validation_output = 'Failed! Quantity must be a number'
            self.intx_data['last_nft_name_input']=nft['nft_name']
            self.intx_data['last_quantity_input']=nft['quantity']
            self.intx_data['last_nft_id_input']=nft['nft_id']
            self.intx_data['last_token_address_input']=nft['token_address']

        if 'input_nfts' not in self.intx_data:
            self.intx_data['input_nfts']=[]
        if validation_output == "Passed":
            if self.edit:
                for key,val in nft.items():
                    self.intx_data['change']['nft'][key]=val
            else:
                self.intx_data['input_nfts'].append(nft)
        else:
            self.intx_data['em'].add_field(name=validation_output,value=f"** **",inline=False)

        if self.edit:
            await interaction.response.edit_message(embed=self.intx_data['em'], view=nft_edit_confirm_view(self.client,self.intx_data))
            return
        
        unique_nft_count=0
        nft_quantity=0
        table_values=[]
        table=None
        for nft in self.intx_data['input_nfts']:
            print(nft)
            unique_nft_count+=1
            nft_quantity+=int(nft['quantity'])
            table_values.append([nft['quantity'],nft['nft_name']])
            table=tabulate(table_values,headers=['Quantity','Name'],tablefmt='plain')
        if len(table) > 1016:
            table=f"Too many NFTs to display!\n\n{unique_nft_count} unique NFTs\n{nft_quantity} total NFTs"
        self.intx_data['em'].add_field(name=f"Input NFTs",value=f"```\n{table}```",inline=False)
        await interaction.response.edit_message(embed=self.intx_data['em'], view=nft_input_again_or_finish_view(self.client,self.intx_data))

class import_nfts_from_code_input(nextcord.ui.Modal):
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client

        super().__init__(
            "Bulk NFT Import",
            timeout=5 * 60,  # 5 minutes
        )

        self.import_code= nextcord.ui.TextInput(
            label="Import Code",
            required=True,
            max_length=256
        )
        self.add_item(self.import_code)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        import_code=None
        sheet_url=None
        for import_sheet in nft_db.get_bulk_import_sheets(self.intx_data['intx'].guild.id):
            if import_sheet['import_code'] == self.import_code.value:
                import_code=import_sheet['import_code']
                sheet_url=import_sheet['sheet_url']
                break
        nft_list=sheets.load_spreadsheet_as_dict_list(sheet_url,worksheet_name='Master',header_row=2)
        table_values=[]
        unique_nft_count=0
        nft_quantity=0
        if 'input_nfts' not in self.intx_data:
            self.intx_data['input_nfts']=[]
        for nft in nft_list:
            self.intx_data['input_nfts'].append(nft)
            unique_nft_count+=1
            nft_quantity+=int(nft['quantity'])
            table_values.append([nft['quantity'],nft['nft_name']])
        test_table=tabulate(table_values,headers=['Quantity','Name'],tablefmt='plain')
        print(test_table)
        if len(test_table) > 1024:
            test_table=f"Too many NFTs to display!\n\n{unique_nft_count} unique NFTs\n{nft_quantity} total NFTs"
        self.intx_data['em'].add_field(name=f"Input NFTs",value=f"```\n{test_table}```",inline=False)
        await interaction.response.edit_message(embed=self.intx_data['em'], view=nft_input_again_or_finish_view(self.client,self.intx_data))