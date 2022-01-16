# Copyright 2022 stupidbot.
# Use of this source code is governed by the WTFPL
# license that can be found in the LICENSE file.

from dataclasses import dataclass
import os
import json
from typing import Union

import terra_sdk
from terra_sdk.client.lcd import LCDClient


from flipside_toolchain import __DATA_PATH__


@dataclass
class TokenInformation:
    name: str
    contract_address: str
    decimals: int
    symbol: str
    asset_address: str = ''


class AddressFetcher:
    """Helper class
    Fetching necessary info about contract for reverse mapping wormhole asset_address back into terra contract address.
    """
    CHAIN_ID: str = 'columbus-5'
    LCD_URL: str = 'https://lcd.terra.dev'

    def __init__(self, path_to_wormhole_json: str = __DATA_PATH__ + '/wormhole/terra.json'):
        # Instantiate client
        self.c = LCDClient(chain_id=self.CHAIN_ID, url=self.LCD_URL)
        try:
            assert os.path.isfile(path_to_wormhole_json), FileNotFoundError
            with open(path_to_wormhole_json, 'r') as f:
                self.wormhole_db = json.load(f)
                self.contract_list = self.wormhole_db['token_contract']
                self.token_contract_db = self.wormhole_db['token_contract_meta']
        except Exception as e:
            print("Exception caught while loading database, initialize empty database")
            self.contract_list = list()
            self.token_contract_db = dict()
            self.wormhole_db = {
                'token_contract': self.contract_list,
                'token_contract_meta': self.token_contract_db,
            }


    def setup_database(self):
        from tqdm import tqdm
        self.db = dict()
        self.export_db  = dict()
        fillnull = lambda sym, caddr: caddr if sym == '' else sym
        for contract in tqdm(self.contract_list):
            info = terra_sdk.client.lcd.api.wasm.WasmAPI(self.c).contract_info(contract)
            self.asset_db[info['init_msg'].get(['asset_address'], 'UNK')] = {
                'name': info['init_msg'].get('name', ''),
                'symbol': fillnull(info['init_msg'].get['symbol'], info['address']),
                'decimals': info['init_msg'].get('decimals'),
                'contract_address': info['address'],
                'asset_address': info['init_msg']['asset_address']
            }
            self.token_contract_db[info['address']] = {
                'name': info['init_msg']['name'],
                'asset_address': info['init_msg']['asset_address'],
                'decimals': info['init_msg']['decimals'],
                'symbol': info['init_msg']['symbol']
            }

    def asset_match(self, asset_address):
        try:
            return self.asset_db[asset_address]
        except:
            return {
                'symbol': asset_address,
                'decimals': 0,
                'contract_address': '',
                'asset_address': asset_address
            }
    
    def _get_info_token_dict(self, info_dict: dict):
        return {
            'name': info_dict.get('name'),
            'asset_address': info_dict.get('asset_address'),
            'decimals': info_dict.get('decimals'),
            'symbol': info_dict.get('symbol')
        }

    def token_contract_lookup(self, contract_address: str) -> Union[TokenInformation, None]:
        """ Lookup contract, return token information.
        """
        def _lookup():
            info = terra_sdk.client.lcd.api.wasm.WasmAPI(self.c).contract_info(contract_address)
            if info.get('init_msg') is None:
                return None
            meta = info['init_msg']
            info['name'] = meta.get('name')
            info['decimals'] = meta.get('decimals')
            info['asset_address'] = meta.get('asset_address', '')
            info['symbol'] = meta.get('symbol', '')
            if info['decimals'] is None: return None # Not a currency
            self.contract_list.append(contract_address)
            self.token_contract_db[contract_address] = {
                'name': info['name'],
                'asset_address': info['asset_address'],
                'decimals': info['decimals'],
                'symbol': info['symbol']
            }
            return info

        token_info = self.token_contract_db.get(
            contract_address, _lookup()
        )
        if token_info is None: return None
        return TokenInformation(
            contract_address=contract_address,
            **self._get_info_token_dict(token_info)
        )