import sys
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
from database import database

def save_guild_command_roles(guild_id,command,role_list,init=False):
    print(f"len(role_list)={len(role_list)}={role_list}=")
    if init:
        return database.store('ctkxbotdb_bot_config','command_roles',{'guild_id':guild_id,'role_id_list':role_list,'command':command},update=False)
    else:
        if len(role_list) == 0:
            return database.store('ctkxbotdb_bot_config','command_roles',{},conditions={'guild_id':guild_id,'command':command},delete=True)
        else:
            return database.store('ctkxbotdb_bot_config','command_roles',{'role_id_list':role_list},update=True,conditions={'guild_id':guild_id,'command':command})

def get_guild_command_roles(guild_id,command):
    command_roles = database.get('ctkxbotdb_bot_config','command_roles',conditions={'guild_id':guild_id,'command':command})
    if len(command_roles) == 0:
        return None
    return command_roles[0]['role_id_list']