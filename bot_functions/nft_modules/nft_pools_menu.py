import nextcord
import sys
from tabulate import tabulate

if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
    
from keys_and_codes import default_embed_footer
import nft_main_menu
from database import nft_db

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Functions                                                *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
def change_summary(change):
    if change['type'] == 'create_nft_pool':
        return(f"Create NFT Pool: {change['nft_pool_input']}")
    if change['type'] == 'edit_nft_pool':
        return(f"Edit NFT Pool: {change['edit_pool_name']} to {change['nft_pool_input']}")
    if change['type'] == 'delete_nft_pool':
        return(f"Delete NFT Pool: {change['edit_pool_name']}")

def template_embed(intx_data,pool_stats=True):
    if 'nft_pools' not in intx_data:
        intx_data['nft_pools'] = nft_db.get_nft_pools(intx_data['intx'].guild.id)

    em = nextcord.Embed(title=intx_data['title'],description=intx_data['descr'],color=nextcord.Colour.random())

    if pool_stats:
        if len(intx_data['nft_pools']) == 0:
            em.add_field(name="No NFT Pools Configured!", value=f"** **", inline=False)
        else:
            pools_table_rows=[]
            for pool in intx_data['nft_pools']:
                pool['nft_list'],pool['nft_quantity'],pool['unique_nfts'] = nft_db.get_pool_nfts(intx_data['intx'].guild.id,pool['id'])
            pools_table_rows.append([pool['pool_name'],pool['unique_nfts'],pool['nft_quantity']])

        em.add_field(name="Pools", value=f"```\n{tabulate(pools_table_rows,headers=['Pool Name','Unique NFTs','Quantity'],tablefmt='simple')}```",inline=False)

    if 'embed_footer' in intx_data:
        embed_footer_text=intx_data['embed_footer']
    else:
        embed_footer_text=default_embed_footer['text']
    em.set_footer(text = embed_footer_text, icon_url = default_embed_footer['icon_url'])

    return(em)

async def nft_pool_search_or_select(client,intx_data):
    em = template_embed(intx_data)
    # Select or Search Pools
    if len(intx_data['nft_pools']) == 0: # If there are no nft pools
        em.add_field(name="No NFT Pools Found!", value="Please create an NFT Pool first.", inline=False)
        em.add_field(name="What would you like to configure?", value="** **", inline=False)
        await intx_data['intx'].response.edit_message(embed=em, view=entrypoint_view(client,intx_data))
        return
        # No pools to edit
    elif 1<= len(intx_data['nft_pools']) <= 25: # Select Pool
        em.add_field(name="Select an NFT Pool", value="** **", inline=False)
        await intx_data['intx'].response.edit_message(embed=em, view=nft_pool_dropdown(client,intx_data)) 
        return
    elif len(intx_data['nft_pools']) > 25:
        # Maximum elements in a select menu is 25, send pool_name modal and search
        await intx_data['intx'].response.send_modal(nft_pool_name_modal(client,intx_data,search=True))
        return


# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Views                                                    *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class entrypoint_view(nextcord.ui.View):
    
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        intx_data['nft_pools'] = nft_db.get_nft_pools(intx_data['intx'].guild.id)
        super().__init__() 

    @nextcord.ui.button(label='Create Pool', style=nextcord.ButtonStyle.green)
    async def create(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['change'] = {
            'type': 'create_nft_pool',
        }
        # Send Pool Name Modal
        await interaction.response.send_modal(nft_pool_name_modal(self.client,self.intx_data))

    @nextcord.ui.button(label='Edit Pool', style=nextcord.ButtonStyle.blurple)
    async def edit(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['change'] = {
            'type': 'edit_nft_pool',
        }
        self.intx_data['intx'] = interaction
        await nft_pool_search_or_select(self.client,self.intx_data)

    @nextcord.ui.button(label='Delete Pool', style=nextcord.ButtonStyle.red)
    async def delete(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['change'] = {
            'type': 'delete_nft_pool',
        }
        self.intx_data['intx'] = interaction
        await nft_pool_search_or_select(self.client,self.intx_data)

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def back(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        em = nft_main_menu.template_embed(self.intx_data)
        await interaction.response.edit_message(embed=em, view=nft_main_menu.entrypoint_view(self.client,self.intx_data))

class nft_pool_dropdown_select(nextcord.ui.Select):
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client

        options = []

        if 'nft_pool_search_results' in self.intx_data:
            nft_pools_list = self.intx_data['nft_pool_search_results']
        else:
            if 'nft_pools' not in intx_data:
                nft_pools_list = nft_db.get_nft_pools(intx_data['intx'].guild.id)
            else:
                nft_pools_list = intx_data['nft_pools']

        for pool in nft_pools_list:
            options.append(nextcord.SelectOption(label=pool['pool_name'], description=f"", emoji=None),)

        super().__init__(placeholder='Select an NFT Pool...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        em = template_embed(self.intx_data)
        pool_name = self.values[0]
        pool_id = None

        for pool in self.intx_data['nft_pools']:
            if pool_name == self.values[0]:
                pool_id = pool['id']
                break

        if pool_id is None:
            em.add_field(name="Error", value=f"Could not find pool id for {pool_name}.", inline=False)
            em.add_field(name="What would you like to configure?", value="** **", inline=False)
            await interaction.response.edit_message(embed=em, view=entrypoint_view(self.client,self.intx_data))
            return

        if 'next_view' in self.intx_data:
            self.intx_data['target_nft_pool'] = {
                'name': pool_name,
                'id': pool_id
            }
            await interaction.response.edit_message(embed=em, view=self.intx_data['next_view'])

        elif 'change' in self.intx_data :
            self.intx_data['change']['edit_pool_name'] = pool_name
            self.intx_data['change']['edit_pool_id'] = pool_id

            if self.intx_data['change']['type'] == 'edit_nft_pool':
                await interaction.response.send_modal(nft_pool_name_modal(self.client,self.intx_data))
            elif self.intx_data['change']['type'] == 'delete_nft_pool':
                em.add_field(name="Confirm Change?", value=change_summary(self.intx_data['change']), inline=False)
                await interaction.response.edit_message(embed=em, view=confirm_change_view(self.client,self.intx_data))

# Define a simple View that gives us a counter button
class nft_pool_dropdown(nextcord.ui.View):
    # Discord disabled selects in modals, we'll use a view for now TODO
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        super().__init__()
        self.add_item(nft_pool_dropdown_select(self.client,intx_data))

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        em = template_embed(self.intx_data)
        await interaction.response.edit_message(embed=em, view=nft_main_menu.entrypoint_view(self.client,self.intx_data))


class confirm_change_view(nextcord.ui.View):

    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        intx_data['nft_pools'] = nft_db.get_nft_pools(intx_data['intx'].guild.id)
        super().__init__() 

    @nextcord.ui.button(label='Confirm', style=nextcord.ButtonStyle.green)
    async def confirm(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        success,output=False,None
        if 'change' not in self.intx_data:
            output="No change requested!"

        elif self.intx_data['change']['type'] == 'create_nft_pool':
            if 'nft_pool_input' not in self.intx_data['change']:
                output="No NFT Pool input!"
            else:
                success,output = nft_db.create_nft_pool(self.intx_data['intx'].guild.id,self.intx_data['change']['nft_pool_input'])
                if success: # Output is the pool's ID and we don't need it here
                    output=f"NFT Pool '{self.intx_data['change']['nft_pool_input']}' created!"
        elif self.intx_data['change']['type'] == 'edit_nft_pool':
            success,output = nft_db.edit_nft_pool(self.intx_data['intx'].guild.id,self.intx_data['change']['nft_pool_input'],self.intx_data['change']['edit_pool_id'])
            if success:
                output=f"NFT Pool '{self.intx_data['change']['edit_pool_name']}' renamed to '{self.intx_data['change']['nft_pool_input']}'!"
        elif self.intx_data['change']['type'] == 'delete_nft_pool':
            success,output = nft_db.delete_nft_pool(self.intx_data['intx'].guild.id,self.intx_data['change']['edit_pool_id'])
            if success:
                output=f"NFT Pool '{self.intx_data['change']['edit_pool_name']}' deleted!"
        if success:
            emoji='✅'
        else:
            emoji='❌'
        self.intx_data['change']=None
        em=template_embed(self.intx_data)
        em.add_field(name="Change Outcome", value=f"{emoji} {output}", inline=False)
        await interaction.response.edit_message(embed=em, view=nft_main_menu.entrypoint_view(self.client,self.intx_data))

    @nextcord.ui.button(label='Cancel', style=nextcord.ButtonStyle.red)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        em = nft_main_menu.template_embed(self.intx_data)
        self.intx_data['change'] = None
        await interaction.response.edit_message(embed=em, view=nft_main_menu.entrypoint_view(self.client,self.intx_data))

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Modals                                                   *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class nft_pool_name_modal(nextcord.ui.Modal):
    def __init__(self,client,intx_data,search=False):
        self.intx_data = intx_data
        self.client = client
        self.search = search

        super().__init__(
            "NFT Pool Name",
            timeout=5 * 60,  # 5 minutes
        )

        self.nft_pool = nextcord.ui.TextInput(
            label="Name",
            min_length=2,
            max_length=50,
        )
        self.add_item(self.nft_pool)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        em = template_embed(self.intx_data,)
        if self.search:
            self.intx_data['nft_pool_search_results'] = []
            search_string = self.nft_pool.value.lower().replace(' ','')
            for nft_pool in self.intx_data['nft_pools']:
                if search_string in nft_pool['pool_name'].lower().replace(' ',''):
                    self.intx_data['nft_pool_search_results'].append(nft_pool)
            if len(self.intx_data['nft_pool_search_results']) == 0:
                em.add_field(name=f"No pools found!", value=f"Searched: {self.nft_pool.value}", inline=False)
                em = template_embed(self.intx_data)
                em.add_field(name="What would you like to configure?", value="** **", inline=False)
                await interaction.response.edit_message(embed=em, view=entrypoint_view(self.client,self.intx_data))
                return
            em.add_field(name="Select an NFT Pool", value="** **", inline=False)
            await interaction.response.edit_message(embed=em, view=nft_pool_dropdown(self.client,self.intx_data)) 
            return

        elif 'change' in self.intx_data and self.intx_data['change'] is not None:
            self.intx_data['change']['nft_pool_input'] = self.nft_pool.value

            for nft_pool in self.intx_data['nft_pools']:
                if nft_pool['pool_name'].lower() == self.nft_pool.value.lower():
                    if self.intx_data['change']['type'] == 'create_nft_pool':
                        em.add_field(name=f"An NFT Pool named '{nft_pool['pool_name']}' already exists!", value="Please choose another name.", inline=False)
                        em.add_field(name="What would you like to configure?", value="** **", inline=False)
                        await interaction.response.edit_message(embed=em, view=entrypoint_view(self.client,self.intx_data))
                        return
            em.add_field(name="Confirm Change?", value=change_summary(self.intx_data['change']), inline=False)
            await interaction.response.edit_message(embed=em, view=confirm_change_view(self.client,self.intx_data))






