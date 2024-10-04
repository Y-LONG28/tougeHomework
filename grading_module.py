# grading_module.py

import tkinter as tk
from tkinter import messagebox, scrolledtext
from api import get_homework_list, get_homework_id_by_number
import re
import requests
import time
from utils import generate_signature
import json

def assist_grading(root, session):
    # 创建辅助批改界面
    window = tk.Toplevel(root)
    window.title("辅助批改")
    window.geometry("600x600")

    # 步骤1：输入课程ID、作业编号、学生序号范围
    tk.Label(window, text="课程ID:").grid(row=0, column=0, padx=10, pady=5)
    courses_id_entry = tk.Entry(window)
    courses_id_entry.grid(row=0, column=1)

    tk.Label(window, text="作业编号:").grid(row=1, column=0, padx=10, pady=5)
    homework_number_entry = tk.Entry(window)
    homework_number_entry.grid(row=1, column=1)

    tk.Label(window, text="学生序号范围（起始）:").grid(row=2, column=0, padx=10, pady=5)
    start_index_entry = tk.Entry(window)
    start_index_entry.grid(row=2, column=1)

    tk.Label(window, text="学生序号范围（结束）:").grid(row=3, column=0, padx=10, pady=5)
    end_index_entry = tk.Entry(window)
    end_index_entry.grid(row=3, column=1)

    # 2. 输入评分要求，添加滚动条
    tk.Label(window, text="评分要求:").grid(row=4, column=0, padx=10, pady=5)
    requirements_frame = tk.Frame(window)
    requirements_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=5)
    requirements_text = scrolledtext.ScrolledText(requirements_frame, width=50, height=10)
    requirements_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # 使评分要求文本框响应鼠标滚轮事件
    def _on_mousewheel(event):
        requirements_text.yview_scroll(int(-1*(event.delta/120)), "units")
        return "break"  # 防止事件向上传递

    requirements_text.bind_all("<MouseWheel>", _on_mousewheel)

    # 3. 确认按钮，进入评分界面
    def confirm_parameters():
        # 获取输入的参数
        courses_id = courses_id_entry.get()
        homework_number = homework_number_entry.get()
        start_index = start_index_entry.get()
        end_index = end_index_entry.get()
        requirements = requirements_text.get("1.0", tk.END)

        # 输入验证
        if not courses_id or not homework_number or not start_index or not end_index or not requirements.strip():
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

        # 获取作业批次ID
        category_id = get_homework_id_by_number(user_session, courses_id, homework_number)
        if category_id:
            # 获取学生作业列表
            student_work_ids = get_homework_list(user_session, courses_id, category_id)
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

            # 进入评分界面
            grading_window = tk.Toplevel(window)
            grading_window.title("评分界面")
            grading_window.geometry("600x600")
            grading_process(grading_window, user_session, courses_id, category_id, student_numbers, student_number_to_id, requirements)
        else:
            messagebox.showerror("错误", "无法获取作业批次ID")

    confirm_button = tk.Button(window, text="确认", command=confirm_parameters)
    confirm_button.grid(row=6, column=0, columnspan=2, pady=10)

