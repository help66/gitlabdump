import os
import requests
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

# 配置区域
GITLAB_URL = ""  # 默认空，用户通过界面输入
ACCESS_TOKEN = ""  # 默认空，用户通过界面输入
LOCAL_SAVE_PATH = ""  # 默认空，用户选择路径

def get_gitlab_projects(url, token):
    """
    从 GitLab API 获取所有项目的克隆地址
    """
    headers = {"Authorization": f"Bearer {token}"}
    projects = []
    page = 1

    while True:
        api_url = f"{url}/api/v4/projects?per_page=100&page={page}&membership=true"
        response = requests.get(api_url, headers=headers)
        if response.status_code != 200:
            print(f"无法访问 API: {response.status_code}, {response.text}")
            break

        data = response.json()
        if not data:
            break

        for project in data:
            # 使用 API 返回的 http_url_to_repo 并替换 HTTPS
            http_url = project["http_url_to_repo"]
            clone_url = http_url.replace("https://", f"https://oauth2:{token}@")
            projects.append(clone_url)
        
        page += 1

    return projects

def clone_projects(projects, save_path, output_text):
    """
    使用 git clone 克隆项目到本地
    """
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    for repo_url in projects:
        project_name = repo_url.split("/")[-1].replace(".git", "")
        project_path = os.path.join(save_path, project_name)

        if os.path.exists(project_path):
            output_text.insert(tk.END, f"项目 {project_name} 已存在，跳过克隆...\n")
            output_text.yview(tk.END)
            continue

        output_text.insert(tk.END, f"正在克隆项目: {project_name}\n")
        output_text.yview(tk.END)
        try:
            # 执行 git clone 命令
            result = subprocess.run(
                ["git", "clone", repo_url, project_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',  # 强制使用 UTF-8 编码
                check=True
            )
            output_text.insert(tk.END, result.stdout + "\n")  # 打印标准输出
            output_text.yview(tk.END)
        except subprocess.CalledProcessError as e:
            output_text.insert(tk.END, f"克隆失败: {repo_url}\n错误输出: {e.stderr}\n")
            output_text.yview(tk.END)
        except UnicodeDecodeError as e:
            output_text.insert(tk.END, f"解码错误: {e}\n")
            output_text.yview(tk.END)

def select_folder():
    """
    打开文件夹选择对话框
    """
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_path.set(folder_selected)

def start_cloning():
    """
    启动克隆过程
    """
    global GITLAB_URL, ACCESS_TOKEN, LOCAL_SAVE_PATH

    GITLAB_URL = entry_gitlab_url.get()
    ACCESS_TOKEN = entry_access_token.get()
    LOCAL_SAVE_PATH = folder_path.get()

    if not GITLAB_URL or not ACCESS_TOKEN or not LOCAL_SAVE_PATH:
        messagebox.showerror("错误", "请确保填写所有信息并选择保存路径")
        return

    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, "正在获取项目克隆地址...\n")
    output_text.yview(tk.END)

    try:
        # 获取项目列表
        projects = get_gitlab_projects(GITLAB_URL, ACCESS_TOKEN)
        output_text.insert(tk.END, f"共找到 {len(projects)} 个项目。\n")
        output_text.yview(tk.END)

        # 克隆项目
        clone_projects(projects, LOCAL_SAVE_PATH, output_text)

        messagebox.showinfo("完成", "所有项目已克隆完成！")
    except Exception as e:
        messagebox.showerror("错误", f"发生错误: {str(e)}")

# 创建主窗口
root = tk.Tk()
root.title("GitLab 项目克隆工具")
root.geometry("600x400")

# GitLab URL 输入框
label_gitlab_url = tk.Label(root, text="GitLab URL:")
label_gitlab_url.pack(pady=5)
entry_gitlab_url = tk.Entry(root, width=50)
entry_gitlab_url.pack(pady=5)

# 访问令牌输入框
label_access_token = tk.Label(root, text="GitLab 访问令牌:")
label_access_token.pack(pady=5)
entry_access_token = tk.Entry(root, width=50)
entry_access_token.pack(pady=5)

# 保存路径选择框
label_save_path = tk.Label(root, text="选择保存路径:")
label_save_path.pack(pady=5)

folder_path = tk.StringVar()
entry_save_path = tk.Entry(root, textvariable=folder_path, width=50)
entry_save_path.pack(pady=5)

button_browse = tk.Button(root, text="浏览", command=select_folder)
button_browse.pack(pady=5)

# 开始克隆按钮
button_start = tk.Button(root, text="开始克隆", command=start_cloning)
button_start.pack(pady=10)

# 输出文本框
output_text = tk.Text(root, height=10, width=70)
output_text.pack(pady=10)

# 运行主循环
root.mainloop()
