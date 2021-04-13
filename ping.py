import shlex
import subprocess

def get_simple_cmd_output(cmd, stderr=subprocess.STDOUT):
    """
    Execute a simple external command and get its output.
    """
    args = shlex.split(cmd)
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=stderr).communicate()[0]

def get_ping_time(host):
    host = host.split(':')[0]
    cmd = "ping {host} -C 3 -q".format(host=host)
    res = [float(x) for x in get_simple_cmd_output(cmd).strip().split(':')[-1].split() if x != '-']
    if len(res) > 0:
        return sum(res) / len(res)
    else:
        return 999999

def ping(server='example.com', count=1, wait_sec=1):
    """

    :rtype: dict or None
    """
    cmd = "ping -c {} -W {} {}".format(count, wait_sec, server).split(' ')
    try:
        output = subprocess.check_output(cmd).decode().strip()
        lines = output.split("\n")
        total = lines[-2].split(',')[3].split()[1]
        loss = lines[-2].split(',')[2].split()[0]
        timing = lines[-1].split()[3].split('/')
        res = {
            'type': 'rtt',
            'min': timing[0],
            'avg': timing[1],
            'max': timing[2],
            'mdev': timing[3],
            'total': total,
            'loss': loss,
        }
        return res['avg']
    except Exception as e:
        # print(e)
        return '0'

if __name__ == '__main__':
    print(ping("localhost"))
    print(ping("baidu.com"))
    print(ping("google.com"))