def grading_process(window, session, courses_id, category_id, student_numbers, student_number_to_id, requirements):
    # 选择要评分的学生
    tk.Label(window, text="请选择要评分的学生:").pack(pady=5)
    student_var = tk.StringVar(window)
    student_var.set(student_numbers[0])  # 默认选择第一个学生

    student_menu = tk.OptionMenu(window, student_var, *student_numbers)
    student_menu.pack(pady=5)

    # 显示评分要求，并生成评分输入框
    tk.Label(window, text="评分要求:").pack(pady=5)
    requirement_lines = requirements.strip().split('\n')

    score_entries = []  # 保存每个题目的得分输入框

    # 创建一个带滚动条的画布，用于放置评分输入框
    frame_canvas = tk.Canvas(window)
    frame_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = tk.Scrollbar(window, orient=tk.VERTICAL, command=frame_canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    frame_canvas.configure(yscrollcommand=scrollbar.set)

    frame_inner = tk.Frame(frame_canvas)
    frame_canvas.create_window((0, 0), window=frame_inner, anchor='nw')

    def on_frame_configure(event):
        frame_canvas.configure(scrollregion=frame_canvas.bbox("all"))

    frame_inner.bind("<Configure>", on_frame_configure)

    # 使 Canvas 响应鼠标滚轮事件
    def _on_mousewheel(event):
        frame_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        return "break"

    frame_canvas.bind_all("<MouseWheel>", _on_mousewheel)

    for line in requirement_lines:
        if "得分（总分" in line:
            # 提取总分
            match = re.search(r'得分（总分\s*(\d+)\s*）', line)
            if match:
                total_score = int(match.group(1))
                # 创建题目标签和得分输入框
                tk.Label(frame_inner, text=line).pack(anchor='w')
                score_entry = tk.Entry(frame_inner)
                score_entry.pack(anchor='w')
                score_entry.insert(0, str(total_score))  # 默认得满分
                score_entries.append((score_entry, total_score))
        else:
            tk.Label(frame_inner, text=line).pack(anchor='w')

    # 额外评语输入框
    tk.Label(window, text="额外评语:").pack(pady=5)
    comment_text = scrolledtext.ScrolledText(window, width=50, height=5)
    comment_text.pack(pady=5)

    # 显示总分的标签
    total_score_label = tk.Label(window, text="总分：0")
    total_score_label.pack(pady=5)

    # 计算总分的函数
    def calculate_total_score():
        total = 0
        for entry, max_score in score_entries:
            try:
                score = float(entry.get())
                if score > max_score:
                    messagebox.showwarning("警告", f"得分不能超过总分（{max_score}）")
                    entry.delete(0, tk.END)
                    entry.insert(0, str(max_score))
                    score = max_score
                total += score
            except ValueError:
                messagebox.showwarning("警告", "请输入有效的得分")
                return
        total_score_label.config(text=f"总分：{total}")

    # 在每个得分输入框失去焦点时计算总分
    for entry, _ in score_entries:
        entry.bind("<FocusOut>", lambda event: calculate_total_score())




    # 提交评阅的函数
    def submit_review():
        # 获取当前选择的学生编号和对应的ID
        student_number = student_var.get()
        student_id = student_number_to_id.get(student_number)
        if not student_id:
            messagebox.showerror("错误", "未找到对应的学生ID")
            return

        # 获取各题得分
        scores = []
        for i, (entry, max_score) in enumerate(score_entries):
            try:
                score = float(entry.get())
                if score > max_score:
                    messagebox.showwarning("警告", f"第 {i+1} 题得分不能超过总分（{max_score}）")
                    return
                scores.append(score)
            except ValueError:
                messagebox.showwarning("警告", f"第 {i+1} 题请输入有效的得分")
                return
        # 获取额外评语
        comment = comment_text.get("1.0", tk.END).strip()

        # 组合完整的评语，包括评分要求、各题得分、总分和额外评语
        total_score = sum(scores)
        full_comment = "评分结果：\n"
        idx = 0
        for line in requirement_lines:
            if "得分（总分" in line:
                full_comment += f"{line}：{scores[idx]}分\n"
                idx += 1
            else:
                full_comment += line + "\n"
        full_comment += f"\n总分：{total_score}\n"
        full_comment += f"评语：{comment}\n"

        # 提交评阅
        success = submit_review_to_server(session, student_id, courses_id, category_id, total_score, full_comment)
        if success:
            messagebox.showinfo("成功", f"已提交对学生 {student_number} 的评阅")
        else:
            messagebox.showerror("错误", f"提交评阅失败，学生：{student_number}")

    submit_button = tk.Button(window, text="提交评阅", command=submit_review)
    submit_button.pack(pady=10)


def get_zzud_value(session):
    zzud = session.cookies.get('zzud')
    if zzud:
        return zzud
    else:
        # 如果 Cookies 中没有，可以尝试从其他地方获取
        return 'prvul23zw'  # 或者使用捕获到的值（不推荐）
    
# 提交评阅的函数
def submit_review_to_server(session, student_id, courses_id, category_id, total_score, comment):
    # 构造请求URL
    review_api_url = f'https://data.educoder.net/api/student_works/{student_id}/add_score.json'

    # 获取或生成 zzud 参数
    zzud = get_zzud_value(session)

    # 构造完整的请求URL，包含查询参数 zzud
    review_api_url_with_params = f'{review_api_url}?zzud={zzud}'

    timestamp = int(time.time() * 1000)
    method = 'POST'
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
        'Referer': f'https://www.educoder.net/classrooms/{courses_id}/common_homework/{category_id}/review/{student_id}'
    }

    # 构造请求载荷（Payload）
    payload = {
        "score": total_score,
        "comment": comment,
        "userId": str(student_id)
    }

    # 发送 POST 请求
    response = session.post(review_api_url_with_params, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        result = response.json()
        if result.get('status') == 0:
            return True
        else:
            print('提交失败：', result.get('message', '未知错误'))
            return False
    else:
        print('请求失败，状态码：', response.status_code)
        return False
