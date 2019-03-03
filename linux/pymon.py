# encoding:utf-8
# !/usr/bin/env python
import psutil
import time
from threading import Lock
from flask import Flask, render_template
from flask_socketio import SocketIO

async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()

# 后台线程 产生数据，即刻推送至前端
def background_thread():
    count = 0
    diskioInfo1 = psutil.disk_io_counters()
    netioInfo1 = psutil.net_io_counters()
    interval = 3
    while True:
        socketio.sleep(interval)
        count += 1
        timeInfo = time.strftime('%M:%S', time.localtime())
        # 获取系统时间（只取分:秒）
        #cpus = psutil.cpu_percent(interval=None, percpu=True)
        tmp = psutil.cpu_times_percent(interval=None, percpu=False)
        cpuInfo = (tmp.user,tmp.system,tmp.nice,tmp.iowait,tmp.irq, tmp.softirq, tmp.steal, tmp.guest)
        tmp = psutil.virtual_memory()
        memInfo = (tmp.total/1024,tmp.available/1024,tmp.used/1024,tmp.free/1024,tmp.buffers/1024, tmp.cached/1024, tmp.shared/1024, tmp.slab/1024)
        diskioInfo2 = psutil.disk_io_counters()
        netioInfo2 = psutil.net_io_counters()
        diskioInfo = ((diskioInfo2.read_bytes - diskioInfo1.read_bytes)/interval/1024,(diskioInfo2.write_bytes - diskioInfo1.write_bytes)/interval/1024)
        netioInfo = ((netioInfo2.bytes_sent - netioInfo1.bytes_sent)/interval/1024, (netioInfo2.bytes_recv - netioInfo1.bytes_recv)/interval/1024)
        diskioInfo1 = diskioInfo2
        netioInfo1 = netioInfo2
        # 获取系统cpu使用率 non-blocking
        socketio.emit('server_response', {'time':timeInfo, 'cpu':cpuInfo, 'mem':memInfo, 'diskio':diskioInfo, 'netio':netioInfo,'count':count}, namespace='/test')
        # 注意：这里不需要客户端连接的上下文，默认 broadcast = True

@app.route('/')
def index():
    return render_template('index.html', async_mode=socketio.async_mode)

@socketio.on('connect', namespace='/test')
def test_connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(target=background_thread)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=False)
