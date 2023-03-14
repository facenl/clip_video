from flask import Flask, request, jsonify
import subprocess
from datetime import datetime
import uuid
import os
import sqlite3

app = Flask(__name__)


@app.route('/clip', methods=['POST'])
def clip_video():
    # 获取用户提交的信息
    user_id = request.form.get('user_id')
    video_url = request.form.get('video_url')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')  # 将用户提交的信息存储到数据库中
    conn = sqlite3.connect('clip.db')
    c = conn.cursor()
    task_id = str(uuid.uuid4())
    c.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?)",
              (task_id, user_id, video_url, start_time, end_time, datetime.now(), 'IN_PROGRESS'))
    conn.commit()
    conn.close()  # 剪辑视频
    output_filename = task_id + '.mp4'
    subprocess.call(['ffmpeg', '-i', video_url, '-ss', start_time, '-to', end_time, '-c', 'copy', output_filename])
    # 将新视频存储到服务器中
    with open(output_filename, 'rb') as f:
        file_data = f.read()
    os.remove(output_filename)
    # 更新任务状态
    conn = sqlite3.connect('clip.db')
    c = conn.cursor()
    c.execute("UPDATE tasks SET end_time=?, status=? WHERE id=?",
              (datetime.now(), 'COMPLETED', task_id))
    conn.commit()
    conn.close()
    # 返回新视频的URL
    return jsonify({'url': '/videos/' + task_id + '.mp4'})


@app.route('/progress/<task_id>', methods=['GET'])
def get_progress(task_id):
    # 查询任务进度
    conn = sqlite3.connect('clip.db')
    c = conn.cursor()
    c.execute("SELECT status FROM tasks WHERE id=?", (task_id,))
    status = c.fetchone()[0]
    conn.close()
    # 返回任务状态
    return jsonify({'status': status})


if __name__ == '__main__':
    # 创建数据库
    conn = sqlite3.connect('clip.db')
    c = conn.cursor()
    c.execute(
        '''CREATE TABLE tasks (id text, user_id text, video_url text, start_time text, end_time text, start_date text, end_date text, status text)''')
