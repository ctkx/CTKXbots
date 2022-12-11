import sys
import time
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
from database import database

def create_nft_role(role):
    return database.store('ctkxbotdb_nft','guild_nft_roles',role)

def edit_nft_role(guild_id,role_id,new_role_data):
    return database.store('ctkxbotdb_nft','guild_nft_roles',new_role_data,conditions={'guild_id':guild_id,'id':role_id},update=True)

def delete_nft_role(guild_id,role_id):
    return database.store('ctkxbotdb_nft','guild_nft_roles',{},conditions={'guild_id':guild_id,'id':role_id},delete=True)

def get_nft_roles(guild_id):
    return database.get('ctkxbotdb_nft','guild_nft_roles',conditions={'guild_id':guild_id})

def get_nft_role_guilds():
    guild_list=[]
    for role in database.get('ctkxbotdb_nft','guild_nft_roles'):
        guild_list.append(role['guild_id'])
    return guild_list

def get_nft_role(guild_id,role_id):
    return database.get('ctkxbotdb_nft','guild_nft_roles',conditions={'guild_id':guild_id,'id':role_id})[0]

def get_nft_pools(guild_id=None):
    if guild_id is None:
        return database.get('ctkxbotdb_nft','guild_nft_pools')
    return database.get('ctkxbotdb_nft','guild_nft_pools',conditions={'guild_id':guild_id})

def get_nft_pool(guild_id,pool_id):
    return database.get('ctkxbotdb_nft','guild_nft_pools',conditions={'guild_id':guild_id,'id':pool_id})[0]

def create_nft_pool(guild_id,pool_name):
    return database.store('ctkxbotdb_nft','guild_nft_pools',{'guild_id':guild_id,'pool_name':pool_name})

def edit_nft_pool(guild_id,pool_name,edit_row_id):
    return database.store('ctkxbotdb_nft','guild_nft_pools',{'pool_name':pool_name},conditions={'guild_id':guild_id,'id':edit_row_id},update=True)

def delete_nft_pool(guild_id,edit_row_id):
    return database.store('ctkxbotdb_nft','guild_nft_pools',{},conditions={'guild_id':guild_id,'id':edit_row_id},delete=True)

def get_pool_nfts(guild_id,pool_id):
    nft_list = database.get('ctkxbotdb_nft','guild_nfts',conditions={'guild_id':guild_id,'pool_id':pool_id})
    nft_quantity = 0
    unique_nfts  = 0
    for nft in nft_list:
        unique_nfts += 1
        nft_quantity += int(nft['quantity'])
    return nft_list,nft_quantity,unique_nfts

def get_pool_nft(guild_id,nft_id):
    return database.get('ctkxbotdb_nft','guild_nfts',conditions={'guild_id':guild_id,'id':nft_id})[0]

def add_nfts_to_pool(guild_id,pool_id,nft_list):
    for nft in nft_list:
        nft['guild_id'] = guild_id
        nft['pool_id']  = pool_id
    return database.store('ctkxbotdb_nft','guild_nfts',nft_list)

def edit_pool_nft(guild_id,nft):
    nft_id=nft['id']
    del nft['id']
    return database.store('ctkxbotdb_nft','guild_nfts',nft,conditions={'guild_id':guild_id,'id':nft_id},update=True)
    
def delete_pool_nft(guild_id,nft):
    return database.store('ctkxbotdb_nft','guild_nfts',{},conditions={'guild_id':guild_id,'id':nft['id']},delete=True)


def add_bulk_import_sheet(guild_id,import_code,sheet_url):
    return database.store('ctkxbotdb_nft','bulk_import_sheets',{'guild_id':guild_id,'import_code':import_code,'sheet_url':sheet_url})

def get_bulk_import_sheets(guild_id):
    return database.get('ctkxbotdb_nft','bulk_import_sheets',conditions={'guild_id':guild_id})

def get_user_wallets(guild_id,user_id=None,all_users=False):
    if all_users:
        return database.get('ctkxbotdb_nft','user_wallets',conditions={'guild_id':guild_id})
    elif user_id is not None:
        return database.get('ctkxbotdb_nft','user_wallets',conditions={'guild_id':guild_id,'user_id':user_id})

def get_wallet_owner_id(guild_id,wallet_address):
    wallets = database.get('ctkxbotdb_nft','user_wallets',conditions={'guild_id':guild_id,'wallet_address':wallet_address})
    if len(wallets) == 0:
        return None
    return wallets[0]['user_id']


def edit_user_wallet(intx_data):
    print(intx_data['operation'])
    if intx_data['operation'] == "add":
        data={
            'guild_id': intx_data['guild_id'],
            'user_id': intx_data['user_id'],
            'wallet_input': intx_data['wallet_input'].lower(),
            'wallet_address': intx_data['wallet_address'].lower(),
            'wallet_note': intx_data['wallet_note'],
            'last_ens_refresh': str(time.time()).split('.')[0],
            'last_loopring_account_refresh': str(time.time()).split('.')[0],
        }
        success,output = database.store('ctkxbotdb_nft','user_wallets',data)
        print(success,output)
        print("---")
    elif intx_data['operation'] == "remove":
        cond={
            'guild_id': intx_data['guild_id'],
            'user_id': intx_data['user_id'],
            'wallet_input': intx_data['wallet_input'],
        }
        query=f"DELETE FROM user_wallets WHERE guild_id='{intx_data['guild_id']}' AND user_id='{intx_data['user_id']}' AND wallet_input='{intx_data['wallet_input']}';"
        success,output = database.store('ctkxbotdb_nft','user_wallets',conditions=cond,delete=True)
