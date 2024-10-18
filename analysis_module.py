# analysis_module.py

import tkinter as tk
from tkinter import messagebox, filedialog
from api import get_homework_list, get_homework_id_by_number
import requests
import json
import re
import os
import pandas as pd
import time
from utils import generate_signature  # 假设您有一个生成签名的函数

def analyze_assignments(root, session):
    # 创建统计分析界面
    window = tk.Toplevel(root)
    window.title("统计分析")
    window.geometry("600x400")
    
    # 输入参数
    tk.Label(window, text="课程ID:").grid(row=0, column=0, padx=10, pady=5)
    courses_id_entry = tk.Entry(window)
    courses_id_entry.grid(row=0, column=1)
    courses_id_entry.insert(0, 'yrjif25m')  # 默认值，可根据需要修改

    tk.Label(window, text="作业编号:").grid(row=1, column=0, padx=10, pady=5)
    homework_number_entry = tk.Entry(window)
    homework_number_entry.grid(row=1, column=1)

    tk.Label(window, text="学生序号范围（起始）:").grid(row=2, column=0, padx=10, pady=5)
    start_index_entry = tk.Entry(window)
    start_index_entry.grid(row=2, column=1)

    tk.Label(window, text="学生序号范围（结束）:").grid(row=3, column=0, padx=10, pady=5)
    end_index_entry = tk.Entry(window)
    end_index_entry.grid(row=3, column=1)

    # 导出路径
    tk.Label(window, text="保存路径:").grid(row=4, column=0, padx=10, pady=5)
    save_path_entry = tk.Entry(window, width=40)
    save_path_entry.grid(row=4, column=1)

    def select_save_path():
        path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel文件', '*.xlsx')])
        if path:
            save_path_entry.delete(0, tk.END)
            save_path_entry.insert(0, path)

    select_path_button = tk.Button(window, text="选择路径", command=select_save_path)
    select_path_button.grid(row=4, column=2, padx=5, pady=5)

    # 确认按钮
    def start_analysis():
        # 获取输入的参数
        courses_id = courses_id_entry.get()
        homework_number = homework_number_entry.get()
        start_index = start_index_entry.get()
        end_index = end_index_entry.get()
        save_path = save_path_entry.get()

        # 输入验证
        if not courses_id or not homework_number or not start_index or not end_index or not save_path:
            messagebox.showwarning("警告", "请填写所有字段")
            return

        try:
            homework_number = int(homework_number)
            start_index = int(start_index)
            end_index = int(end_index)
        except ValueError:
            messagebox.showwarning("警告", "作业编号和序号范围必须是整数")
            return

        if start_index > end_index:
            messagebox.showwarning("警告", "起始序号不能大于结束序号")
            return

        # 使用共享的会话
        user_session = session.get('session')
        if not user_session:
            messagebox.showerror("错误", "会话不存在，请重新登录")
            return

        # 执行统计分析
        analyze_scores(user_session, courses_id, homework_number, start_index, end_index, save_path)

    confirm_button = tk.Button(window, text="开始分析", command=start_analysis)
    confirm_button.grid(row=5, column=0, columnspan=3, pady=20)

