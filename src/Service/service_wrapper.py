import sys
import time
import servicemanager
import win32service
import win32serviceutil
import win32event
from service_instance import ServiceInstance


class ServiceWrapper(win32serviceutil.ServiceFramework):
    """
    Windows 服务包装器
    """
    
    _svc_name_ = "PhantomCourierService"
    _svc_display_name_ = "Phantom Courier Service"
    _svc_description_ = "文件扫描上传服务"
    
    def __init__(self, args):
        """
        初始化服务
        
        Args:
            args: 服务参数
        """
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.service_instance = None
    
    def SvcStop(self):
        """
        停止服务
        """
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        
        if self.service_instance:
            self.service_instance.stop()
        
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, '')
        )
    
    def SvcDoRun(self):
        """
        运行服务
        """
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        self.service_instance = ServiceInstance()
        self.service_instance.start()
        
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)


def install_service():
    """
    安装服务
    """
    win32serviceutil.InstallService(
        ServiceWrapper._svc_name_,
        ServiceWrapper._svc_display_name_,
        ServiceWrapper._svc_description_,
        startType=win32service.SERVICE_AUTO_START
    )
    print(f"服务已安装: {ServiceWrapper._svc_display_name_}")


def uninstall_service():
    """
    卸载服务
    """
    win32serviceutil.RemoveService(ServiceWrapper._svc_name_)
    print(f"服务已卸载: {ServiceWrapper._svc_display_name_}")


def start_service():
    """
    启动服务
    """
    win32serviceutil.StartService(ServiceWrapper._svc_name_)
    print(f"服务已启动: {ServiceWrapper._svc_display_name_}")


def stop_service():
    """
    停止服务
    """
    win32serviceutil.StopService(ServiceWrapper._svc_name_)
    print(f"服务已停止: {ServiceWrapper._svc_display_name_}")


def restart_service():
    """
    重启服务
    """
    stop_service()
    time.sleep(2)
    start_service()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'install':
            install_service()
        elif command == 'uninstall':
            uninstall_service()
        elif command == 'start':
            start_service()
        elif command == 'stop':
            stop_service()
        elif command == 'restart':
            restart_service()
        else:
            win32serviceutil.HandleCommandLine(ServiceWrapper)
    else:
        print("用法:")
        print("  Service.py install    - 安装服务")
        print("  Service.py uninstall  - 卸载服务")
        print("  Service.py start      - 启动服务")
        print("  Service.py stop       - 停止服务")
        print("  Service.py restart    - 重启服务")