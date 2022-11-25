import nextcord
import sys
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
from database import log_channel_db

log_message_template={
    'title':"",
    'description':"",
    'fields' : {
        'title': 'value',
        'title': 'value',
    }
}

async def send(intx_data,log_message,guild=None):
    if 'title' not in log_message:
        log_message['title'] = "Log Message"

    if 'description' not in log_message:
        log_message['description'] = "** **"

    em = nextcord.Embed(title=log_message['title'],description=log_message['description'],color=nextcord.Colour.random())
    for field_title,field_value in log_message['fields'].items():
        em.add_field(name=field_title,value=field_value,inline=False)

    if not guild:
        guild = intx_data['intx'].guild
    log_channel_id=log_channel_db.get_guild_log_channel_id(guild.id)

    if log_channel_id is not None:
        log_channel = guild.get_channel(log_channel_id)
        await log_channel.send(embed=em)
