import asyncio
import socketio
import jwt
import json
import requests
import traceback
import time
from ping import ping
from task import docker_run, docker_download_file
from utils import console_log, console_init
import argparse

from device import getDeviceInfo, getRealtimeDeviceInfo
sio = socketio.AsyncClient()

jwt_key = ''
uid = ''
args = ''

@sio.event
async def connect():
    console_log('服务器通信链路已建立', 2)


@sio.event
async def new_task(data):
    global args
    console_log('接收到新的任务：{}'.format(data["name"]), 3)
    if data["format"] == "Docker镜像":
        res = await docker_download_file(data["path"], args.log_file)
        if res: await docker_run(data["cmd"], args.log_file)
    await sio.emit('my response', {'response': 'my response'})

@sio.event
async def disconnect():
    console_log('服务器通信链路中断，尝试重连中...', 1)

async def main():
    await sio.connect(args.BASE_URL)
    while True:
        try:
            info = getRealtimeDeviceInfo()
            info["ping"] = ping(args.host)
            info["uid"] = uid

            if sio.connected:
                console_log("CPU: {:d}%  MEM: {:.1f}%  PING: {:.1f}ms".format(
                    int(info["cpu_ing"]), float(info["memory_ing"])/float(info["memory"]), float(info["ping"])))
                await sio.emit('heart', info)
            await sio.sleep(5)
        except asyncio.CancelledError:
            print("Got CancelledError")
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
    try:
        parser = argparse.ArgumentParser(description='Training Client')
        parser.add_argument("--host", default='localhost', help="HOST IP")
        parser.add_argument("-p","--port", default='8088', help="HOST PORT")
        parser.add_argument("-l","--log_file", default="client.log", help="Log output file")

        args = parser.parse_args()

        args.BASE_URL = "http://" + args.host + ":" + str(args.port)
        args.REGISTER_URL = args.BASE_URL + '/api/device/register'
        register()
        asyncio.run(main())
    except:
        exit(1)