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
def get_range_str(min_str, max_str):
    if min_str != "-1" and max_str == "-1":
        return f"{min_str}+"
    elif min_str == "-1" and max_str != "-1":
        return f"0 - {max_str}"
    else:
        return f"{min_str} - {max_str}"

def get_roles_with_info(intx_data):
    guild_nft_roles = nft_db.get_nft_roles(intx_data['intx'].guild.id)
    for guild_nft_role in guild_nft_roles:
        range_str=get_range_str(guild_nft_role['quantity_min'], guild_nft_role['quantity_max'])
        guild_nft_role['role_list'] = []
        if guild_nft_role['target_type'] == "nft":
            target_dict = nft_db.get_pool_nft(guild_nft_role['guild_id'],guild_nft_role['target_id'])
            guild_nft_role['target_name'] = target_dict['nft_name']
            qual_str = f"{range_str} x '{guild_nft_role['target_name']}'"

        elif guild_nft_role['target_type'] == "pool":
            target_dict = nft_db.get_nft_pool(guild_nft_role['guild_id'],guild_nft_role['target_id'])
            guild_nft_role['target_name'] = target_dict['pool_name']
            qual_str = f"{range_str} NFTs in pool : {guild_nft_role['target_name']}"
        role_names = []
        for role_id in guild_nft_role['role_id_list']:
            for _,role in intx_data['guild_roles'].items():
                if str(role.id) == role_id:
                    guild_nft_role['role_list'].append(role)
                    role_names.append(role.name)
        role_list_str = "\n".join(str(name) for name in role_names)
        guild_nft_role['qual_message'] = qual_str
        guild_nft_role['role_message'] = role_list_str
    return guild_nft_roles

def template_embed(intx_data):
    em = nextcord.Embed(title=intx_data['title'],description=intx_data['descr'],color=nextcord.Colour.random())
    guild_nft_roles = get_roles_with_info(intx_data)

    table_rows = []
    for role in guild_nft_roles:
        table_rows.append([role['qual_message'],role['role_message'].replace("\n",", ")])
    table = tabulate(table_rows, headers=['Qualification','Roles'], tablefmt='fancy_outline')

    em_val = ''
    em_val_name = f'NFT Roles'
    for line in table.splitlines():
        new_val = f"{em_val}{line}\n"
        if len(new_val) > 1016:
            em.add_field(name=em_val_name, value=f"```\n{em_val}```", inline=False)
            em_val_name='** **'
            em_val = f"{line}\n"
        else:
            em_val = new_val
    em.add_field(name=em_val_name, value=f"```\n{em_val}```", inline=False)

    if 'embed_footer' in intx_data:
        embed_footer_text=intx_data['embed_footer']
    else:
        embed_footer_text=default_embed_footer['text']
    em.set_footer(text = embed_footer_text, icon_url = default_embed_footer['icon_url'])

    return(em)

