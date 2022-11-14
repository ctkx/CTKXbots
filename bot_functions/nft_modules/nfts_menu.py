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
# def change_summary(change):
#     if change['type'] == 'create_nft_pool':
#         return(f"Create NFT Pool: {change['nft_pool_input']}")
#     if change['type'] == 'edit_nft_pool':
#         return(f"Edit NFT Pool: {change['edit_pool_name']} to {change['nft_pool_input']}")
#     if change['type'] == 'delete_nft_pool':
#         return(f"Delete NFT Pool: {change['edit_pool_name']}")
def get_random_word():
    response = requests.get('https://random-word-api.herokuapp.com/word')
    return response.json()[0]

def create_new_bulk_import_sheet(pool_name):
    import_code=get_random_word()
    spreadsheet_name=f"CTKXBot Bulk NFT Import {import_code}"
    url,worksheet=sheets.create_spreadsheet(spreadsheet_name)
    url,worksheet=sheets.deploy_template('bulk_nft_import',url,{'import_code':import_code,'pool_name':pool_name})
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
        pools_table_rows.append([intx_data['target_nft_pool']['name'],intx_data['target_nft_pool']['unique_nfts'],intx_data['target_nft_pool']['nft_quantity']])
        em.add_field(name="Target Pool", value=f"```\n{tabulate(pools_table_rows,headers=['Pool Name','Unique NFTs','Quantity'],tablefmt='simple')}```",inline=False)

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

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def back(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        em = nft_main_menu.template_embed(self.intx_data)
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
    async def back(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        pass

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

        import_code,sheet_url=create_new_bulk_import_sheet(pool_name=self.intx_data['target_nft_pool']['name'])
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

# # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
# #                                      Modals                                                   *
# # * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *


class add_nft_modal(nextcord.ui.Modal):
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        super().__init__(
            "Add NFT",
            timeout=5 * 60,  # 5 minutes
        )

        if 'last_nft_name_input' in self.intx_data:
            nft_name_default_input=self.intx_data['last_nft_name_input']
            self.intx_data['last_nft_name_input']=''
        else:
            nft_name_default_input=''

        self.nft_name = nextcord.ui.TextInput(
            label="NFT Name",
            required=True,
            max_length=256,
            default_value=nft_name_default_input
        )
        self.add_item(self.nft_name)

        if 'last_nft_id_input' in self.intx_data:
            nft_id_default_input=self.intx_data['last_nft_id_input']
            self.intx_data['last_nft_id_input']=''
        else:
            nft_id_default_input=''

        self.nft_id = nextcord.ui.TextInput(
            label="NFT ID",
            required=True,
            max_length=256,
            default_value=nft_id_default_input
        )
        self.add_item(self.nft_id)

        if 'last_minter_address_input' in self.intx_data:
            minter_address_default_input=self.intx_data['last_minter_address_input']
        else:
            minter_address_default_input=''
            
        self.minter_address = nextcord.ui.TextInput(
            label="Minter Address",
            required=True,
            max_length=256,
            default_value=minter_address_default_input
        )
        self.add_item(self.minter_address)

        if 'last_token_address_input' in self.intx_data:
            token_address_default_input=self.intx_data['last_token_address_input']
            self.intx_data['last_token_address_input']=''
        else:
            token_address_default_input=''
            
        self.token_address = nextcord.ui.TextInput(
            label="Token Address",
            required=True,
            max_length=256,
            default_value=token_address_default_input
        )
        self.add_item(self.token_address)

        if 'last_quantity_input' in self.intx_data:
            quantity_default_input=self.intx_data['last_quantity_input']
            self.intx_data['last_quantity_input']=''
        else:
            quantity_default_input=''
            
        self.quantity = nextcord.ui.TextInput(
            label="Quantity",
            required=True,
            max_length=256,
            default_value=quantity_default_input
        )
        self.add_item(self.quantity)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        nft={}
        nft['name'] = self.nft_name.value
        nft['nft_id'] = self.nft_id.value
        nft['minter_address'] = self.minter_address.value
        nft['token_address'] = self.token_address.value
        nft['quantity'] = self.quantity.value
        self.intx_data['last_minter_address_input']=nft['minter_address']
        self.intx_data['em'] = nextcord.Embed(title=self.intx_data['title'],description=self.intx_data['descr'],color=nextcord.Colour.random())

        table_values=[]
        table_columns=[]
        table_row=[]

        nft_fields=['nft_id','minter_address','token_address','quantity']
        for field in nft_fields:
            field_name=field.replace('_',' ').title()
            if field_name not in table_columns:
                table_columns.append(field_name)

            table_row.append(nft[field])

        table_values.append(table_row)

        self.intx_data['em'].add_field(name=f"Last NFT: {nft['name']}",value=f"```\n{tabulate(table_values,headers=table_columns,tablefmt='plain')}```",inline=False)

        if nft['quantity'].isdecimal():
            validation_output = validate_nft(nft)
        else:
            validation_output = 'Failed! Quantity must be a number'
            self.intx_data['last_nft_name_input']=nft['name']
            self.intx_data['last_quantity_input']=nft['quantity']
            self.intx_data['last_nft_id_input']=nft['nft_id']
            self.intx_data['last_token_address_input']=nft['token_address']
        if 'input_nfts' not in self.intx_data:
            self.intx_data['input_nfts']={}
        if validation_output == "Passed":
            self.intx_data['input_nfts'][nft['name']]={}
            for field in nft_fields:
                self.intx_data['input_nfts'][nft['name']][field] = nft[field]
        else:
            self.intx_data['em'].add_field(name=validation_output,value=f"** **",inline=False)

        table_values=[]
        if len(self.intx_data['input_nfts']) > 0:
            table_columns=['Quantity','Name']
            input_nft_list_string=''
            for existing_nft_name,existing_nft in self.intx_data['input_nfts'].items():
                table_values.append([existing_nft['quantity'],existing_nft_name])
            self.intx_data['em'].add_field(name=f"Input NFTs",value=f"```\n{tabulate(table_values,headers=table_columns,tablefmt='plain')}```",inline=False)

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
            self.intx_data['input_nfts']={}
        for nft in nft_list:
            self.intx_data['input_nfts'][nft['name']]=nft
            unique_nft_count+=1
            nft_quantity+=int(nft['quantity'])
            table_values.append([nft['quantity'],nft['name']])
        test_table=tabulate(table_values,headers=['Quantity','Name'],tablefmt='plain')
        print(test_table)
        if len(test_table) > 1024:
            test_table=f"Too many NFTs to display!\n\n{unique_nft_count} unique NFTs\n{nft_quantity} total NFTs"
        self.intx_data['em'].add_field(name=f"Input NFTs",value=f"```\n{test_table}```",inline=False)
        await interaction.response.edit_message(embed=self.intx_data['em'], view=nft_input_again_or_finish_view(self.client,self.intx_data))