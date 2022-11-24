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

# first, we need a loop running in a parallel Thread
class AsyncLoopThread(Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.loop = asyncio.new_event_loop()

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()


async def auto_manage_nft_roles(guild,guild_members):
    nft_holders={}
    guild_wallets=nft_db.get_user_wallets(f'{guild.id}' ,all_users=True)
    role_assignments_output=''
    # Get NFT Roles, make a dict for each role
    guild_nft_roles=nft_db.get_nft_roles(guild.id)
    guild_auto_nft_roles={}
    for nft_role in guild_nft_roles:
        for role_id in nft_role['role_id_list']:

            nft_id_list = []
            # nft_pool = nft_role['nft_pool']
            # nfts = nft_db.get_nft_pool(f"{guild.id}",nft_role['target_id'])['nfts']

            if role_id not in guild_auto_nft_roles:
                guild_auto_nft_roles[role_id] = {
                    'qualifying_nft_list': [],
                    'quantity_required': nft_role['quantity_min']
                }

            if nft_role['target_type'] == 'nft':
                nft = nft_db.get_pool_nft(f"{guild.id}",nft_role['target_id'])
                nft_id_list.append(nft['nft_id'])
                if nft['nft_id'] not in nft_holders:
                    nft_holders[nft['nft_id']] = get_nft_owner_addresses(nft['nft_id'],nft['minter_address'],nft['token_address'])
                    guild_auto_nft_roles[role_id]['qualifying_nft_list'].append(nft['nft_id'])
            if nft_role['target_type'] == 'pool':
                
                pool_nfts,nft_quantity,unique_nfts = nft_db.get_pool_nfts(f"{guild.id}",nft_role['target_id'])
                
                for nft in pool_nfts:
                    nft_holders[nft['nft_id']] = get_nft_owner_addresses(nft['nft_id'],nft['minter_address'],nft['token_address'])
                    nft_id_list.append(nft['nft_id'])

            # for index,nft_id in enumerate(nft_id_list, start=1):
            #     if nft_id not in nft_holders:
            #         for nft_name,nft in pool_nfts.items():
            #             if nft['nft_id'] == nft_id:
            #                 nft_holders[nft['nftnft_idId']] = get_nft_owner_addresses(nft['nft_id'],nft['minter_address'],nft['token_address'])
            #                 print(f"auto_nft_role: {len(nft_holders[nft['nft_id']])} owner addresses found for NFT {nft_name} - NFT {index} of {len(nft_id_list)}")

            #         guild_auto_nft_roles[role_id]['qualifying_nft_list'].append(nft['nft_id'])
            #         if nft['nft_id'] not in nft_holders:
            #             nft_holders[nft['nft_id']] = get_nft_owner_addresses(nft['nft_id'],nft['minter'],nft['tokenAddress'])
        print(guild_nft_roles)
        # print(guild_auto_nft_roles)
        # guild_nft_roles[nft_role['id']]['nft_id_list'] = nft_id_list
    wallet_balances = {}
    for nft_role in guild_nft_roles:
        print(f"Processing NFT Role {nft_role['id']}")
        user_scores = {}
        target_roles=[]
        for role in guild.roles:
            if role.is_integration() or role.is_bot_managed():
                pass
            else:
                for role_list_id in nft_role['role_id_list']:
                    if role.id == int(role_list_id):
                        target_roles.append(role)
                        break
        if len(target_roles) != len(nft_role['role_id_list']):
            print(f"auto_nft_role: ERROR: role list mismatch ( {len(target_roles)} / {len(nft_role['role_id_list'])} )for {nft_role['id']}")
            break
        users_with_wallet=[]
        print("HERE1")
        for wallet in guild_wallets:
            print("HERE2")
            print(wallet)
            users_with_wallet.append(wallet['discord_user_id'])
            print("HERE2.1")
            
            if wallet['discord_userid'] not in user_scores:
                print("HERE2.1 YES ")
                user_scores[wallet['discord_userid']] = 0
            else:
                print("HERE2.1 NO ")
            print("HERE2.2")
                
            for nft_id in nft_role['nft_id_list']:
                print("HERE2.3")
                
                if wallet['address'] in nft_holders[nft_id]:
                    if wallet['address'] not in wallet_balances:
                        wallet_balances[wallet['address']]=get.user_nft_balance(get.user_info(wallet['address'])['accountId'])
                    for _,nft in wallet_balances[wallet['address']].items():
                        if nft['nft_id'] == nft_id:
                            # print(f"----> Found NFT Wallet CONTAINING NFT owned by {wallet['discord_userid']} {type(wallet['discord_userid'])}")
                            user_scores[wallet['discord_userid']] += int(nft['total'])
        print("HERE3")

        # for member in guild:
        for member in guild_members:
            print("HERE4")
            
            member_entitled_to_role = False
            if member.bot:
                continue
            tempscore=0
            if f'{member.id}' in user_scores:
                tempscore=user_scores[f'{member.id}']
            # print(f"member: {member.name}/{member.id} scored: {f'{member.id}' in user_scores} {tempscore}/{nft_role['quantity_min']}")

            if f"{member.id}" not in users_with_wallet:
                print(f"auto_nft_role: member: {member.name} FAILED : no registered wallets!")
            elif f'{member.id}' not in user_scores:
                print(f"auto_nft_role: member: {member.name} FAILED : has not been scored!")
            elif user_scores[f'{member.id}'] >= int(nft_role['quantity_min']):
                if nft_role['quantity_max'] == '-1' or user_scores[f'{member.id}'] <= int(nft_role['quantity_max']):
                    print(f"auto_nft_role: member: {member.name} PASSED ({user_scores[f'{member.id}']} / {nft_role['quantity_min']})")
                    member_entitled_to_role = True
                else:
                    print(f"auto_nft_role: member: {member.name} FAILED - Holds too many NFTS ({user_scores[f'{member.id}']} / {nft_role['quantity_max']})")
            elif user_scores[f'{member.id}'] < int(nft_role['quantity_min']):
                print(f"auto_nft_role: member: {member.name} FAILED - Does not hold enough NFTS ({user_scores[f'{member.id}']} / {nft_role['quantity_min']})")
            for target_role in target_roles:
                member_has_role=False
                for member_role in member.roles:
                    if member_role.id == target_role.id:
                        member_has_role=True
                        break
                if member_entitled_to_role:
                    if not member_has_role: # Assign the role
                        role_assignments_output=(f"{role_assignments_output}\n - Adding role {target_role.name} to {member.name}")
                        if not dry_run:
                            await member.add_roles(target_role)
                    elif debug: # Do nothing
                        print(f"debug: {nft_role['id']} no changes needed for member: {member.name}, already has role {target_role.name}. {nft_role['quantity_min']} NFTS needed , and user scored {tempscore}")

                elif not member_entitled_to_role:
                    if member_has_role: # Remove the role
                        role_assignments_output=(f"{role_assignments_output}\n - auto_nft_role: Removing role {target_role.name} from {member.name}")
                        if not dry_run:
                            await member.remove_roles(target_role)
                    elif debug:
                        print(f"debug: {nft_role['id']} no changes needed for member: {member.name}, does not have role {target_role.name}. {nft_role['quantity_min']} NFTS needed , and user scored {tempscore}")

    print(f"- - - - - RUN COMPLETE ON GUILD {guild.name} Dry Run:{dry_run} - - - - -")
    print(role_assignments_output)

class auto_nft_role(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.checked_messages = []

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog Loaded : "+__file__)
        self.myLoop.start()

    @tasks.loop(hours = 1) # repeat after every 10 mins
    async def myLoop(self):
        loop_handler = AsyncLoopThread()
        loop_handler.start()


        guild_id_list=nft_db.get_nft_role_guilds()
        guild_list=[]
        for guild in self.client.guilds:
            print(f"auto_nft_role: {guild.name} active={f'{guild.id}' in guild_id_list}")
            if f"{guild.id}" in guild_id_list:
                guild_list.append(guild)

        for guild in guild_list:
            print(f'Add {guild.name} to the role processing loop')
            guild_members = await guild.fetch_members().flatten()
            asyncio.run_coroutine_threadsafe(auto_manage_nft_roles(guild,guild_members), loop_handler.loop)

def setup(client):
    client.add_cog(auto_nft_role(client))
