import sys
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")

from database import database

def save_log_channel(guild_id,log_channel_id,init=False):
    if init:
        return database.store('ctkxbotdb_bot_config','log_channels',{'guild_id':guild_id,'log_channel_id':log_channel_id},update=False)
    else:
        return database.store('ctkxbotdb_bot_config','log_channels',{'log_channel_id':log_channel_id},update=True,conditions={'guild_id':guild_id})

def get_guild_log_channel_id(guild_id):
    log_channels=database.get('ctkxbotdb_bot_config','log_channels',conditions={'guild_id':guild_id})
    if len(log_channels) == 0 :
        channel_id=None
    else:
        channel_id=int(log_channels[0]['log_channel_id'])
    return channel_id