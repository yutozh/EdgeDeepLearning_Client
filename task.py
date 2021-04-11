import time
import asyncio
import traceback
from utils import console_log, console_init

async def run_cmd_output(cmd, log_file):
    try:
        with open(log_file, 'a+') as f:
            f.write("\n{}-{}\n".format(time.strftime('%Y-%m-%d %H:%M:%S'), cmd))
            ret = await asyncio.create_subprocess_shell(cmd, stdout=f, stderr=f)
        stdout, stderr  = await ret.communicate()
        return ret.returncode
    except Exception as e:
        traceback.print_exc()
        return False

async def docker_download_file(image_url, log_file):
    try:
        console_log("开始下载镜像", 3)
        res = await run_cmd_output("docker pull {}".format(image_url), log_file)
        if res == 0:
            console_log("镜像下载完成", 3)
            return True
        else:
            console_log("镜像下载失败", 1)
    except Exception as e:
        console_log("镜像下载失败: " + str(e), 1)
    return False

async def docker_run(cmd, log_file):
    try:
        console_log("模型训练启动", 3)
        res = await run_cmd_output(cmd, log_file)
        if res == 0:
            console_log("模型训练完成", 3)
        else:
            console_log("模型训练中断", 1)
    except Exception as e:
        console_log("启动镜像失败: " + str(e), 1)

if __name__ == '__main__':
    asyncio.run(run_cmd_output("docker pull hello-world"))