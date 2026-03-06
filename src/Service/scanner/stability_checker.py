import os
import time
from typing import Dict, Tuple, List


class StabilityChecker:
    """
    稳定性检查器
    """
    
    def __init__(self, file_check_count: int = 3, file_check_interval: int = 1):
        """
        初始化稳定性检查器
        
        Args:
            file_check_count: 文件稳定性检查次数
            file_check_interval: 文件稳定性检查间隔（秒）
        """
        self.file_check_count = file_check_count
        self.file_check_interval = file_check_interval
    
    def check_files_stability(self, file_paths: List[str]) -> Dict[str, bool]:
        """
        检查文件列表的稳定性（按照间隔取三次信息，一次性比对出稳定和不稳定的结果）
        
        Args:
            file_paths: 文件路径列表
        
        Returns:
            文件路径到是否稳定的映射
        """
        if not file_paths:
            return {}
        
        results = {file_path: False for file_path in file_paths}
        file_infos = {file_path: [] for file_path in file_paths}
        
        for i in range(self.file_check_count):
            for file_path in file_paths:
                if os.path.exists(file_path):
                    file_stat = os.stat(file_path)
                    file_infos[file_path].append({
                        'size': file_stat.st_size,
                        'mod_time': file_stat.st_mtime
                    })
                else:
                    file_infos[file_path] = []
                    results[file_path] = False
            
            if i < self.file_check_count - 1:
                time.sleep(self.file_check_interval)
        
        for file_path in file_paths:
            infos = file_infos[file_path]
            if len(infos) == self.file_check_count:
                first_info = infos[0]
                all_same = True
                for info in infos[1:]:
                    if (info['size'] != first_info['size'] or 
                        info['mod_time'] != first_info['mod_time']):
                        all_same = False
                        break
                results[file_path] = all_same
            else:
                results[file_path] = False
        
        return results
    
    def check_folder_stability(self, folder_path: str) -> bool:
        """
        检查文件夹的稳定性（按照间隔取三次信息，一次性比对出稳定和不稳定的结果）
        
        Args:
            folder_path: 文件夹路径
        
        Returns:
            True: 文件夹稳定
            False: 文件夹不稳定
        """
        snapshots = []
        
        for i in range(self.file_check_count):
            current_files = {}
            try:
                for file_name in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, file_name)
                    if os.path.isfile(file_path):
                        file_stat = os.stat(file_path)
                        current_files[file_path] = {
                            'size': file_stat.st_size,
                            'mod_time': file_stat.st_mtime
                        }
            except Exception as e:
                return False
            
            snapshots.append(current_files)
            
            if i < self.file_check_count - 1:
                time.sleep(self.file_check_interval)
        
        for i in range(1, len(snapshots)):
            if len(snapshots[i]) != len(snapshots[0]):
                return False
            
            for file_path, file_info in snapshots[i].items():
                if file_path not in snapshots[0]:
                    return False
                
                if file_info['size'] != snapshots[0][file_path]['size']:
                    return False
        
        return True