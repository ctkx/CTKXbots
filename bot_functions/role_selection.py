import nextcord
import sys
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")

from keys_and_codes import default_embed_footer
from nft_modules import nft_roles_menu
from admin_modules import command_config_menu
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Functions                                                *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

async def go_to_next_view(client,intx_data,extra_field=None):
    if 'change' in intx_data:
        if 'nft_role' in intx_data['change']['type'] :
            em = nft_roles_menu.role_editor_embed(intx_data)
            if extra_field:
                em.add_field(name=extra_field['name'], value=extra_field['value'], inline=False)
            await intx_data['intx'].response.edit_message(embed=em, view=nft_roles_menu.role_edit_view(client,intx_data))
            return
        elif intx_data['change']['type'] == 'command_auth_role':
            em = command_config_menu.command_auth_role_embed(intx_data)
            if extra_field:
                em.add_field(name=extra_field['name'], value=extra_field['value'], inline=False)
            await intx_data['intx'].response.edit_message(embed=em, view=command_config_menu.auth_role_confirm(client,intx_data))
            return

async def guild_role_search_or_select(client,intx_data):
    # Select or Search Roles
    if len(intx_data['guild_roles']) == 0: # If there are no Roles
        go_to_next_view(client,intx_data,extra_field={'name':'No Roles Found!','value':'Please create some roles first.'})

    elif 1<= len(intx_data['guild_roles']) <= 25: # Select Role
        intx_data['em'].add_field(name="Select a Role", value="** **", inline=False)
        await intx_data['intx'].response.edit_message(embed=intx_data['em'], view=guild_role_dropdown(client,intx_data)) 

    elif len(intx_data['guild_roles']) > 25:
        # Maximum elements in a select menu is 25, send modal and search
        await intx_data['intx'].response.send_modal(guild_role_name_modal(client,intx_data,search=True))
    
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Views                                                    *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class guild_role_dropdown_select(nextcord.ui.Select):
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client

        options = []
        active_role_id_list = []
        role_list = self.intx_data['guild_roles']

        if 'role_name_search_results' in self.intx_data:
            role_list = self.intx_data['role_name_search_results']

        if 'change' in self.intx_data:
            if 'nft_role' in self.intx_data['change']['type']:
                active_role_id_list = intx_data['change']['edit_role']['role_id_list']
            elif intx_data['change']['type'] == 'command_auth_role':
                active_role_id_list = intx_data['change']['role_id_list']
        for role_name,role in role_list.items():
            if str(role.id) in active_role_id_list:
                options.append(nextcord.SelectOption(label=role_name, description=f"", emoji="✅"),)
            else:
                options.append(nextcord.SelectOption(label=role_name, description=f"", emoji="❌"),)

        super().__init__(placeholder='Select Roles ...', min_values=1, max_values=len(options), options=options)

    async def callback(self, interaction: nextcord.Interaction):
        selected_role_names = self.values
        self.intx_data['selected_roles']={}
        # role_names=[]
        for name in selected_role_names:
            self.intx_data['selected_roles'][name] = self.intx_data['guild_roles'][name]
        #     role_names.append(name)
        # roles_str='\n'.join(role_names)
        # embed=self.intx_data['em'].add_field(name="Selected Roles",value=f"```\n{roles_str}```",inline=False)
        self.intx_data['intx'] = interaction
        await go_to_next_view(self.client,self.intx_data)

# Define a simple View that gives us a counter button
class guild_role_dropdown(nextcord.ui.View):
    # Discord disabled selects in modals, we'll use a view for now TODO
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        super().__init__()
        self.add_item(guild_role_dropdown_select(self.client,intx_data))

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['intx'] = interaction
        await go_to_next_view(self.client,self.intx_data)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Modals                                                   *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *


class guild_role_name_modal(nextcord.ui.Modal):
    def __init__(self,client,intx_data,search=False):
        self.intx_data = intx_data
        self.client = client
        self.search = search

        super().__init__(
            "Role Name",
            timeout=5 * 60,  # 5 minutes
        )

        self.role_name_seach = nextcord.ui.TextInput(
            label="Role",
            min_length=2,
            max_length=50,
        )
        self.add_item(self.role_name_seach)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        self.intx_data['role_name_search_input'] = self.role_name_seach.value
        search_str=self.intx_data['role_name_search_input'].lower().replace(" ","")
        results = []
        for role_name,role in self.intx_data['guild_roles']:
            if search_str in role_name.lower().replace(" ",""):
                results.append(role)
                break
        self.intx_data['role_name_search_results'] = results
        self.intx_data['em'].add_field(name="Select a Role", value="** **", inline=False)
        await interaction.response.edit_message(embed=self.intx_data['em'], view=guild_role_dropdown(self.client,self.intx_data)) 