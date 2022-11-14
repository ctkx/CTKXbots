import sys
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")

from database import database

def save_log_channel(guild_id,log_channel_id,init=False):
    if init:
        database.store('guild_config','log_channels',{'guild_id':guild_id,'log_channel_id':log_channel_id},update=False)
    else:
        database.store('guild_config','log_channels',{'log_channel_id':log_channel_id},update=True,conditions={'guild_id':guild_id})

def get_guild_log_channel_id(guild_id):
    log_channel=database.get('guild_config','log_channels',conditions={'guild_id':guild_id})[0]['log_channel_id']
    return int(log_channel)