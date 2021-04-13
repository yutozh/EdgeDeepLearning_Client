import time
import asyncio
import traceback
from utils import console_log, console_init

async def run_cmd_output(cmd, log_file="client.log"):
    try:
        with open(log_file, 'a+') as f:
            f.write("\n{}-{}\n".format(time.strftime('%Y-%m-%d %H:%M:%S'), cmd))
            ret = await asyncio.create_subprocess_shell(cmd, stdout=f, stderr=f)
        # stdout, stderr  = await ret.communicate()
        # print(ret.returncode)
        return True
    except Exception as e:
        traceback.print_exc()
        return False

async def run_cmd_output_wait(cmd):
    try:
        ret = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr  = await ret.communicate()
        return stdout
    except Exception as e:
        traceback.print_exc()
        return False

async def docker_download_file(image_url, log_file):
    try:
        console_log("开始下载镜像", 3)
        res = await run_cmd_output("docker pull {}".format(image_url), log_file)
        if res:
            console_log("镜像下载完成", 3)
            return True
        else:
            console_log("镜像下载失败", 1)
    except Exception as e:
        console_log("镜像下载失败: " + str(e), 1)
    return False

async def docker_run(cmd, container_name, log_file):
    try:
        console_log("镜像启动...", 3)

        cmd_list = list(cmd)
        cmd_list.insert(11, "--name " + container_name)
        cmd = ''.join(cmd_list)

        await run_cmd_output("docker rm -f {}".format(container_name), log_file)
        await asyncio.sleep(1)
        await run_cmd_output(cmd, log_file)

        # 检查运行状态
        check_cnt = 0
        while check_cnt < 5:
            await asyncio.sleep(0.5)
            res = await __docker_check_running(container_name)
            if res:
                console_log("镜像启动成功", 2)
                return True
            else:
                check_cnt += 1

        console_log("镜像启动失败", 1)
        return False
    except Exception as e:
        console_log("镜像启动失败: " + str(e), 1)
        return False

async def docker_stop(container_name):
    try:
        console_log("镜像停止...", 3)
        res = await run_cmd_output_wait("docker rm -f {}".format(container_name))
        if res.decode().strip() == container_name:
            console_log("镜像停止成功", 2)
            return True
        console_log("镜像停止失败", 1)
    except Exception as e:
        console_log("镜像停止失败", 1)
        traceback.print_exc()
        return False

async def __docker_check_running(container_name):
    try:
        res = await run_cmd_output_wait("docker container inspect -f '{{{{.State.Running}}}}' {}".format(container_name))
        return res.decode().strip() == "true"
    except Exception as e:
        traceback.print_exc()
        return False


if __name__ == '__main__':
    asyncio.run(run_cmd_output("docker rm -f a1 && docker run --name a1 hello-world &"))