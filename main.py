import json
from login import login
from api import get_homework_list
from downloader import download_files
import os

# 读取配置文件
def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    config = load_config()
    
    username = config['username']
    password = config['password']
    courses_id = config['courses_id']
    category_id = config['category_id']
    base_download_path = config['base_download_path']
    start_index = config['start_index']
    end_index = config['end_index']

    session = login(username, password)
    if session:
        student_work_ids = get_homework_list(session, courses_id, category_id)
        for index in range(start_index - 1, end_index):
            if index < len(student_work_ids):
                student_id = student_work_ids[index]
                download_path = os.path.join(base_download_path, f'stu{index + 1}')
                print(f'下载学生 (ID: {student_id}) 的作业...')
                download_files(session, student_id, download_path, courses_id, category_id)
            else:
                print(f'序号 {index + 1} 超出学生列表范围')
    else:
        print('登录失败，程序终止')

if __name__ == '__main__':
    main()
