from multiprocessing import reduction
from urllib import response
import requests
import time
api_url='https://api3.loopring.io'
from keys_and_codes import loopring_api_key,debug

def api_call(api_call_data):
    
    if 'json' in api_call_data:
        r = requests.request(method=api_call_data['method'],url=f"{api_url}{api_call_data['url']}",headers=api_call_data['headers'],json=api_call_data['json'], timeout=10)
    else:
        r = requests.request(method=api_call_data['method'],url=f"{api_url}{api_call_data['url']}",headers=api_call_data['headers'],params=api_call_data['params'], timeout=10)

    if r.status_code == 200 or 'resultInfo' in r.json():
        return False,r.json()
    else:
        return True,r.status_code

def user_info(wallet_address):
    api_call_data= {
        'method': 'GET',
        'url': '/api/v3/account',
        'headers': None,
        'params': {'owner': wallet_address} # seems to e the maximum number for limit
    }
    failed,api_resp_data=api_call(api_call_data)
    if failed:
        return f'API Failure. HTTP {api_resp_data}'

    user_info_dict={}
    for key,val in api_resp_data.items():
        if key == 'publicKey':
            user_info_dict['publicKey']={}
            for key_name,key_value in val.items():
                user_info_dict['publicKey'][key_name]=key_value
        else:
            user_info_dict[key]=val
    
    return user_info_dict

def target_nft_data(target_nft):
    '''
    Inputs: target_nft dictionary with fields
        - minter_address
        - token_address
        - id

    Outputs: target_nft dictionary with appended data:
        - nftData
        - minter
        - nftType
        - tokenAddress
        - nftId
        - creatorFeeBips
        - royaltyPercentage
        - originalRoyaltyPercentage
        - status
        - nftFactory
        - nftOwner
        - nftBaseUri
        - royaltyAddress
        - originalMinter
        - createdAt
    '''
    api_call_data= {
        'method': 'GET',
        'url': '/api/v3/nft/info/nftData',
        'headers': None,
        'params': {'minter': target_nft['minter_address'], 'tokenAddress': target_nft['token_address'], 'nftId': target_nft['id']}
    }
    failed,api_resp_data=api_call(api_call_data)
    
    if failed:
        return f'API Failure. HTTP {api_resp_data}'
    else:
        nft_data=api_resp_data
        
    for key,val in nft_data.items():
        target_nft[key]=val
    return(target_nft)

def user_nft_balance(loopring_account_id):
    api_call_data= {
        'method': 'GET',
        'url': '/api/v3/user/nft/balances',
        'headers':{"X-API-KEY":loopring_api_key},
        'params': {'accountId': loopring_account_id, 'limit': "999999999"} # seems to e the maximum number for limit
    }
    failed,api_resp_data=api_call(api_call_data)
    nft_balance_dict={}
    if failed:
        return f'API Failure. HTTP {api_resp_data}'
    for nft in api_resp_data['data']:
        nft_balance_dict[nft['id']]={}
        for key,value in nft.items():
            nft_balance_dict[nft['id']][key]=value
    return(nft_balance_dict)
def target_nft_attrs(target_nft,list=False,holder_account=None):
    if debug:
        print(f"\ntarget_nft_attrs input:\n{target_nft}\n")
    if holder_account:
        account_id=holder_account
    else:
        account_id=target_nft['holder_account_id']
    print(f'account_id; {account_id}')
    api_call_data= {
        'method': 'GET',
        'url': '/api/v3/user/nft/balances',
        'headers':{"X-API-KEY":loopring_api_key},
        'params': {'accountId': account_id, 'limit': "999999999",'metadata': 'true'}
    }
    failed,api_resp_data=api_call(api_call_data)
    return_data=None
    if failed:
        return f'API Failure. HTTP {api_resp_data}'
    print(f'api_resp_data; {api_resp_data}')
    
    if list:
        index=0
        nft_dict={}
        nft_dict['data']={}
        nft_id_list=target_nft
        for nft in api_resp_data['data']:
            if nft['nftId'] in nft_id_list: # in nftIdList:
                nft_dict['data'][index]=nft
                index+=1
        return_data=nft_dict
    else:
        for nft in api_resp_data['data']:
            print(f'nft: {nft}')
            
            print(f"wallet nft id: {target_nft['id']}")
            if target_nft['id'] == nft['nftId']: # in nftIdList:
                for attr,val in nft.items():
                    target_nft[attr]=val
                return_data=target_nft
    if debug:
        print(f"\ntarget_nft_attrs returning:\n{return_data}\n")
    return return_data
        
def token_storage_id(target_nft):
    api_call_data= {
        'method': 'GET',
        'url': '/api/v3/storageId',
        'headers':{"X-API-KEY":loopring_api_key},
        'params': {'accountId': target_nft['holder_account_id'], 'sellTokenId': target_nft['tokenId']}
    }
    failed,api_resp_data=api_call(api_call_data)

    if failed:
        return f'API Failure. HTTP {api_resp_data}'
    target_nft['storage_id']={}
    for key,val in api_resp_data.items():  
        target_nft['storage_id'][key]=val
    return target_nft['storage_id']

def transfer_fees(plgr_data):
    api_call_data= {
        'method': 'GET',
        'url': '/api/v3/user/offchainFee', #     url="https://uat2.loopring.io/api/v3/user/offchainFee",
        'headers':{"X-API-KEY":loopring_api_key},
        'params': {'accountId': plgr_data['target_user']['account_id'],"requestType": 3,"tokenSymbol": "LRC"}
    }
    failed,api_resp_data=api_call(api_call_data)

    if failed:
        return f'API Failure. HTTP {api_resp_data}'
    else:
        fees_dict={}
        for key, val in api_resp_data.items():
            if key == 'fees':
                for _token in api_resp_data['fees']:
                    token = _token['token']
                    fees_dict[token]={}
                    for key,val in _token.items():
                        if key != 'token':
                            fees_dict[token][key]=val
            else:
                fees_dict[key]=[val]
        return fees_dict

def last_transfer_status(account_id):
    api_call_data= {
        'method': 'GET',
        'url': '/api/v3/user/transfers',
        'headers':{"X-API-KEY":loopring_api_key},
        'params': {'accountId': account_id, "start": int(time.time()*1000 - 3 * 1000)} #, "tokenSymbol": "ETH"}
    }
    failed,api_resp_data=api_call(api_call_data)

    if failed:
        return f'API Failure. HTTP {api_resp_data}'
    last_transfer_status_dict={}
    for key,val in api_resp_data.items():  
        last_transfer_status_dict[key]=val
    return last_transfer_status_dict
