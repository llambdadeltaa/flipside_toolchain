
from warnings import warn
import os

import base64
import json
import bech32

from flipside_toolchain import __DATA_PATH__


__WORMHOLE_JSON_PATH__ = os.path.join(__DATA_PATH__, 'wormhole/terra.json')

class VAAParser:
    """
    Original: lambdadelta#7856
    Contributor: BinhaChon#0041(Fixed vary recipient_address), ant#8260 (Refactor + Tinker)
    WormholeMsg:
    Header
    byte        version                  (VAA Version)
    u32         guardian_set_index       (Indicates which guardian set is signing)
    u8          len_signatures           (Number of signatures stored)

    [][66]byte  signatures               (Collection of ecdsa signatures)

    Body:
    u32         timestamp
    u32         nonce
    u16         emitter_chain
    [32]byte    emitter_address
    u64         sequence
    u8          consistency_level
    []byte      payload

        Payload:
        u8 action
        [u8] payload

            Body:
            u256     amount
            [u8; 32] token_address
            u16      token_chain
            [u8; 40] recipient
            u16      recipient_chain
            u256     fee
    """
    VERSION_POS = 0
    HEADER_LEN = 6
    LEN_SIGNATURE_POS = 5
    SIGNATURE_LEN = 66

    EMITTER_CHAIN_POS = 8
    PAYLOAD_POS = 51

    MSG_PAYLOAD_POS = 1
    AMOUNT_POS = 0
    AMOUNT_SIZE = 32
    TOKEN_ADDR_POS = 32
    TOKEN_ADDR_SIZE = 40
    FEE_POS = 100
    RECIPIENT_POS = 66
    RECIPIENT_SIZE = 32

    TIMESTAMP_SIZE = 4
    NONCE_SIZE = 4
    EMITTER_CHAIN_SIZE = 2
    EMITTER_ADDRESS_SIZE = 32
    SEQUENCE_SIZE = 8

    def __init__(self, path_to_wormhole_json: str = __WORMHOLE_JSON_PATH__) -> None:
        with open(path_to_wormhole_json, 'r') as f:
            chain_dict = json.load(f)['wormhole_chain_id']
        self.chain_mapper = lambda chain_id: chain_dict[chain_id]

    def parse_vaa(self, vaa: str, address_matcher = None):
        """Parse vaa_data message into human-readable format
        """
        # Load as bytearray

        #print (base64.b64decode(vaa).hex())
        vaa_arr = list(bytearray(base64.b64decode(vaa)))
        len_signatures = vaa_arr[self.LEN_SIGNATURE_POS]
        
        body_offset = self.HEADER_LEN + (len_signatures * self.SIGNATURE_LEN)
        body_arr = vaa_arr[body_offset:]
        body_print = ''.join(list(map(lambda x: hex(x)[2:], body_arr)))
        #print((body_print))
        emitter_chain = body_arr[self.EMITTER_CHAIN_POS:self.EMITTER_CHAIN_POS+2]
        payload = body_arr[self.PAYLOAD_POS:]

        # body payload - stuffs
        body_timestamp = body_arr[0:self.TIMESTAMP_SIZE]
        body_nonce = body_arr[self.TIMESTAMP_SIZE : self.TIMESTAMP_SIZE+self.NONCE_SIZE]
        body_emitter_chain = body_arr[self.TIMESTAMP_SIZE+self.NONCE_SIZE : self.TIMESTAMP_SIZE+self.NONCE_SIZE+self.EMITTER_CHAIN_SIZE]
        body_emitter_address = body_arr[self.TIMESTAMP_SIZE+self.NONCE_SIZE+self.EMITTER_CHAIN_SIZE : self.TIMESTAMP_SIZE+self.NONCE_SIZE+self.EMITTER_CHAIN_SIZE+self.EMITTER_ADDRESS_SIZE]
        body_sequence = body_arr[self.TIMESTAMP_SIZE+self.NONCE_SIZE+self.EMITTER_CHAIN_SIZE+self.EMITTER_ADDRESS_SIZE : self.TIMESTAMP_SIZE+self.NONCE_SIZE+self.EMITTER_CHAIN_SIZE+self.EMITTER_ADDRESS_SIZE+self.SEQUENCE_SIZE]

        # payload - stuffs
        msg_payload = payload[self.MSG_PAYLOAD_POS:]
        payload_print = ''.join(list(map(lambda x: hex(x)[2:], msg_payload)))
        #print((payload_print))
        amount = msg_payload[self.AMOUNT_POS :self.AMOUNT_POS + self.AMOUNT_SIZE]
        amount = int.from_bytes(bytes(amount), 'big')
        token_addr = msg_payload[self.TOKEN_ADDR_POS:self.TOKEN_ADDR_POS + self.TOKEN_ADDR_SIZE]
        recipient = msg_payload[self.RECIPIENT_POS:self.RECIPIENT_POS + self.RECIPIENT_SIZE]
        recipient = base64.b64encode(bytes(recipient))

        token_name = ''.join(list(map(lambda x: chr(x), token_addr)))
        token_name = token_name[-5:].lstrip('\x00')
        if not token_name in ['uluna', 'uusd']:
            token_name = base64.b64encode(bytes(token_addr)).decode()
            if not address_matcher is None:
                info = address_matcher(token_name)
                token_name = info['symbol']
                amount /= (10 ** info['decimals'])
        else:
            _t = {'uluna': 'LUNA', 'uusd': 'UST'}
            token_name = _t[token_name]
            amount /= 1e6
        fee = msg_payload[self.FEE_POS:self.FEE_POS+32]
        fee = int.from_bytes(bytes(fee), 'big')
        try:
            recipient = hex_to_terra(base64_to_hex(recipient.decode()))
        except Exception as e:
            # Usually an asset_address specified here, causing an error.
            recipient = recipient.decode()
            warn('Unable to parse `recipient_address`. Maybe an asset_address')

        return {
            'BODY_TIMESTAMP' : int(''.join(list(map(lambda x: hex(x)[2:], body_timestamp))), 16),
            'BODY_NONCE' : int(''.join(list(map(lambda x: hex(x)[2:], body_nonce))), 16),
            'BODY_EMITTER_CHAIN_ID' : int(''.join(list(map(lambda x: hex(x)[2:], body_emitter_chain))), 16),
            'BODY_EMITTER_ADDRESS' : '0x' + (''.join(list(map(lambda x: hex(x)[2:], body_emitter_address)))),
            'BODY_SEQUENCE' : int(''.join(list(map(lambda x: hex(x)[2:], body_sequence))), 16),
            'FROM_CHAIN': self.chain_mapper(str(bytearr_to_int(emitter_chain[-1::-1]))),
            'RECIPIENT': recipient,
            'AMOUNT': amount,
            'CURRENCY_ADDRESS': token_name,
            'FEE': fee
            }

parse_vaa = VAAParser().parse_vaa

def base64_to_hex(base64str):
    return base64.b64decode(base64str).hex().lstrip('0') # Left strip is needed for correct address.

def hex_to_terra(hexstr):
    """credit: BinhaChon#0081""" 
    hexstr = bytearray.fromhex(hexstr)
    hexstr = bech32.convertbits(hexstr, 8, 5)
    hexstr = bech32.bech32_encode('terra', hexstr)
    return hexstr

    
def bytearr_to_int(arr):
    result = 0
    for i, v in enumerate(arr):
        result += v * (2**i)
    return result
