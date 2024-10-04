# main.py

import tkinter as tk
from tkinter import messagebox
from login import login
from download_module import download_homework
from grading_module import assist_grading

def main():
    # 创建主窗口
    root = tk.Tk()
    root.title("Educoder 助手")
    root.geometry("400x300")

    # 存储会话的全局变量
    session = {}

    # 用户名和密码标签及输入框
    tk.Label(root, text="用户名:").pack(pady=5)
    username_entry = tk.Entry(root)
    username_entry.pack(pady=5)

    tk.Label(root, text="密码:").pack(pady=5)
    password_entry = tk.Entry(root, show='*')
    password_entry.pack(pady=5)

    # 登录函数
    def perform_login():
        username = username_entry.get()
        password = password_entry.get()

        if not username or not password:
            messagebox.showwarning("警告", "请填写用户名和密码")
            return

        # 执行登录
        user_session = login(username, password)
        if user_session:
            messagebox.showinfo("成功", "登录成功")
            session['session'] = user_session
            # 启用功能按钮
            download_button.config(state=tk.NORMAL)
            grading_button.config(state=tk.NORMAL)
        else:
            messagebox.showerror("错误", "登录失败")

    # 登录按钮
    login_button = tk.Button(root, text="登录", width=15, command=perform_login)
    login_button.pack(pady=10)

    # 功能按钮
    download_button = tk.Button(root, text="作业下载", width=20,
                                command=lambda: download_homework(root, session), state=tk.DISABLED)
    download_button.pack(pady=10)

    grading_button = tk.Button(root, text="辅助批改", width=20,
                               command=lambda: assist_grading(root, session), state=tk.DISABLED)
    grading_button.pack(pady=10)

    root.mainloop()

if __name__ == '__main__':
    main()