def analyze_scores(session, courses_id, homework_number, start_index, end_index, save_path):
    # 获取作业批次ID
    category_id = get_homework_id_by_number(session, courses_id, homework_number)
    if not category_id:
        messagebox.showerror("错误", "无法获取作业批次ID")
        return

    # 获取学生作业列表
    student_work_ids = get_homework_list(session, courses_id, category_id)
    if not student_work_ids:
        messagebox.showerror("错误", "未找到学生作业列表")
        return

    # 处理指定范围内的学生
    selected_student_ids = student_work_ids[start_index - 1:end_index]
    student_number_to_id = {}
    student_numbers = []
    for idx, student_id in enumerate(selected_student_ids, start=start_index):
        student_number = f'stu{idx}'
        student_number_to_id[student_number] = student_id
        student_numbers.append(student_number)

    # 获取每个学生的评阅结果
    scores_data = {}
    max_scores = []  # 存储每道题的总分
    question_labels = []  # 存储每道题的标签，如"习题3.1-5"

    for student_number in student_numbers:
        student_id = student_number_to_id[student_number]
        # 获取评阅结果
        score_info = get_student_score_info(session, courses_id, category_id, student_id)
        if score_info:
            # 解析评阅结果，获取每题得分
            student_scores, max_score_list, labels = parse_score_info(score_info)
            scores_data[student_number] = student_scores
            # 更新 max_scores 和 question_labels
            if not max_scores:
                max_scores = max_score_list
                question_labels = labels
        else:
            # 未评阅，记录为空
            scores_data[student_number] = None

    # 统计分析
    if not max_scores:
        messagebox.showerror("错误", "未能获取到评分要求或评分数据")
        return

    # 创建 DataFrame
    columns = [f'{label}（总分{max_score}）' for label, max_score in zip(question_labels, max_scores)]
    df = pd.DataFrame(columns=columns, index=student_numbers)

    # 填充学生得分
    for student_number in student_numbers:
        scores = scores_data[student_number]
        if scores is None:
            df.loc[student_number] = ['未评阅'] * len(max_scores)
        else:
            df.loc[student_number] = scores

    # 计算错题人数百分比和得分百分比
    total_students = len(student_numbers)
    wrong_counts = []
    score_totals = []
    for i in range(len(max_scores)):
        total_score = max_scores[i] * total_students
        student_scores = df.iloc[:, i]
        # 将未评阅的学生排除
        valid_scores = student_scores[student_scores != '未评阅'].astype(float)
        total_earned = valid_scores.sum()
        wrong_count = (valid_scores != max_scores[i]).sum()
        wrong_percentage = wrong_count / total_students * 100
        score_percentage = total_earned / total_score * 100

        wrong_counts.append(f'{wrong_percentage:.2f}%')
        score_totals.append(f'{score_percentage:.2f}%')

    # 添加统计行
    df.loc['错题人数百分比'] = wrong_counts
    df.loc['得分百分比'] = score_totals

    # 导出到 Excel
    try:
        df.to_excel(save_path)
        messagebox.showinfo("成功", f"统计结果已保存到 {save_path}")
    except Exception as e:
        messagebox.showerror("错误", f"保存 Excel 文件失败：{e}")

def get_student_score_info(session, courses_id, category_id, student_id):
    # 构造请求URL
    # URL示例：https://data.educoder.net/api/student_works/{student_id}/comment_list.json?coursesId={courses_id}&categoryId={category_id}
    api_url = f'https://data.educoder.net/api/student_works/{student_id}/comment_list.json'
    params = {
        'coursesId': courses_id,
        'categoryId': category_id
    }

    # 构造请求头，包含时间戳、签名等
    timestamp = int(time.time() * 1000)
    method = 'GET'
    mi_encoded = "WlRsa1pEVmlORE15TW1ZNVpqZGtPRE5rTURBNVpHVTVZbVpoTVRBd1l6TT0="
    hw_encoded = "TW1VelpHRXdObUZsTWpaaVlUbG1OelpoTldRNFpETTFOVGMwTm1ZeVptVT0="

    signature = generate_signature(method, mi_encoded, hw_encoded, timestamp)

    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0',
        'X-EDU-Timestamp': str(timestamp),
        'X-EDU-Type': 'pc',
        'X-EDU-Signature': signature,
        'Pc-Authorization': session.cookies.get('_educoder_session'),
        'Referer': f'https://www.educoder.net/classrooms/{courses_id}/common_homework/{category_id}/review/{student_id}'
    }

    response = session.get(api_url, headers=headers, params=params)

    if response.status_code == 200:
        result = response.json()
        # 检查返回的数据是否正确
        if 'comment_scores' in result and result['comment_scores']:
            # 获取最新的评阅结果
            last_comment = result['comment_scores'][0]
            content = last_comment['content']
            return content
        else:
            return None
    else:
        print(f"获取学生 {student_id} 的评阅结果失败，状态码：{response.status_code}")
        return None

def parse_score_info(content):
    lines = content.strip().split('\n')
    scores = []
    max_scores = []
    labels = []  # 存储题目标签

    current_chapter = ''
    for line in lines:
        line = line.strip()
        # 检查是否是章节标题，如 "习题3.1"
        chapter_match = re.match(r'^习题.*', line)
        if chapter_match:
            current_chapter = line
            continue

        # 匹配每题的得分，如 "5    得分（总分4）：4.0分"
        match = re.search(r'^(\d+)\s*\.?\s*得分（总分\s*(\d+(\.\d+)?)\s*）\s*：\s*(\d+(\.\d+)?)分', line)
        if match:
            question_number = match.group(1)
            max_score = float(match.group(2))
            score = float(match.group(4))

            # 创建题目标签，如 "习题3.1-5"
            label = f"{current_chapter}-{question_number}"
            labels.append(label)
            max_scores.append(max_score)
            scores.append(score)
        else:
            # 如果行不匹配，可能是总分或评语，忽略
            continue
    return scores, max_scores, labels