def role_editor_embed(intx_data):
    title = intx_data['change']['type'].replace("_"," ").title().replace("Nft","NFT")
    em = nextcord.Embed(title=title,description=intx_data['descr'],color=nextcord.Colour.random())

    range_str = None
    target_name = None
    qual_str = None

    if intx_data['change']['edit_role']['quantity_min'] != intx_data['change']['edit_role']['quantity_max']: 
        # Quantities have been set
        min_str = str(intx_data['change']['edit_role']['quantity_min'])
        max_str = str(intx_data['change']['edit_role']['quantity_max'])

        range_str = get_range_str(min_str, max_str)

    if 'target_type' in intx_data['change']['edit_role']:
        # Target type has been set`
        target_type = intx_data['change']['edit_role']['target_type']
        if target_type == "nft":
            target_type = 'NFT '
            target_dict = nft_db.get_pool_nft(intx_data['intx'].guild.id,intx_data['change']['edit_role']['target_id'])
            target_name = target_dict['nft_name']

        elif target_type == "pool":
            target_type = 'Pool'
            target_dict = nft_db.get_nft_pool(intx_data['intx'].guild.id,intx_data['change']['edit_role']['target_id'])
            target_name = target_dict['pool_name']

    if target_name and not range_str:
        qual_str = target_name
    elif range_str and not target_name:
        qual_str = range_str
    elif target_name and range_str:
        qual_str = f"{target_type}     : {target_name}\nQuantity : {range_str}" # f"{range_str} {target_str}"

    if qual_str:
        em.add_field(name="Qualification",value=f"```\n{qual_str}```",inline=False)

    if 'role_message' in intx_data['change']['edit_role']:
        em.add_field(name="Grant Roles (Saved)",value=f"```\n{intx_data['change']['edit_role']['role_message']}```",inline=False)

    if 'selected_roles' in intx_data and intx_data['selected_roles'] is not None:
        role_names = []
        for role_name,role in intx_data['selected_roles'].items():
            if str(role.id) in intx_data['change']['edit_role']['role_id_list']:
                role_names.append(f"{role_name} (Removing)")
            else:
                if intx_data['change']['type'] == 'edit_nft_role':
                    role_names.append(f"{role_name} (Adding)")
                else:
                    role_names.append(role_name)
        roles_str = '\n'.join(role_names)
        em.add_field(name="Grant Roles",value=f"```\n{roles_str}```",inline=False)

    if intx_data['change']['type'] == 'create_nft_role':
        if intx_data['change']['edit_role']['target_type'] is None or intx_data['change']['edit_role']['target_id'] is None:
            em.add_field(name="Please Select Qualifying NFT or Pool",value=f"** **",inline=False) 
        elif intx_data['change']['edit_role']['quantity_min'] == intx_data['change']['edit_role']['quantity_max']:
            em.add_field(name="Please Set Required NFT Quantity",value=f"** **",inline=False)
        elif 'selected_roles' not in intx_data or intx_data['selected_roles'] is None:
            em.add_field(name="Please Select Role",value=f"** **",inline=False)
        else:
            em.add_field(name="Ready to Save",value=f"** **",inline=False)

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
                'role_id_list':[],
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
        await interaction.response.edit_message(embed=template_embed(self.intx_data), view=nft_role_dropdown(self.client,self.intx_data))

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def back(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        em = nft_main_menu.template_embed(self.intx_data)
        await interaction.response.edit_message(embed=em, view=nft_main_menu.entrypoint_view(self.client,self.intx_data))

class role_edit_view(nextcord.ui.View):

    def __init__(self,client,intx_data,deleteable=False):
        self.intx_data = intx_data
        self.client = client
        self.deleteable = deleteable
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

    @nextcord.ui.button(label='Roles', style=nextcord.ButtonStyle.blurple)
    async def role(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['role_id_list']=self.intx_data['change']['edit_role']['role_id_list']
        self.intx_data['intx']=interaction
        self.intx_data['em']=role_editor_embed(self.intx_data)
        await role_selection.guild_role_search_or_select(self.client,self.intx_data)
        
    @nextcord.ui.button(label='Save', style=nextcord.ButtonStyle.green)
    async def save_role(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        new_role_id_list = []
        existing_role_id_list = self.intx_data['change']['edit_role']['role_id_list']
        selected_role_id_list = []
        edit_role = self.intx_data['change']['edit_role']
        if 'selected_roles' in self.intx_data:
            for _,role in self.intx_data['selected_roles'].items():
                selected_role_id = str(role.id)
                selected_role_id_list.append(selected_role_id)
                if selected_role_id not in existing_role_id_list: # Removing role
                    new_role_id_list.append(selected_role_id)
        else:
            selected_role_id_list = []
        for role_id in existing_role_id_list:
            if role_id not in selected_role_id_list and role_id not in new_role_id_list: # Existing roles that were not selected
                new_role_id_list.append(role_id)

        edit_role['role_id_list']=new_role_id_list
        edit_role['guild_id']=str(interaction.guild.id)
        if self.intx_data['change']['type'] == 'create_nft_role':
            saveable = True
            if edit_role['target_type'] is None or edit_role['target_id'] is None:
                saveable = False
            elif edit_role['quantity_min'] == edit_role['quantity_max']:
                saveable = False
            elif 'selected_roles' not in self.intx_data or self.intx_data['selected_roles'] is None:
                saveable = False
            if not saveable:
                em = role_editor_embed(self.intx_data)
                em.add_field(name="Finish Role setup before saving!",value="** **",inline=False)
                await interaction.response.edit_message(embed=em, view=role_edit_view(self.client,self.intx_data))
                return

            success,output=nft_db.create_nft_role(role=edit_role)

        elif self.intx_data['change']['type'] == 'edit_nft_role':
            saved_role = nft_db.get_nft_role(edit_role['guild_id'],edit_role['id'])
            new_role_data = {}
            for key,og_value in saved_role.items():
                if edit_role[key] != og_value:
                    new_role_data[key]=edit_role[key]
            success,output=nft_db.edit_nft_role(str(edit_role['guild_id']),edit_role['id'],new_role_data)

        em=template_embed(self.intx_data)
        em_name=self.intx_data['change']['type'].replace("_"," ").title().replace("Nft","NFT")

        if success:
            output=f"Success !"
            emoji='✅'
            self.intx_data['selected_roles']=None
            self.intx_data['change']=None
        else:
            emoji='❌'

        em.add_field(name=em_name, value=f"{emoji} {output}", inline=False)
        await interaction.response.edit_message(embed=em, view=nft_main_menu.entrypoint_view(self.client,self.intx_data))

    @nextcord.ui.button(label='Delete', style=nextcord.ButtonStyle.red)
    async def delete(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        if not self.deleteable :
            em = role_editor_embed(self.intx_data)
            em.add_field(name="Are you sure you want to delete this NFT role?",value="Press Delete again to confirm.",inline=False)
            await interaction.response.edit_message(embed=em, view=role_edit_view(self.client,self.intx_data,deleteable=True))
            return
        success = True # If role is being created, there is nothing to delete
        if self.intx_data['change']['type'] == 'edit_nft_role':
            success,output=nft_db.delete_nft_role(str(self.intx_data['change']['edit_role']['guild_id']),self.intx_data['change']['edit_role']['id'])

        em = template_embed(self.intx_data)
        if success:
            output=f"NFT Role Deleted"
            emoji='✅'
            self.intx_data['selected_roles']=None
            self.intx_data['change']=None
        else:
            emoji='❌'
        em.add_field(name="** **", value=f"{emoji} {output}", inline=False)

        await interaction.response.edit_message(embed=em, view=nft_main_menu.entrypoint_view(self.client,self.intx_data))

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def back(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        em = nft_main_menu.template_embed(self.intx_data)
        await interaction.response.edit_message(embed=em, view=entrypoint_view(self.client,self.intx_data))

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
        await interaction.response.edit_message(embed=em, view=role_edit_view(self.client,self.intx_data))


class nft_role_dropdown_select(nextcord.ui.Select):
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client

        options = []
        self.guild_nft_roles = get_roles_with_info(intx_data)

        for guild_nft_role in self.guild_nft_roles:
            roles_str = guild_nft_role['role_message'].replace("\n",", ")
            options.append(nextcord.SelectOption(label=guild_nft_role['qual_message'], description=roles_str),)

        super().__init__(placeholder='Select NFT Role ...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        for guild_nft_role in self.guild_nft_roles:
            if guild_nft_role['qual_message'] == self.values[0]:
                self.intx_data['change']['edit_role']= guild_nft_role
        await interaction.response.edit_message(embed=role_editor_embed(self.intx_data), view=role_edit_view(self.client,self.intx_data))

class nft_role_dropdown(nextcord.ui.View):
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        super().__init__()
        self.add_item(nft_role_dropdown_select(self.client,intx_data))

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.edit_message(embed=template_embed(self.intx_data), view=entrypoint_view(self.client,self.intx_data))





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

