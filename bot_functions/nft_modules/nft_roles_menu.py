import nextcord
import sys
from tabulate import tabulate

if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
    
from keys_and_codes import default_embed_footer
import nft_main_menu
import role_selection
from nft_modules import nfts_menu,nft_pools_menu
from database import nft_db
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Functions                                                *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

def template_embed(intx_data):
    em = nextcord.Embed(title=intx_data['title'],description=intx_data['descr'],color=nextcord.Colour.random())


    if 'embed_footer' in intx_data:
        embed_footer_text=intx_data['embed_footer']
    else:
        embed_footer_text=default_embed_footer['text']
    em.set_footer(text = embed_footer_text, icon_url = default_embed_footer['icon_url'])

    return(em)

def role_editor_embed(intx_data):
    title = intx_data['change']['type'].replace("_"," ").title().replace("Nft","NFT")
    em = nextcord.Embed(title=title,description=intx_data['descr'],color=nextcord.Colour.random())
    print(intx_data)
    if 'target_type' in intx_data['change']['edit_role']:
        em.add_field(name="Target Type",value=f"```\n{intx_data['change']['edit_role']['target_type']}```",inline=False) 
    if 'target_id' in intx_data['change']:
        em.add_field(name="Target ID",value=f"```\n{intx_data['change']['edit_role']['target_id']}```",inline=False)

    if 'active_role_id_list' in intx_data['change']['edit_role']:
        em.add_field(name="Active Role ID List",value=f"```\n{intx_data['change']['edit_role']['active_role_id_list']}```",inline=False)

    for field in ['quantity_min','quantity_max']:
        if field in intx_data['change']['edit_role']:
            if intx_data['change']['edit_role'][field] == '-1':
                value = '-1 (No Limit)'
            else:
                value = intx_data['change']['edit_role'][field]
            em.add_field(name=field.replace("_"," ").title(),value=f"```\n{value}```",inline=False)

    if 'selected_roles' in intx_data:
        role_names = []
        for role_name,_ in intx_data['selected_roles'].items():
            role_names.append(role_name)
        roles_str = '\n'.join(role_names)
        em.add_field(name="Selected Roles",value=f"```\n{roles_str}```",inline=False)

    return(em)
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Views                                                    *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class entrypoint_view(nextcord.ui.View):
    
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        intx_data['nft_roles'] = nft_db.get_nft_roles(intx_data['intx'].guild.id)
        super().__init__() 

    @nextcord.ui.button(label='Create Role', style=nextcord.ButtonStyle.green)
    async def create(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['change'] = {
            'type': 'create_nft_role',
            'edit_role':{
                'active_role_id_list':[],
                'quantity_min':'-1',
                'quantity_max':'-1',
                'target_type':None,
                'target_id':None,
            }
        }
        # Send Role Name Modal
        await interaction.response.edit_message(embed=role_editor_embed(self.intx_data), view=role_edit_view(self.client,self.intx_data))


    @nextcord.ui.button(label='Edit Role', style=nextcord.ButtonStyle.blurple)
    async def edit(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['change'] = {
            'type': 'edit_nft_role',
        }
        self.intx_data['intx'] = interaction
        # await nft_role_search_or_select(self.client,self.intx_data)

    @nextcord.ui.button(label='Delete Role', style=nextcord.ButtonStyle.red)
    async def delete(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['change'] = {
            'type': 'delete_nft_role',
        }
        self.intx_data['intx'] = interaction
        # await nft_role_search_or_select(self.client,self.intx_data)

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def back(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        em = nft_main_menu.template_embed(self.intx_data)
        await interaction.response.edit_message(embed=em, view=nft_main_menu.entrypoint_view(self.client,self.intx_data))

class role_edit_view(nextcord.ui.View):

    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        intx_data['nft_roles'] = nft_db.get_nft_roles(intx_data['intx'].guild.id)
        super().__init__() 

    @nextcord.ui.button(label='Qualifying NFTs', style=nextcord.ButtonStyle.blurple)
    async def qual_nft(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        em = role_editor_embed(self.intx_data)
        em.add_field(name="How should the role be granted?",value="If user owns:\n - A specific **NFT**\n - any NFT in a **Pool**",inline=False)
        await interaction.response.edit_message(embed=em, view=role_target_type_view(self.client,self.intx_data))

    @nextcord.ui.button(label='Required Quantity', style=nextcord.ButtonStyle.blurple)
    async def req_quant(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.send_modal(role_quantity_modal(self.client,self.intx_data))

    @nextcord.ui.button(label='Role', style=nextcord.ButtonStyle.blurple)
    async def role(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['forward_view']=role_edit_view(self.client,self.intx_data)
        self.intx_data['back_view']=role_edit_view(self.client,self.intx_data)
        self.intx_data['active_role_id_list']=self.intx_data['change']['edit_role']['active_role_id_list']
        self.intx_data['intx']=interaction
        self.intx_data['em']=role_editor_embed(self.intx_data)
        await role_selection.guild_role_search_or_select(self.client,self.intx_data)

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def back(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        em = nft_main_menu.template_embed(self.intx_data)
        await interaction.respconse.edit_message(embed=em, view=entrypoint_view(self.client,self.intx_data))

class role_target_type_view(nextcord.ui.View):
    
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        intx_data['nft_roles'] = nft_db.get_nft_roles(intx_data['intx'].guild.id)
        super().__init__() 

    @nextcord.ui.button(label='NFT', style=nextcord.ButtonStyle.blurple)
    async def nft(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['change']['edit_role']['target_type'] = 'nft'
        self.intx_data['intx'] = interaction
        await nft_pools_menu.nft_pool_search_or_select(self.client,self.intx_data)
        # await interaction.response.edit_message(embed=role_editor_embed(self.intx_data), view=role_edit_view(self.client,self.intx_data))

    @nextcord.ui.button(label='Pool', style=nextcord.ButtonStyle.blurple)
    async def pool(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['change']['edit_role']['target_type'] = 'pool'
        self.intx_data['intx'] = interaction
        await nft_pools_menu.nft_pool_search_or_select(self.client,self.intx_data)
        # await interaction.response.edit_message(embed=role_editor_embed(self.intx_data), view=role_edit_view(self.client,self.intx_data))

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def back(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        em = nft_main_menu.template_embed(self.intx_data)
        await interaction.response.edit_message(embed=em, view=entrypoint_view(self.client,self.intx_data))

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Modals                                                   *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class role_quantity_modal(nextcord.ui.Modal):
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client

        super().__init__(
            "NFT Role Quantity",
            timeout=5 * 60,  # 5 minutes
        )

        self.role_quantity_min = nextcord.ui.TextInput(
            label="Quantity Min",
            min_length=1,
            max_length=8,
            default_value="-1",
        )
        self.add_item(self.role_quantity_min)

        self.role_quantity_max = nextcord.ui.TextInput(
            label="Quantity Max",
            min_length=1,
            max_length=8,
            default_value="-1",
        )
        self.add_item(self.role_quantity_max)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        self.intx_data['change']['edit_role']['quantity_min']=self.role_quantity_min.value
        self.intx_data['change']['edit_role']['quantity_max']=self.role_quantity_max.value
        await interaction.response.edit_message(embed=role_editor_embed(self.intx_data), view=role_edit_view(self.client,self.intx_data))

