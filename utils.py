import base64
import hashlib

def get_key(encoded_key):
    first_decode = base64.b64decode(encoded_key).decode('utf-8')
    second_decode = base64.b64decode(first_decode).decode('utf-8')
    return second_decode

def generate_signature(method, mi_encoded, hw_encoded, timestamp):
    method_upper = method.upper()
    ak = get_key(mi_encoded)
    sk = get_key(hw_encoded)
    sign_str = f"method={method_upper}&ak={ak}&sk={sk}&time={timestamp}"
    sign_str_base64 = base64.b64encode(sign_str.encode('utf-8')).decode('utf-8')
    signature = hashlib.md5(sign_str_base64.encode('utf-8')).hexdigest()
    return signature
