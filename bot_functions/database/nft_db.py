import sys
import time
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
from database import database

def get_nft_pools(guild_id=None):
    if guild_id is None:
        return database.get('ctkxbotdb_nft','guild_nft_pools')
    return database.get('ctkxbotdb_nft','guild_nft_pools',conditions={'guild_id':guild_id})

def create_nft_pool(guild_id,pool_name):
    return database.store('ctkxbotdb_nft','guild_nft_pools',{'guild_id':guild_id,'pool_name':pool_name})

def edit_nft_pool(guild_id,pool_name,edit_row_id):
    return database.store('ctkxbotdb_nft','guild_nft_pools',{'pool_name':pool_name},conditions={'guild_id':guild_id,'id':edit_row_id},update=True)

def delete_nft_pool(guild_id,edit_row_id):
    return database.store('ctkxbotdb_nft','guild_nft_pools',{},conditions={'guild_id':guild_id,'id':edit_row_id},delete=True)

def get_pool_nfts(guild_id,pool_id): # was get_nft_pool 
    nft_list = database.get('ctkxbotdb_nft','guild_nfts',conditions={'guild_id':guild_id,'pool_id':pool_id})
    nft_quantity = 0
    unique_nfts  = 0
    for nft in nft_list:
        unique_nfts += 1
        nft_quantity += int(nft['nft_quantity'])
    return nft_list,nft_quantity,unique_nfts

def add_bulk_import_sheet(guild_id,import_code,sheet_url):
    return database.store('ctkxbotdb_nft','bulk_import_sheets',{'guild_id':guild_id,'import_code':import_code,'sheet_url':sheet_url})

def get_bulk_import_sheets(guild_id):
    return database.get('ctkxbotdb_nft','bulk_import_sheets',conditions={'guild_id':guild_id})