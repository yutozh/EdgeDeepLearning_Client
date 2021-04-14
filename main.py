import asyncio
import socketio
import jwt
import json
import requests
import traceback
import time
from ping import ping
from task import docker_run, docker_stop, docker_download_file
from utils import console_log, console_init
import argparse
import signal
import os

from device import getDeviceInfo, getRealtimeDeviceInfo
sio = socketio.AsyncClient()

jwt_key = ''
uid = ''
args = ''
running_container = {}

@sio.event
async def connect():
    console_log('服务器通信链路已建立', 2)


@sio.event
async def new_task(data):
    global args, running_container, uid
    console_log('接收到新的任务：{}'.format(data["name"]), 3)
    mid = data.get("mid", '')
    try:
        if mid == '':
            raise Exception('缺少ID, 任务 {} 无效'.format(data["name"]))
        if data["format"] == "Docker镜像":
            # 指定名字，并添加到全局变量running_container中，方便停止
            container_name = "container_" + str(mid)
            running_container[mid] = container_name
            res = await docker_download_file(data["path"], args.log_file)
            if res:
                if await docker_run(data["cmd"], container_name, args.log_file):
                    console_log('训练任务启动成功', 2)
                    await sio.emit('task_states_update', {'uid': uid, 'mid': mid, 'status': '1'})
                    return
            # 启动失败
            raise Exception('训练任务启动失败')
        else:
            raise Exception('不支持的任务类型：{}'.format(data["format"]))
    except Exception as e:
        console_log(str(e), 1)
        await sio.emit('task_states_update', {'uid': uid, 'mid': mid, 'status': '-2'})


@sio.event
async def stop_task(data):
    global args, uid
    console_log('停止任务：{}'.format(data["name"]), 3)
    mid = data.get("mid", '')
    try:
        if mid == '':
            raise Exception('缺少ID, 停止任务 {} 失败'.format(data["name"]))

        container_name = running_container.get(mid, '')
        if container_name != '':
            running_container.pop(mid, '')
            if await docker_stop(container_name):
                console_log('训练任务停止成功', 2)
                await sio.emit('task_states_update', {'uid': uid, 'mid': mid, 'status': '-1'})
                return
            raise Exception('训练任务停止失败')
        raise Exception('没有找到训练任务： {}'.format(data["name"]))
    except Exception as e:
        console_log(str(e), 1)
        await sio.emit('task_states_update', {'uid': uid, 'mid': mid, 'status': '-1'})

@sio.event
async def reboot():
    console_log('执行重启指令...', 1)
    os.system("docker rm $(docker ps -aq)")
    await sio.sleep(5)
    os.system("reboot")

@sio.event
async def disconnect():
    console_log('服务器通信链路中断，尝试重连中...', 1)

async def main():
    global running_container
    await sio.connect(args.BASE_URL)
    while True:
        try:
            info = getRealtimeDeviceInfo()
            info["ping"] = ping(args.host)
            info["uid"] = uid
            info["running"] = len(running_container)

            if sio.connected:
                console_log("CPU: {:d}%  MEM: {:.1f}%  PING: {:.1f}ms".format(
                    int(info["cpu_ing"]), float(info["memory_ing"])/float(info["memory"]), float(info["ping"])))
                await sio.emit('heart', info)
            await sio.sleep(5)
        except asyncio.CancelledError:
            print("Got CancelledError")
            break
        except Exception as e:
            print("Exception:: ", e)
            await sio.disconnect()
            break
    await sio.wait()


def register():
    global jwt_key, uid
    try:
        console_log("获取设备信息...")
        info = getDeviceInfo()
        console_init(info)
        console_log("设备注册中... (服务器IP: {})".format(args.host))
        response = requests.post(url=args.REGISTER_URL,
                                 headers={'Content-Type': 'application/json'},
                                 data=json.dumps(info))

        if response.json().get("result", "") != 0:
            console_log("注册失败,请重试", 1)
            exit()
        else:
            jwt_key = response.json().get("value", "")
            uid = response.json().get("uid", "")
            console_log("注册成功 (UID: {})".format(uid), 2)
    except Exception as e:
        console_log("注册失败,请重试 [{}]".format(e), 1)
        # traceback.print_exc()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Training Client')
    parser.add_argument("--host", default='localhost', help="HOST IP")
    parser.add_argument("-p","--port", default='8088', help="HOST PORT")
    parser.add_argument("-l","--log_file", default="client.log", help="Log output file")

    args = parser.parse_args()

    args.BASE_URL = "http://" + args.host + ":" + str(args.port)
    args.REGISTER_URL = args.BASE_URL + '/api/device/register'

    cnt = 0
    while True:
        try:
            register()
            asyncio.run(main())
        except KeyboardInterrupt:
            exit(1)
        except Exception as e:
            cnt += 1
            if cnt < 10:
                time.sleep(10)
                console_log(e, 1)
            else:
                os.system("reboot")
