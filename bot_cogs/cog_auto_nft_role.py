from nextcord.ext import tasks,commands
import sys
import requests
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
from keys_and_codes import loopring_api_key,debug
from loopring import get
from database import nft_db
import asyncio
from threading import Thread
import time
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Functions                                                *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
def get_nft_owner_addresses(nft_id,minter_address,token_address):
    # print(f"auto_nft_role: get_owner_addresses")
    # print(membership_nft)
    url=f"https://api3.loopring.io/api/v3/nft/info/nftData?minter={minter_address}&tokenAddress={token_address}&nftId={nft_id}"

    data=requests.get(url).json()
    if 'nftData' not in data:
        return []
    nft_data=data['nftData']

    hdr = {"X-API-KEY":loopring_api_key}

    url=f"https://api3.loopring.io/api/v3/nft/info/nftHolders?nftData={nft_data}"#  &offset=0&limit=100"
    nft_holders=requests.get(url=url,headers=hdr).json()['nftHolders']

    nft_owner_address_list=[]
    for holder in nft_holders:
        url=f"https://api3.loopring.io/api/v3/account?accountId={holder['accountId']}"
        owner_address=requests.get(url).json()['owner']
        nft_owner_address_list.append(owner_address.lower())
        
    return(nft_owner_address_list)


# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Loop Class                                               *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
dry_run = False

# make a loop running in a parallel Thread
class AsyncLoopThread(Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.loop = asyncio.new_event_loop()

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

async def auto_manage_nft_roles(guild,guild_members):
    guild_wallets=nft_db.get_user_wallets(f'{guild.id}' ,all_users=True)
    guild_nft_roles=nft_db.get_nft_roles(guild.id)
    data={
        'owner_addresses':{},
        'wallet_balances':{},
        'user_wallets':{},
        'roles':{}
    }

    # Get NFT Roles and target NFT info, and get owner addresses for each NFT
    print(f"auto_manage_nft_roles: processing role data for {guild.name} ")
    for nft_role in guild_nft_roles:
        for discord_role_id in nft_role['role_id_list']:
            if discord_role_id not in data['roles']:
                data['roles'][str(discord_role_id)] = nft_role
            print(discord_role_id)

        if nft_role['target_type'] == 'nft':
            data['roles'][discord_role_id]['nft_list'] = [nft_db.get_pool_nft(f"{guild.id}",nft_role['target_id'])]
        elif nft_role['target_type'] == 'pool':
            data['roles'][discord_role_id]['nft_list'],_,_ = nft_db.get_pool_nfts(f"{guild.id}",nft_role['target_id'])
        for nft in data['roles'][discord_role_id]['nft_list']:
            if nft['nft_id'] not in data['owner_addresses']:
                data['owner_addresses'][nft['nft_id']] = get_nft_owner_addresses(nft['nft_id'],nft['minter_address'],nft['token_address'])
                print(f"Found {len(data['owner_addresses'][nft['nft_id']])} owners for NFT: {nft['nft_name']}")

    print(f"auto_manage_nft_roles: processing owner addresses for {guild.name} ")
    for nft_id,address_list in data['owner_addresses'].items(): 
        # get_nft_owner_addresses only gives us the address, not the quantity of NFTs owned. So we need to get the balance of each address
        for wallet_address in address_list:
            if wallet_address.lower() not in data['wallet_balances']:
                loopring_account_id = get.user_info(wallet_address)['accountId']
                data['wallet_balances'][wallet_address.lower()] = get.user_nft_balance(loopring_account_id)

    print(f"auto_manage_nft_roles: processing wallets for {guild.name} ")

    for wallet in guild_wallets:
    # guild_wallets is a list of dicts, each dict is a user's wallet info.
    # We'll build a new dict using the user ID as the key, and the wallet address as the value.
    # This way we won't have to loop through the guild_wallets list every time we check a new user.
        user_id = str(wallet['discord_user_id'])
        if user_id not in data['user_wallets']:
            data['user_wallets'][user_id] = []
        data['user_wallets'][user_id].append(wallet['wallet_address'].lower())

    print(f"auto_manage_nft_roles: managing roles for {guild.name} ")
    for member in guild_members:
        if member.bot:
            continue # skip bots
        for member_role in member.roles:
            if str(member_role.id) not in data['roles']:
                continue # skip roles that aren't NFT roles
            print(data['roles'][str(member_role.id)])
            min_req_nfts = int(data['roles'][str(member_role.id)]['quantity_min'])
            max_req_nfts = int(data['roles'][str(member_role.id)]['quantity_max'])
            print(f"Member {member.name} has NFT role {member_role.name}")




class auto_nft_role(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.checked_messages = []
        self.parallel = False # Set to False to disable parallel processing for debugging
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog Loaded : "+__file__)
        self.main_loop.start()

    @tasks.loop(hours = 1) # repeat this often
    async def main_loop(self):


        guild_id_list=nft_db.get_nft_role_guilds()
        guild_list=[]
        for guild in self.client.guilds:
            print(f"auto_nft_role: {guild.name} active={f'{guild.id}' in guild_id_list}")
            if f"{guild.id}" in guild_id_list:
                guild_list.append(guild)

        for guild in guild_list:
            guild_members = await guild.fetch_members().flatten()
            if self.parallel:
                # Create a parallel thread and run the processing there.
                # This allows the bot to continue processing other commands in the main thread.

                loop_handler = AsyncLoopThread()
                loop_handler.start()
                asyncio.run_coroutine_threadsafe(auto_manage_nft_roles(guild,guild_members), loop_handler.loop)
            else:
                # We can't see stderr from the parallel thread. ( I can probably fix this later )
                # But for now i'm being lazy and running the loop in the main thread for debugging
                await auto_manage_nft_roles(guild,guild_members)

def setup(client):
    client.add_cog(auto_nft_role(client))
