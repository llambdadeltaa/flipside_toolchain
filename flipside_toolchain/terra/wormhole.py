import base64


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

    @staticmethod
    def parse_vaa(cls, vaa: str, address_matcher = None):
            # Load as bytearray

            #print (base64.b64decode(vaa).hex())
            vaa_arr = list(bytearray(base64.b64decode(vaa)))
            len_signatures = vaa_arr[cls.LEN_SIGNATURE_POS]
            
            body_offset = cls.HEADER_LEN + (len_signatures * cls.SIGNATURE_LEN)
            body_arr = vaa_arr[body_offset:]
            body_print = ''.join(list(map(lambda x: hex(x)[2:], body_arr)))
            #print((body_print))
            emitter_chain = body_arr[cls.EMITTER_CHAIN_POS:cls.EMITTER_CHAIN_POS+2]
            payload = body_arr[cls.PAYLOAD_POS:]

            # body payload - stuffs
            body_timestamp = body_arr[0:cls.TIMESTAMP_SIZE]
            body_nonce = body_arr[cls.TIMESTAMP_SIZE : cls.TIMESTAMP_SIZE+cls.NONCE_SIZE]
            body_emitter_chain = body_arr[cls.TIMESTAMP_SIZE+cls.NONCE_SIZE : cls.TIMESTAMP_SIZE+cls.NONCE_SIZE+cls.EMITTER_CHAIN_SIZE]
            body_emitter_address = body_arr[cls.TIMESTAMP_SIZE+cls.NONCE_SIZE+cls.EMITTER_CHAIN_SIZE : cls.TIMESTAMP_SIZE+cls.NONCE_SIZE+cls.EMITTER_CHAIN_SIZE+cls.EMITTER_ADDRESS_SIZE]
            body_sequence = body_arr[cls.TIMESTAMP_SIZE+cls.NONCE_SIZE+cls.EMITTER_CHAIN_SIZE+cls.EMITTER_ADDRESS_SIZE : cls.TIMESTAMP_SIZE+cls.NONCE_SIZE+cls.EMITTER_CHAIN_SIZE+cls.EMITTER_ADDRESS_SIZE+cls.SEQUENCE_SIZE]

            # payload - stuffs
            msg_payload = payload[cls.MSG_PAYLOAD_POS:]
            payload_print = ''.join(list(map(lambda x: hex(x)[2:], msg_payload)))
            #print((payload_print))
            amount = msg_payload[cls.AMOUNT_POS :cls.AMOUNT_POS + cls.AMOUNT_SIZE]
            amount = int.from_bytes(bytes(amount), 'big')
            token_addr = msg_payload[cls.TOKEN_ADDR_POS:cls.TOKEN_ADDR_POS + cls.TOKEN_ADDR_SIZE]
            recipient = msg_payload[cls.RECIPIENT_POS:cls.RECIPIENT_POS + cls.RECIPIENT_SIZE]
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
            fee = msg_payload[cls.FEE_POS:cls.FEE_POS+32]
            fee = int.from_bytes(bytes(fee), 'big')
            return {
                'BODY_TIMESTAMP' : int(''.join(list(map(lambda x: hex(x)[2:], body_timestamp))), 16),
                'BODY_NONCE' : int(''.join(list(map(lambda x: hex(x)[2:], body_nonce))), 16),
                'BODY_EMITTER_CHAIN' : int(''.join(list(map(lambda x: hex(x)[2:], body_emitter_chain))), 16),
                'BODY_EMITTER_ADDRESS' : '0x' + (''.join(list(map(lambda x: hex(x)[2:], body_emitter_address)))),
                'BODY_SEQUENCE' : int(''.join(list(map(lambda x: hex(x)[2:], body_sequence))), 16),
                'FROM_CHAIN': bytearr_to_int(emitter_chain[-1::-1]),
                'RECIPIENT': '0x' + base64_to_hex(recipient.decode()),
                'AMOUNT': amount,
                'CURRENCY': base64_to_hex(token_name),
                'FEE': fee
                }

parse_vaa = VAAParser.parse_vaa

def base64_to_hex(str):
    return base64.b64decode(str).hex()
    
def bytearr_to_int(arr):
    result = 0
    for i, v in enumerate(arr):
        result += v * (2**i)
    return result
