import requests
import json
import time
from utils import generate_signature

def get_homework_list(session, courses_id, category_id):
    timestamp = int(time.time() * 1000)
    method = 'POST'
    mi_encoded = "WlRsa1pEVmlORE15TW1ZNVpqZGtPRE5rTURBNVpHVTVZbVpoTVRBd1l6TT0="
    hw_encoded = "TW1VelpHRXdObUZsTWpaaVlUbG1OelpoTldRNFpETTFOVGMwTm1ZeVptVT0="

    signature = generate_signature(method, mi_encoded, hw_encoded, timestamp)
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json; charset=utf-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'X-EDU-Timestamp': str(timestamp),
        'X-EDU-Type': 'pc',
        'X-EDU-Signature': signature,
        'Pc-Authorization': session.cookies.get('_educoder_session'),
        'Referer': f'https://www.educoder.net/classrooms/{courses_id}/common_homework/{category_id}/detail'
    }

    payload = {
        "coursesId": courses_id,
        "categoryId": category_id
    }

    homework_api_url = f'https://data.educoder.net/api/homework_commons/{category_id}/works_list.json?zzud=prvul23zw'
    response = session.post(homework_api_url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        result = response.json()
        student_work_ids = result.get("student_works_ids", [])
        return student_work_ids
    else:
        print('获取作业列表失败，状态码：', response.status_code)
        return []


def get_homework_id_by_number(session, courses_id, homework_number):
    timestamp = int(time.time() * 1000)
    method = 'GET'
    mi_encoded = "WlRsa1pEVmlORE15TW1ZNVpqZGtPRE5rTURBNVpHVTVZbVpoTVRBd1l6TT0="
    hw_encoded = "TW1VelpHRXdObUZsTWpaaVlUbG1OelpoTldRNFpETTFOVGMwTm1ZeVptVT0="

    signature = generate_signature(method, mi_encoded, hw_encoded, timestamp)

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json; charset=utf-8',
        'User-Agent': 'Mozilla/5.0',
        'X-EDU-Timestamp': str(timestamp),
        'X-EDU-Type': 'pc',
        'X-EDU-Signature': signature,
        'Pc-Authorization': session.cookies.get('_educoder_session'),
        'Referer': f'https://www.educoder.net/classrooms/{courses_id}/common_homework'
    }

    params = {
        'coursesId': courses_id,
        'id': courses_id,
        'limit': 20,
        'type': 1,
        'zzud': 'prvul23zw'
    }

    homework_list_url = f'https://data.educoder.net/api/courses/{courses_id}/homework_commons/list.json'

    response = session.get(homework_list_url, headers=headers, params=params)

    if response.status_code == 200:
        result = response.json()
        homeworks = result.get('homeworks', [])
        if homework_number - 1 < len(homeworks):
            homework = homeworks[homework_number - 1]
            category_id = str(homework.get('homework_id'))
            print(f"获取到第 {homework_number} 次作业的 category_id: {category_id}")
            return category_id
        else:
            print(f"作业编号 {homework_number} 超出范围，总共有 {len(homeworks)} 个作业。")
            return None
    else:
        print('获取作业列表失败，状态码：', response.status_code)
        return None