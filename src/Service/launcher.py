# -*- coding: utf-8 -*-
import ctypes
import os
import subprocess
import sys
import time

import servicemanager
import win32event
import win32service
import win32serviceutil

from service_instance import ServiceInstance


# 检查当前进程是否具有管理员权限。
def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


# Windows 服务包装器，托管 ServiceInstance。
class ServiceWrapper(win32serviceutil.ServiceFramework):
    _svc_name_ = "PhantomCourier"
    _svc_display_name_ = "Phantom Courier"
    _svc_description_ = "文件扫描上传服务"

    def __init__(self, args):
        super().__init__(args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.service_instance = None

    # 处理服务停止请求。
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        if self.service_instance:
            self.service_instance.stop()

    # 处理系统关机请求。
    def SvcShutdown(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        if self.service_instance:
            self.service_instance.stop()

    # 启动业务服务并阻塞等待停止事件。
    def SvcDoRun(self):
        exe_dir = os.path.dirname(sys.executable) if hasattr(sys, "frozen") else os.path.dirname(os.path.abspath(__file__))
        os.chdir(exe_dir)

        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, f"工作目录: {exe_dir}"),
        )

        self.service_instance = ServiceInstance()
        self.service_instance.start()
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)


# 查询服务安装和运行状态。
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


# 安装或重装服务并配置启动/失败策略。
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

        # 设置延迟自动启动。
        subprocess.run(
            ["sc", "config", ServiceWrapper._svc_name_, "start=", "delayed-auto"],
            capture_output=True,
            text=True,
            check=False,
        )

        # 设置失败重启策略：30秒间隔重启3次。
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


# 从系统中卸载服务。
def uninstall_service():
    try:
        win32serviceutil.RemoveService(ServiceWrapper._svc_name_)
        print(f"✓ 服务已卸载: {ServiceWrapper._svc_display_name_}")
        return True
    except Exception as e:
        print(f"✗ 卸载失败: {e}")
        return False


# 启动服务并轮询10秒等待运行状态。
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


# 停止服务。
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


# 交互模式中的重启封装。
def restart_service():
    print("正在重启服务...")
    stop_service()
    time.sleep(2)
    start_service()


# 前台控制台模式，方便测试调试。
def run_as_console():
    print("=" * 60)
    print(f"  {ServiceWrapper._svc_display_name_}")
    print("  控制台模式")
    print("=" * 60)
    print()

    service = ServiceInstance()
    service.start()

    print("服务已启动，按 Ctrl+C 停止服务...")
    print()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        service.stop()
        print("服务已停止")


# 显示服务状态摘要。
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


# 双击运行时进入交互菜单。
def interactive_mode():
    is_installed, is_running = show_status()

    if is_installed:
        if is_running:
            print("服务正在运行中...")
            print("\n请选择操作:")
            print("  1. 停止服务")
            print("  2. 重启服务")
            print("  3. 以控制台模式运行")
            print("  4. 卸载服务")
            print("  5. 退出")
        else:
            print("服务已安装但未运行...")
            print("\n请选择操作:")
            print("  1. 启动服务")
            print("  2. 以控制台模式运行")
            print("  3. 卸载服务")
            print("  4. 退出")
    else:
        print("服务未安装...")
        print("\n请选择操作:")
        print("  1. 安装服务")
        print("  2. 以控制台模式运行")
        print("  3. 退出")

    print()

    try:
        choice = input("请输入选项 (1-5): ").strip()

        if is_installed:
            if is_running:
                if choice == "1":
                    stop_service()
                elif choice == "2":
                    restart_service()
                elif choice == "3":
                    run_as_console()
                elif choice == "4":
                    stop_service()
                    time.sleep(1)
                    uninstall_service()
                elif choice == "5":
                    pass
                else:
                    print("无效选项")
            else:
                if choice == "1":
                    start_service()
                elif choice == "2":
                    run_as_console()
                elif choice == "3":
                    uninstall_service()
                elif choice == "4":
                    pass
                else:
                    print("无效选项")
        else:
            if choice == "1":
                if install_service():
                    print("\n是否立即启动服务? (y/n): ", end="")
                    if input().strip().lower() == "y":
                        start_service()
            elif choice == "2":
                run_as_console()
            elif choice == "3":
                pass
            else:
                print("无效选项")

        print("\n按任意键退出...")
        input()

    except KeyboardInterrupt:
        print("\n\n已取消")


# 显示命令行帮助信息。
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
    print("  Service.exe console")
    print()


# 入口：有参数走命令模式，无参数优先尝试服务模式。
if __name__ == "__main__":
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
        elif command == "restart":
            restart_service()
        elif command == "status":
            show_status()
        elif command == "console":
            run_as_console()
        else:
            show_help()
    else:
        try:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(ServiceWrapper)
            servicemanager.StartServiceCtrlDispatcher()
        except Exception:
            interactive_mode()
