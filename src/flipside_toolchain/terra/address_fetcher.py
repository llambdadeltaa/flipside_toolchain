# Copyright 2022 stupidbot.
# Use of this source code is governed by the WTFPL
# license that can be found in the LICENSE file.

import json

import terra_sdk
from terra_sdk.client.lcd import LCDClient


class AddressFetcher:
    """Helper class
    Fetching necessary info about contract for reverse mapping wormhole asset_address back into terra contract address.
    """
    CHAIN_ID: str = 'columbus-5'
    LCD_URL: str = 'https://lcd.terra.dev'

    def __init__(self, path_to_wormhole_json: str = 'data/wormhole/terra.json'):
        # Instantiate client
        self.c = LCDClient(chain_id=self.CHAIN_ID, url=self.LCD_URL)
        with open(path_to_wormhole_json, 'r') as f:
            self.WORMHOLE_CONTRACT_LIST = json.load(f)['token_contract']

    def setup_database(self):
        from tqdm import tqdm
        self.db = dict()
        self.export_db  = dict()
        fillnull = lambda sym, caddr: caddr if sym == '' else sym
        for contract in tqdm(self.WORMHOLE_CONTRACT_LIST):
            info = terra_sdk.client.lcd.api.wasm.WasmAPI(self.c).contract_info(contract)
            self.db[info['init_msg']['asset_address']] = {
                'symbol': fillnull(info['init_msg']['symbol'], info['address']),
                'decimals': info['init_msg']['decimals'],
                'contract_address': info['address'],
                'asset_address': info['init_msg']['asset_address']
            }
            self.export_db[info['address']] = {
                'asset_address': info['init_msg']['asset_address'],
                'decimals': info['init_msg']['decimals'],
                'symbol': info['init_msg']['symbol']
            }

    def match(self, asset_address):
        try:
            return self.db[asset_address]
        except:
            return {
                'symbol': asset_address,
                'decimals': 0,
                'contract_addr': '',
                'asset_address': asset_address
            }