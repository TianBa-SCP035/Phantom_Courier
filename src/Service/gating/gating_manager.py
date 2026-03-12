import os
import subprocess
import sys
import json
import time
import threading
from typing import Dict, List, Optional


class GatingManager:
    """
    Gating 管理器
    """
    
    def __init__(self, gating_config: dict, data_dir: str, bin_dir: str, record_file_name: str = 'gating_records.json'):
        """
        初始化 Gating 管理器
        
        Args:
            gating_config: Gating 配置
            data_dir: 数据目录
            bin_dir: 可执行文件目录
            record_file_name: 记录文件名
        """
        self.enabled = gating_config.get('enabled', True)
        self.exe_path = gating_config.get('exe_path', 'Gating.exe')
        self.file_extension = gating_config.get('file_extension', '.fcs')
        
        self.data_dir = data_dir
        self.bin_dir = bin_dir
        self.record_file = os.path.join(data_dir, record_file_name)
    
    def submit_task_async(self, dir_path: str):
        """
        异步提交任务
        
        Args:
            dir_path: 目录路径
        """
        if not self.enabled:
            return
        
        thread = threading.Thread(
            target=self._process_gating_task,
            args=(dir_path,),
            daemon=True
        )
        thread.start()
    
    def _process_gating_task(self, dir_path: str):
        """
        处理 Gating 任务（在线程中执行）
        
        Args:
            dir_path: 目录路径
        """
        try:
            folder_snapshot = self._get_folder_snapshot(dir_path)
            
            if not folder_snapshot:
                return
            
            time.sleep(60)
            
            if not self._check_stability(dir_path, folder_snapshot['dir_mtime'], folder_snapshot['files']):
                return
            
            time.sleep(120)
            
            if not self._check_stability(dir_path, folder_snapshot['dir_mtime'], folder_snapshot['files']):
                return
            
            self.call_gating(dir_path)
        except Exception as e:
            pass
    
    def _get_folder_snapshot(self, dir_path: str) -> Optional[Dict]:
        """
        获取文件夹快照（包含目录修改时间和文件信息）
        同时检查是否是 Gating 文件夹
        
        Args:
            dir_path: 目录路径
        
        Returns:
            {
                'dir_mtime': 目录修改时间,
                'files': {file_path: {'size': ..., 'mod_time': ...}}
            }
            如果不是 Gating 文件夹或出错，返回 None
        """
        try:
            dir_mtime = os.stat(dir_path).st_mtime
            files = {}
            
            for file_name in os.listdir(dir_path):
                if not file_name.lower().endswith(self.file_extension):
                    return None
                
                file_path = os.path.join(dir_path, file_name)
                if os.path.isfile(file_path):
                    file_stat = os.stat(file_path)
                    files[file_path] = {
                        'size': file_stat.st_size,
                        'mod_time': file_stat.st_mtime
                    }
            
            return {
                'dir_mtime': dir_mtime,
                'files': files
            }
        except Exception as e:
            return None
    
    def _check_stability(self, dir_path: str, first_mtime: float, file_snapshot: Dict) -> bool:
        """
        检查任务目录是否仍然稳定
        
        Args:
            dir_path: 目录路径
            first_mtime: 第一次检查时的目录修改时间
            file_snapshot: 第一次检查时的文件快照
        
        Returns:
            True: 稳定
            False: 不稳定
        """
        try:
            current_mtime = os.stat(dir_path).st_mtime
            
            if current_mtime != first_mtime:
                return False
            
            current_snapshot = self._get_folder_snapshot(dir_path)
            
            if not current_snapshot:
                return False
            
            current_files = current_snapshot['files']
            
            if len(current_files) != len(file_snapshot):
                return False
            
            for file_path, file_info in current_files.items():
                if file_path not in file_snapshot:
                    return False
                
                if file_info['size'] != file_snapshot[file_path]['size']:
                    return False
            
            return True
        except Exception as e:
            return False
    
    def call_gating(self, folder_path: str) -> bool:
        """
        调用 Gating
        
        Args:
            folder_path: 文件夹路径
        
        Returns:
            True: 调用成功
            False: 调用失败
        """
        if not self.enabled:
            return False
        
        exe_full_path = os.path.abspath(os.path.join(self.bin_dir, self.exe_path))
        
        if not os.path.exists(exe_full_path):
            main_py_path = os.path.abspath(os.path.join(self.bin_dir, 'main.py'))
            if os.path.exists(main_py_path):
                exe_full_path = main_py_path
            else:
                return False
        
        try:
            sample_files_json = json.dumps([folder_path])
            
            if sys.platform == 'win32':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            if exe_full_path.endswith('.py'):
                subprocess.Popen(
                    [sys.executable, exe_full_path, '--sample_files', sample_files_json],
                    startupinfo=startupinfo if sys.platform == 'win32' else None,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL
                )
            else:
                subprocess.Popen(
                    [exe_full_path, '--sample_files', sample_files_json],
                    startupinfo=startupinfo if sys.platform == 'win32' else None,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL
                )
            
            self.save_result(folder_path, {
                'call_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'called'
            })
            
            return True
        except Exception as e:
            return False
    
    def save_result(self, folder_path: str, result: Dict):
        """
        保存 Gating 调用结果
        
        Args:
            folder_path: 文件夹路径
            result: 结果信息
        """
        lock_file = self.record_file + '.lock'
        max_retries = 5
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                with open(lock_file, 'x') as f:
                    pass
                
                try:
                    records = {}
                    if os.path.exists(self.record_file):
                        with open(self.record_file, 'r', encoding='utf-8') as f:
                            records = json.load(f)
                    
                    if folder_path in records:
                        records[folder_path].update(result)
                    else:
                        records[folder_path] = result
                    
                    temp_file = self.record_file + '.tmp'
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        json.dump(records, f, indent=4, ensure_ascii=False)
                    os.replace(temp_file, self.record_file)
                    
                    return
                finally:
                    if os.path.exists(lock_file):
                        try:
                            os.remove(lock_file)
                        except:
                            pass
                            
            except FileExistsError:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    return
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    return
