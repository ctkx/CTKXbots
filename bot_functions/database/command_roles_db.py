import sys
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
from database import database

def save_guild_command_roles(guild_id,command,role_list,init=False):
    if init:
        database.store('guild_config','command_roles',{'guild_id':guild_id,'role_list':role_list,'command':command},update=False)
    else:
        database.store('guild_config','command_roles',{'role_list':role_list},update=True,conditions={'guild_id':guild_id,'command':command})

def get_guild_comand_roles(guild_id,command):
    return database.get('guild_config','command_roles',conditions={'guild_id':guild_id,'command':command})