import sys
import os
from service_instance import ServiceInstance


def main():
    """
    主入口函数
    """
    config_path = None
    
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    service = ServiceInstance(config_path)
    service.start()
    
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        service.stop()
        print("服务已停止")


if __name__ == '__main__':
    main()