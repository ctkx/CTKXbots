import nextcord
import sys
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")

from keys_and_codes import default_embed_footer
from admin_modules import log_config_menu
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Functions                                                *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

async def go_to_next_view(client,intx_data,extra_field=None):
    if 'log_channel' in intx_data['change']['type'] :
        em = log_config_menu.template_embed(intx_data)
        if extra_field:                                                        
            em.add_field(name=extra_field['name'],value=extra_field['value'],inline=False)
        await intx_data['intx'].response.edit_message(embed=em, view=log_config_menu.confirm_changes_view(client,intx_data)) 

async def guild_channel_search_or_select(client,intx_data):
    # Select or Search Channels
    if len(intx_data['guild_channels']) == 0: # If there are no Channels
        go_to_next_view(client,intx_data,extra_field={'name':'No Channels Found!','value':'Please create some channels first.'})

    elif 1<= len(intx_data['guild_channels']) <= 25: # Select Channel
        intx_data['em'].add_field(name="Select a Channel", value="** **", inline=False)
        await intx_data['intx'].response.edit_message(embed=intx_data['em'], view=guild_channel_dropdown(client,intx_data)) 

    elif len(intx_data['guild_channels']) > 25:
        # Maximum elements in a select menu is 25, send modal and search
        await intx_data['intx'].response.send_modal(guild_channel_name_modal(client,intx_data,search=True))
    
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Views                                                    *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *

class guild_channel_dropdown_select(nextcord.ui.Select):
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client

        options = []
        active_channel_id_list = []
        channel_list = self.intx_data['guild_channels']

        if 'channel_name_search_results' in self.intx_data:
            channel_list = self.intx_data['channel_name_search_results']

        if 'change' in self.intx_data:
            if 'edit_log_channel' in self.intx_data['change']['type'] and 'log_channel' in self.intx_data:
                active_channel_id_list = [str(intx_data['log_channel'].id)]

        for channel_name,channel in channel_list.items():
            if str(channel.id) in active_channel_id_list:
                options.append(nextcord.SelectOption(label=channel_name, description=f"", emoji="✅"),)
            else:
                options.append(nextcord.SelectOption(label=channel_name, description=f"", emoji="❌"),)

        super().__init__(placeholder='Select Channels ...', min_values=1, max_values=len(options), options=options)

    async def callback(self, interaction: nextcord.Interaction):
        selected_channel_names = self.values
        self.intx_data['selected_channels']={}
        # channel_names=[]
        for name in selected_channel_names:
            self.intx_data['selected_channels'][name] = self.intx_data['guild_channels'][name]

        self.intx_data['intx'] = interaction
        await go_to_next_view(self.client,self.intx_data)

# Define a simple View that gives us a counter button
class guild_channel_dropdown(nextcord.ui.View):
    # Discord disabled selects in modals, we'll use a view for now TODO
    def __init__(self,client,intx_data):
        self.intx_data = intx_data
        self.client = client
        super().__init__()
        self.add_item(guild_channel_dropdown_select(self.client,intx_data))

    @nextcord.ui.button(label='Back', style=nextcord.ButtonStyle.grey)
    async def cancel(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
        self.intx_data['intx'] = interaction
        await go_to_next_view(self.client,self.intx_data)

# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Modals                                                   *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *


class guild_channel_name_modal(nextcord.ui.Modal):
    def __init__(self,client,intx_data,search=False):
        self.intx_data = intx_data
        self.client = client
        self.search = search

        super().__init__(
            "Channel Name",
            timeout=5 * 60,  # 5 minutes
        )

        self.channel_name_seach = nextcord.ui.TextInput(
            label="Channel",
            min_length=2,
            max_length=50,
        )
        self.add_item(self.channel_name_seach)

    async def callback(self, interaction: nextcord.Interaction) -> None:
        self.intx_data['channel_name_search_input'] = self.channel_name_seach.value
        search_str=self.intx_data['channel_name_search_input'].lower().replace(" ","")
        results = []
        for channel_name,channel in self.intx_data['guild_channels']:
            if search_str in channel_name.lower().replace(" ",""):
                results.append(channel)
                break
        self.intx_data['channel_name_search_results'] = results
        self.intx_data['em'].add_field(name="Select a Channel", value="** **", inline=False)
        await interaction.response.edit_message(embed=self.intx_data['em'], view=guild_channel_dropdown(self.client,self.intx_data)) 