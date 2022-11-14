import sys
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
from database import command_roles_db
import log_messages
from keys_and_codes import bot_owner_user_id,debug

async def command_auth(intx_data,auth_command,alert=True):
    if intx_data['intx'].user.id == bot_owner_user_id:
        authenticated = True
        output = "Bot Owner"
    elif intx_data['intx'].user.id == intx_data['intx'].guild.owner_id:
        authenticated = True
        output = "Guild Owner"
    else:
        authenticated = False

        auth_roles = command_roles_db.get_guild_comand_roles(intx_data['intx'].guild.id,auth_command)
        print(f"auth_roles: {auth_roles}")
        for userRole in intx_data['intx'].user.roles:
            print(f"Checking Role: {userRole}")
            if auth_roles is not None and userRole.id in auth_roles:
                authenticated = True
                output = 'Auth Role'
                print(f"Authenticated by Role: {userRole.name}")
                break

        if not authenticated:
            role_names=''
            for role in auth_roles:
                for role_name,guild_role in intx_data['guild_roles'].items():
                    if guild_role.id == role:
                        role_names=f"{role_names}\n{role_name}"

            output=role_names

            if alert:
                # Auth Failed Log Message
                log_message={
                    'title':"Authentication Failed",
                    'description':intx_data['intx'].guild.name,
                    'fields' : {
                        'Channel': intx_data['intx'].channel.name,
                        'Command': auth_command,
                    }
                }
                if intx_data['intx'].user.display_name != intx_data['intx'].user.name:
                    log_message['fields']['User Display Name'] = intx_data['intx'].user.display_name
                log_message['fields']['User Name'] = intx_data['intx'].user.name
                await log_messages.send(intx_data,log_message)

    if debug:
        print(f"command_auth output:\n  authenticated : {authenticated}\n  output        : {output}")

    return(authenticated,output)