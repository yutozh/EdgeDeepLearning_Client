import time

def console_init(info):
    print("="*60)
    for k, v in info.items():
        print("{:<15}{:<30}".format(k, v))
    print("="*60)

def console_log(log, type=0):
    if type == 0:
        print("[{}] {}".format(time.strftime('%Y-%m-%d %H:%M:%S'), log))
    elif type == 1:
        print("\033[1;31m[{}] {}\033[0m".format(time.strftime('%Y-%m-%d %H:%M:%S'), log))
    elif type == 2:
        print("\033[1;32m[{}] {}\033[0m".format(time.strftime('%Y-%m-%d %H:%M:%S'), log))
    elif type == 3:
        print("\033[1;36m[{}] {}\033[0m".format(time.strftime('%Y-%m-%d %H:%M:%S'), log))
