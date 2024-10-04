# download_module.py

import tkinter as tk
from tkinter import filedialog, messagebox
from api import get_homework_list, get_homework_id_by_number
from downloader import download_files
import os

def download_homework(root, session):
    # 创建下载界面
    download_window = tk.Toplevel(root)
    download_window.title("作业下载")
    download_window.geometry("500x300")

    # 步骤1：输入课程ID、作业编号
    tk.Label(download_window, text="课程ID:").grid(row=0, column=0, padx=10, pady=5, sticky='e')
    courses_id_entry = tk.Entry(download_window)
    courses_id_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(download_window, text="作业编号:").grid(row=1, column=0, padx=10, pady=5, sticky='e')
    homework_number_entry = tk.Entry(download_window)
    homework_number_entry.grid(row=1, column=1, padx=10, pady=5)

    # 步骤2：选择下载路径
    tk.Label(download_window, text="下载路径:").grid(row=2, column=0, padx=10, pady=5, sticky='e')
    download_path_entry = tk.Entry(download_window, width=30)
    download_path_entry.grid(row=2, column=1, padx=10, pady=5)

    def select_download_path():
        path = filedialog.askdirectory()
        if path:
            download_path_entry.delete(0, tk.END)
            download_path_entry.insert(0, path)

    select_path_button = tk.Button(download_window, text="选择路径", command=select_download_path)
    select_path_button.grid(row=2, column=2, padx=5, pady=5)

    # 步骤3：输入学生序号范围
    tk.Label(download_window, text="学生序号范围（起始）:").grid(row=3, column=0, padx=10, pady=5, sticky='e')
    start_index_entry = tk.Entry(download_window)
    start_index_entry.grid(row=3, column=1, padx=10, pady=5)

    tk.Label(download_window, text="学生序号范围（结束）:").grid(row=4, column=0, padx=10, pady=5, sticky='e')
    end_index_entry = tk.Entry(download_window)
    end_index_entry.grid(row=4, column=1, padx=10, pady=5)

    # 开始下载按钮
    def start_download():
        # 获取输入的参数
        courses_id = courses_id_entry.get()
        homework_number = homework_number_entry.get()
        download_path = download_path_entry.get()
        start_index = start_index_entry.get()
        end_index = end_index_entry.get()

        # 输入验证
        if not courses_id or not homework_number or not download_path or not start_index or not end_index:
            messagebox.showwarning("警告", "请填写所有字段")
            return

        try:
            homework_number = int(homework_number)
            start_index = int(start_index)
            end_index = int(end_index)
        except ValueError:
            messagebox.showwarning("警告", "作业编号和序号范围必须是整数")
            return

        if not os.path.exists(download_path):
            messagebox.showwarning("警告", "下载路径不存在")
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

            for index in range(start_index - 1, end_index):
                if index < len(student_work_ids):
                    student_id = student_work_ids[index]
                    student_download_path = os.path.join(download_path, f'stu{index + 1}')
                    print(f'下载学生 (ID: {student_id}) 的作业...')
                    download_files(user_session, student_id, student_download_path, courses_id, category_id)
                else:
                    print(f'序号 {index + 1} 超出学生列表范围')
            messagebox.showinfo("完成", "作业下载完成")
        else:
            messagebox.showerror("错误", "无法获取作业批次ID")

    download_button = tk.Button(download_window, text="开始下载", width=15, command=start_download)
    download_button.grid(row=5, column=0, columnspan=3, pady=20)
