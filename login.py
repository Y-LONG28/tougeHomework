import requests
import json
import time
from utils import generate_signature

def login(username, password):
    login_url = 'https://data.educoder.net/api/accounts/login.json'
    method = 'POST'
    timestamp = int(time.time() * 1000)

    mi_encoded = "WlRsa1pEVmlORE15TW1ZNVpqZGtPRE5rTURBNVpHVTVZbVpoTVRBd1l6TT0="
    hw_encoded = "TW1VelpHRXdObUZsTWpaaVlUbG1OelpoTldRNFpETTFOVGMwTm1ZeVptVT0="

    signature = generate_signature(method, mi_encoded, hw_encoded, timestamp)

    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'X-EDU-Timestamp': str(timestamp),
        'X-EDU-Type': 'pc',
        'X-EDU-Signature': signature
    }

    payload = {
        'login': username,
        'password': password,
        'autologin': True
    }

    session = requests.Session()
    response = session.post(login_url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        result = response.json()
        if 'user_id' in result:
            print('登录成功')
            return session
        else:
            error_message = result.get('message', '未知错误')
            print('登录失败:', error_message)
    else:
        print('请求失败，状态码：', response.status_code)
        print('响应内容：', response.text)

    return None
