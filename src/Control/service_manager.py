import os
import sys
import subprocess
import ctypes
import time
from typing import Dict, Any
from env import get_project_root


class ServiceManager:
    def __init__(self):
        self.is_frozen = getattr(sys, 'frozen', False)
        self.service_exe_path = self._find_service_exe()
        self.service_process = None
        self.win_service_name = "PhantomCourier"
        self.project_root = get_project_root()

    def _find_service_exe(self) -> str:
        root = get_project_root()
        service_exe = os.path.join(root, 'bin', 'Service', 'Service.exe')
        if os.path.exists(service_exe):
            return service_exe
        raise FileNotFoundError(f"无法找到 Service.exe (Root: {root})")

    def is_standalone_running(self) -> bool:
        if self.is_win_service_running():
            return False
            
        if self.service_process is not None:
            if self.service_process.poll() is None:
                return True
            else:
                self.service_process = None
                
        try:
            output = subprocess.check_output(
                ['tasklist', '/FI', 'IMAGENAME eq Service.exe', '/NH'],
                creationflags=subprocess.CREATE_NO_WINDOW
            ).decode('gbk', 'ignore')
            return 'Service.exe' in output
        except Exception:
            pass
                
        return False

    def is_win_service_running(self) -> bool:
        try:
            result = subprocess.run(
                ["sc", "query", self.win_service_name],
                capture_output=True, text=True, check=False,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return "RUNNING" in result.stdout
        except Exception:
            return False

    def is_win_service_installed(self) -> bool:
        try:
            result = subprocess.run(
                ["sc", "query", self.win_service_name],
                capture_output=True, text=True, check=False,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return "1060" not in result.stderr and "1060" not in result.stdout and "FAILED" not in result.stdout
        except Exception:
            return False

    def start_standalone(self) -> bool:
        if self.is_win_service_running():
            return False
        if self.is_standalone_running():
            return False
        try:
            cmd = [self.service_exe_path]
            self.service_process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except Exception as e:
            print(f"Failed to start standalone: {e}")
            return False

    def stop_standalone(self) -> bool:
        """终止前台 Service 进程"""
        if self.service_process and self.service_process.poll() is None:
            try:
                self.service_process.terminate()
                try:
                    self.service_process.wait(timeout=5)
                    self.service_process = None
                    return True
                except subprocess.TimeoutExpired:
                    pass
                
                self.service_process.kill()
                try:
                    self.service_process.wait(timeout=3)
                    self.service_process = None
                    return True
                except subprocess.TimeoutExpired:
                    pass
            except Exception:
                pass
        
        if self.service_process and self.service_process.poll() is None:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(self.service_process.pid)],
                    capture_output=True,
                    check=False,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self.service_process = None
            except Exception:
                pass
        
        return True

    def _run_as_admin(self, executable: str, args_list: list) -> bool:
        try:
            args_str = " ".join(f'"{a}"' for a in args_list)
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, args_str, None, 0)
            return int(ret) > 32
        except Exception:
            return False

    def install_win_service(self) -> bool:
        if self.is_standalone_running():
            self.stop_standalone()
        return self._run_as_admin(self.service_exe_path, ['install'])

    def uninstall_win_service(self) -> bool:
        if self.is_standalone_running():
            self.stop_standalone()
        return self._run_as_admin(self.service_exe_path, ['uninstall'])

    def start_win_service(self) -> bool:
        if self.is_standalone_running():
            self.stop_standalone()
            for i in range(10):
                time.sleep(0.5)
                if not self.is_standalone_running():
                    break
            if self.is_standalone_running():
                return False
        return self._run_as_admin("net", ["start", self.win_service_name])

    def stop_win_service(self) -> bool:
        return self._run_as_admin("net", ["stop", self.win_service_name])

    def get_status_info(self) -> Dict[str, Any]:
        return {
            'standalone_running': self.is_standalone_running(),
            'win_service_installed': self.is_win_service_installed(),
            'win_service_running': self.is_win_service_running(),
            'exe_path': self.service_exe_path
        }
