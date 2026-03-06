import os
import subprocess
import sys
import json
import time
from typing import Dict, List


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
    
    def is_gating_folder(self, folder_path: str, files_info: Dict[str, Dict]) -> bool:
        """
        判断是否是 Gating 文件夹
        
        Args:
            folder_path: 文件夹路径
            files_info: 文件夹内的文件信息
        
        Returns:
            True: 是 Gating 文件夹
            False: 不是 Gating 文件夹
        """
        if not files_info:
            return False
        
        for file_path in files_info.keys():
            file_name = os.path.basename(file_path)
            if not file_name.lower().endswith(self.file_extension):
                return False
        
        return True
    
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
            if exe_full_path.endswith('.py'):
                subprocess.Popen(
                    [sys.executable, exe_full_path, folder_path],
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
                )
            else:
                subprocess.Popen(
                    [exe_full_path, folder_path],
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
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
                
                os.remove(lock_file)
                return
            except FileExistsError:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    return
            except Exception as e:
                if os.path.exists(lock_file):
                    try:
                        os.remove(lock_file)
                    except:
                        pass
                return