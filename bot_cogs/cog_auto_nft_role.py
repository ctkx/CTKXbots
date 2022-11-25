from nextcord.ext import tasks,commands
import sys
import requests
if "/bot_functions" not in sys.path:
    sys.path.append("/bot_functions")
from keys_and_codes import loopring_api_key,debug
from loopring import get
from database import nft_db
import log_messages
import asyncio
from threading import Thread
import time
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
#                                      Functions                                                *
# * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *
def get_nft_owner_addresses(nft_id,minter_address,token_address):
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
        'roles':{},
        'changes':{
            'add_role' : {
                # {'user_id':0, 'role_list':[] },
            },
            'remove_role' : {
                # {'user_id':0, 'role_list':[] },
            },
        }
    }

    # Get NFT Roles and target NFT info, and get owner addresses for each NFT
    print(f"auto_nft_role: {guild.name} processing NFT data ")
    for nft_role in guild_nft_roles:
        if nft_role['target_type'] == 'nft':
            nft_role['nft_list'] = [nft_db.get_pool_nft(f"{guild.id}",nft_role['target_id'])]
        elif nft_role['target_type'] == 'pool':
            nft_role['nft_list'],_,_ = nft_db.get_pool_nfts(f"{guild.id}",nft_role['target_id'])
        for nft in nft_role['nft_list']:
            if nft['nft_id'] not in data['owner_addresses']:
                data['owner_addresses'][nft['nft_id']] = get_nft_owner_addresses(nft['nft_id'],nft['minter_address'],nft['token_address'])
                print(f"Found {len(data['owner_addresses'][nft['nft_id']])} owners for NFT: {nft['nft_name']}")

    print(f"auto_nft_role: {guild.name} processing owner addresses ")
    for nft_id,address_list in data['owner_addresses'].items(): 
        # get_nft_owner_addresses only gives us the address, not the quantity of NFTs owned. So we need to get the balance of each address
        for wallet_address in address_list:
            if wallet_address.lower() not in data['wallet_balances']:
                loopring_account_id = get.user_info(wallet_address)['accountId']
                data['wallet_balances'][wallet_address.lower()] = get.user_nft_balance(loopring_account_id)

    print(f"auto_nft_role: {guild.name} processing wallets ")

    for wallet in guild_wallets:
    # guild_wallets is a list of dicts, each dict is a user's wallet info.
    # We'll build a new dict using the user ID as the key, and the wallet address as the value.
    # This way we won't have to loop through the guild_wallets list every time we check a new user.
        user_id = str(wallet['discord_user_id'])
        if user_id not in data['user_wallets']:
            data['user_wallets'][user_id] = []
        data['user_wallets'][user_id].append(wallet['wallet_address'].lower())

    dry_run = False

    for nft_role in guild_nft_roles:
        min_req_nfts = int(nft_role['quantity_min'])
        max_req_nfts = int(nft_role['quantity_max'])

        for member in guild_members:
            if member.bot:
                continue # skip bots

            for role_id in nft_role['role_id_list']:
                role = guild.get_role(int(role_id))

                member_has_role = False
                member_entitled_to_role = False

                for member_role in member.roles:
                    if member_role.id == int(role_id):
                        member_has_role = True
                        break

                score = 0

                for address in data['user_wallets'][str(member.id)]:
                    for nft in nft_role['nft_list']:

                        if address in data['wallet_balances']:
                            for _,wallet_nft in data['wallet_balances'][address].items():

                                if nft['nft_id'] == wallet_nft['nftId']:
                                    score += int(wallet_nft['total'])

                            if score > 0:
                                print(f"auto_nft_role: {guild.name} {wallet['wallet_address']} scored {score}")

                if min_req_nfts <= score <= max_req_nfts:
                    member_entitled_to_role = True

                else:
                    member_entitled_to_role = False

                assignment_output = ''

                if member_has_role and not member_entitled_to_role:
                    if str(member.id) not in data['changes']['remove_role']:
                        data['changes']['remove_role'][str(member.id)] = []

                    assignment_output=f"Removing role {role.name} from {member.name}"
                    data['changes']['remove_role'][str(member.id)].append(role)

                elif not member_has_role and member_entitled_to_role:
                    if str(member.id) not in data['changes']['add_role']:
                        data['changes']['add_role'][str(member.id)] = []

                    assignment_output=f"Adding role {role.name} to {member.name}"
                    data['changes']['add_role'][str(member.id)].append(role)

                if len(assignment_output) > 0:
                    if dry_run:
                        assignment_output=f"{assignment_output} (dry run)"

                    print(assignment_output)

    if dry_run:
        print(f"auto_nft_role: {guild.name} changing roles (dry run) ")

    if not dry_run:
        member_count = len(data['changes']['remove_role']) + len(data['changes']['add_role'])
        print(f"auto_nft_role: {guild.name} changing roles for {member_count} members in{guild.name} ")

        for user_id,remove_role_list in data['changes']['remove_role'].items():
            print(f"Removing roles for {user_id}")
            await member.remove_roles(*remove_role_list)
            role_names = ', '.join([role.name for role in remove_role_list])
            print(f"Removed roles {role_names} from {member.name}")

        for user_id,add_role_list in data['changes']['add_role'].items():
            print(f"Adding roles for {user_id}")
            await member.add_roles(*add_role_list)
            role_names = ', '.join([role.name for role in add_role_list])
            print(f"Added roles {role_names} to {member.name}")

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
