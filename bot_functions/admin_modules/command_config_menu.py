import nextcord
import sys
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
    
from keys_and_codes import default_embed_footer
from admin_modules import bot_config_menu
from database import command_roles_db
import role_selection

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


def command_auth_role_embed(intx_data):
    title = intx_data['change']['type'].replace("_"," ").title().replace("Nft","NFT")
    em = nextcord.Embed(title=title,description=intx_data['descr'],color=nextcord.Colour.random())

    target_name = None
    qual_str = None

    em.add_field(name="Command",value=f"```\n{intx_data['change']['target_command']}```",inline=False)

    if 'selected_roles' in intx_data and intx_data['selected_roles'] is not None:
        role_names = []
        for role_name,role in intx_data['selected_roles'].items():
            if str(role.id) in intx_data['change']['role_id_list']:
                role_names.append(f"{role_name} (Removing)")
            else:
                role_names.append(f"{role_name} (Adding)")

        roles_str = '\n'.join(role_names)
        em.add_field(name="New Roles",value=f"```\n{roles_str}```",inline=False)

    return(em)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Views                                                    *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class entrypoint_view(nextcord.ui.View):

    def __init__(self,client,intx_data): 
        self.intx_data = intx_data
        self.client = client
        self.intx_data['change'] = {}
        super().__init__() 

    @nextcord.ui.button(label='/admin', style=nextcord.ButtonStyle.blurple)
    async def admin(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        await interaction.response.edit_message(embed=template_embed(self.intx_data), view=admin_config_view(self.client,self.intx_data))
        self.intx_data['change'] = {
            'target_command':'/admin'
        }
    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['em'] = bot_config_menu.template_embed(self.intx_data)
        await interaction.response.edit_message(embed=self.intx_data['em'], view=bot_config_menu.entrypoint_view(self.client,self.intx_data))

class admin_config_view(nextcord.ui.View):

    def __init__(self,client,intx_data): 
        self.intx_data = intx_data
        self.client = client
        super().__init__() 

    @nextcord.ui.button(label='Roles', style=nextcord.ButtonStyle.blurple)
    async def admin(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['change']['type'] = 'command_auth_role'
        role_id_list = command_roles_db.get_guild_command_roles(self.intx_data['intx'].guild.id,self.intx_data['change']['target_command'])
        if role_id_list is None:
            role_id_list = []
        self.intx_data['change']['role_id_list'] = role_id_list
        
        self.intx_data['intx'] = interaction
        await role_selection.guild_role_search_or_select(self.client,self.intx_data)

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['em'] = bot_config_menu.template_embed(self.intx_data)
        await interaction.response.edit_message(embed=self.intx_data['em'], view=entrypoint_view(self.client,self.intx_data))




class auth_role_confirm(nextcord.ui.View):
    
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        super().__init__() 
        
    @nextcord.ui.button(label='Save', style=nextcord.ButtonStyle.green)
    async def save_role(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        new_role_id_list = []
        target_command = self.intx_data['change']['target_command']
        # existing_role_id_list = self.intx_data['change']['role_id_list']
        init=False
        existing_role_id_list = command_roles_db.get_guild_command_roles(self.intx_data['intx'].guild.id,target_command)
        if existing_role_id_list is None:
            existing_role_id_list = []
            init=True
        selected_role_id_list = []  
        
        # edit_role = self.intx_data['change']['edit_role']
        for _,role in self.intx_data['selected_roles'].items():
            selected_role_id = str(role.id)
            selected_role_id_list.append(selected_role_id)
            if selected_role_id not in existing_role_id_list: # Removing role
                new_role_id_list.append(selected_role_id)
        for role_id in existing_role_id_list:
            if role_id not in selected_role_id_list and role_id not in new_role_id_list: # Existing roles that were not selected
                new_role_id_list.append(role_id)

        success,output = command_roles_db.save_guild_command_roles(self.intx_data['intx'].guild.id,target_command,new_role_id_list,init=init)
        em=template_embed(self.intx_data)

        if success:
            output=f"Success !"
            emoji='✅'
            self.intx_data['selected_roles']=None
            self.intx_data['change']=None
        else:
            emoji='❌'
        em.add_field(name=f"Update {target_command} roles", value=f"{emoji} {output}", inline=False)
        await interaction.response.edit_message(embed=em, view=entrypoint_view(self.client,self.intx_data))

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def back(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        em = template_embed(self.intx_data)
        self.intx_data['selected_roles']=None
        self.intx_data['change']=None
        await interaction.response.edit_message(embed=em, view=entrypoint_view(self.client,self.intx_data))


# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Modals                                                   *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *














