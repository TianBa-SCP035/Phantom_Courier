import sys
import os
import ctypes
import subprocess
import time
import servicemanager
import win32event
import win32service
import win32serviceutil
from service_instance import ServiceInstance


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


class ServiceWrapper(win32serviceutil.ServiceFramework):
    _svc_name_ = "PhantomCourier"
    _svc_display_name_ = "Phantom Courier"
    _svc_description_ = "文件扫描上传服务"

    def __init__(self, args):
        super().__init__(args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.service_instance = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        if self.service_instance:
            self.service_instance.stop()

    def SvcShutdown(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        if self.service_instance:
            self.service_instance.stop()

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, ""),
        )

        self.service_instance = ServiceInstance()
        self.service_instance.start()
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)


def get_service_status():
    try:
        hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_CONNECT)
        hs = win32service.OpenService(hscm, ServiceWrapper._svc_name_, win32service.SERVICE_QUERY_STATUS)
        status = win32service.QueryServiceStatus(hs)
        win32service.CloseServiceHandle(hs)
        win32service.CloseServiceHandle(hscm)

        is_installed = True
        is_running = status[1] == win32service.SERVICE_RUNNING
        status_map = {
            win32service.SERVICE_STOPPED: "已停止",
            win32service.SERVICE_START_PENDING: "正在启动",
            win32service.SERVICE_STOP_PENDING: "正在停止",
            win32service.SERVICE_RUNNING: "正在运行",
            win32service.SERVICE_CONTINUE_PENDING: "正在继续",
            win32service.SERVICE_PAUSE_PENDING: "正在暂停",
            win32service.SERVICE_PAUSED: "已暂停",
        }
        status_text = status_map.get(status[1], f"未知状态({status[1]})")
    except Exception as e:
        is_installed = False
        is_running = False
        status_text = f"未安装 ({e})"

    return is_installed, is_running, status_text


def install_service():
    try:
        is_installed, _, _ = get_service_status()
        if is_installed:
            print("服务已存在，正在卸载旧版本...")
            uninstall_service()
            time.sleep(1)

        python_class = f"{ServiceWrapper.__module__}.{ServiceWrapper.__name__}"
        win32serviceutil.InstallService(
            python_class,
            ServiceWrapper._svc_name_,
            ServiceWrapper._svc_display_name_,
            startType=win32service.SERVICE_AUTO_START,
            description=ServiceWrapper._svc_description_,
        )

        subprocess.run(
            ["sc", "config", ServiceWrapper._svc_name_, "start=", "delayed-auto"],
            capture_output=True,
            text=True,
            check=False,
        )

        subprocess.run(
            [
                "sc",
                "failure",
                ServiceWrapper._svc_name_,
                "reset=",
                "86400",
                "actions=",
                "restart/30000/restart/30000/restart/30000",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        print(f"✓ 服务已安装: {ServiceWrapper._svc_display_name_}")
        print(f"  服务名称: {ServiceWrapper._svc_name_}")
        print("  启动类型: 自动（延迟启动）")
        print("  失败重试: 3次，间隔30秒")
        print("\n提示: 使用 'Service.exe start' 启动服务")
        return True
    except Exception as e:
        print(f"✗ 安装失败: {e}")
        return False


def uninstall_service():
    try:
        win32serviceutil.RemoveService(ServiceWrapper._svc_name_)
        print(f"✓ 服务已卸载: {ServiceWrapper._svc_display_name_}")
        return True
    except Exception as e:
        print(f"✗ 卸载失败: {e}")
        return False


def start_service():
    try:
        result = subprocess.run(["net", "start", ServiceWrapper._svc_name_], capture_output=True, text=True)
        if result.returncode != 0:
            err = result.stderr.strip() or result.stdout.strip() or "未知错误"
            print(f"✗ 启动失败: {err}")
            return False

        print(f"✓ 服务启动命令已发送: {ServiceWrapper._svc_display_name_}")
        print("正在等待服务启动...")
        for i in range(10):
            time.sleep(1)
            _, is_running, _ = get_service_status()
            if is_running:
                print("✓ 服务已成功启动")
                return True
            print(f"  等待中... ({i + 1}/10)")

        print("✗ 服务启动超时")
        return False
    except Exception as e:
        print(f"✗ 启动失败: {e}")
        return False


def stop_service():
    try:
        result = subprocess.run(["net", "stop", ServiceWrapper._svc_name_], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ 服务已停止: {ServiceWrapper._svc_display_name_}")
            return True
        err = result.stderr.strip() or result.stdout.strip() or "未知错误"
        print(f"✗ 停止失败: {err}")
        return False
    except Exception as e:
        print(f"✗ 停止失败: {e}")
        return False


def show_status():
    is_installed, is_running, status_text = get_service_status()
    admin_status = "管理员" if is_admin() else "普通用户"

    print("=" * 60)
    print(f"  {ServiceWrapper._svc_display_name_}")
    print("  服务状态")
    print("=" * 60)
    print(f"  运行权限: {admin_status}")
    print(f"  服务名称: {ServiceWrapper._svc_name_}")
    print(f"  安装状态: {'已安装' if is_installed else '未安装'}")
    print(f"  运行状态: {status_text}")
    print("=" * 60)
    print()

    return is_installed, is_running


def show_help():
    print("=" * 60)
    print(f"  {ServiceWrapper._svc_display_name_}")
    print("=" * 60)
    print()
    print("用法:")
    print("  Service.exe status")
    print("  Service.exe install")
    print("  Service.exe uninstall")
    print("  Service.exe start")
    print("  Service.exe stop")
    print("  Service.exe restart")
    print()


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
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "install":
            install_service()
        elif command == "uninstall":
            uninstall_service()
        elif command == "start":
            start_service()
        elif command == "stop":
            stop_service()
        elif command == "status":
            show_status()
        else:
            show_help()
    else:
        try:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(ServiceWrapper)
            servicemanager.StartServiceCtrlDispatcher()
        except Exception:
            main()