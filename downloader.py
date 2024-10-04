import requests
import os
import time
from utils import generate_signature

def download_files(session, student_id, download_path, courses_id, category_id):
    timestamp = int(time.time() * 1000)
    method = 'GET'
    mi_encoded = "WlRsa1pEVmlORE15TW1ZNVpqZGtPRE5rTURBNVpHVTVZbVpoTVRBd1l6TT0="
    hw_encoded = "TW1VelpHRXdObUZsTWpaaVlUbG1OelpoTldRNFpETTFOVGMwTm1ZeVptVT0="

    signature = generate_signature(method, mi_encoded, hw_encoded, timestamp)
    homework_api_url = f'https://data.educoder.net/api/student_works/{student_id}.json?coursesId={courses_id}&categoryId={category_id}&userId={student_id}&history_id=&zzud=prvul23zw'
    
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json; charset=utf-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'X-EDU-Timestamp': str(timestamp),
        'X-EDU-Type': 'pc',
        'X-EDU-Signature': signature,
        'Pc-Authorization': session.cookies.get('_educoder_session'),
        'Referer': f'https://www.educoder.net/classrooms/{courses_id}/common_homework/{category_id}/review/{student_id}'
    }
    
    response = session.get(homework_api_url, headers=headers)

    if response.status_code == 200:
        result = response.json()
        attachments = result.get('attachments', [])

        # 确保下载目录存在
        if not os.path.exists(download_path):
            os.makedirs(download_path)

        for attachment in attachments:
            download_url = attachment.get('download_url')
            title = attachment.get('title', '未命名文件')

            if download_url:
                pdf_response = session.get(f'https://data.educoder.net{download_url}')
                if pdf_response.status_code == 200:
                    filename = os.path.join(download_path, title)
                    with open(filename, 'wb') as f:
                        f.write(pdf_response.content)
                    print(f'已下载：{filename}')
                else:
                    print(f'下载文件失败，状态码：{pdf_response.status_code}，文件：{title}')
            else:
                print('未找到下载链接，文件：', title)
    else:
        print('获取作业信息失败，状态码：', response.status_code)
