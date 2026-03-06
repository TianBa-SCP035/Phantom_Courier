import os
from typing import Dict, List, Tuple
from .file_filter import FileFilter
from .stability_checker import StabilityChecker


class FileScanner:
    """
    文件扫描器
    """
    
    def __init__(self, root_paths: List[str], filter_config: dict, stability_config: dict, dir_scan_records: Dict[str, Dict] = None, always_scan_files: bool = False):
        """
        初始化文件扫描器
        
        Args:
            root_paths: 扫描根目录列表
            filter_config: 过滤配置
            stability_config: 稳定性配置
            dir_scan_records: 目录扫描记录（可选）
            always_scan_files: 是否总是进行文件扫描
        """
        self.root_paths = root_paths
        self.file_filter = FileFilter(filter_config)
        self.stability_checker = StabilityChecker(
            file_check_count=stability_config.get('file_check_count', 3),
            file_check_interval=stability_config.get('file_check_interval', 1)
        )
        self.always_scan_files = always_scan_files
        
        self.scanned_files: set = set()
        self.dir_scan_records: Dict[str, Dict] = dir_scan_records if dir_scan_records is not None else {}
    
    def scan(self, recursive: bool = True) -> List[str]:
        """
        扫描目录
        
        Args:
            recursive: 是否递归扫描
        
        Returns:
            符合条件的文件夹路径列表
        """
        self.scanned_files.clear()
        results = []
        
        for root_path in self.root_paths:
            if recursive:
                for dirpath, dirnames, filenames in os.walk(root_path):
                    if self._should_scan_dir(dirpath):
                        results.append(dirpath)
            else:
                if self._should_scan_dir(root_path):
                    results.append(root_path)
        
        return results
    
    def _should_scan_dir(self, dir_path: str) -> bool:
        """
        判断是否应该扫描目录
        
        Args:
            dir_path: 目录路径
        
        Returns:
            True: 应该扫描
            False: 不应该扫描
        """
        if not self.file_filter.should_include_folder(dir_path):
            return False
        
        if self.always_scan_files:
            return True
        
        dir_mod_time = os.path.getmtime(dir_path)
        record = self.dir_scan_records.get(dir_path)
        
        if record is None:
            return True
        
        if record.get('last_dir_mod_time') != dir_mod_time:
            return True
        
        return False
    
    def _scan_directory(self, dir_path: str, filenames: List[str]) -> Dict[str, Dict]:
        """
        扫描目录
        
        Args:
            dir_path: 目录路径
            filenames: 文件名列表
        
        Returns:
            文件路径到文件信息的映射
        """
        files_info = {}
        
        for filename in filenames:
            file_path = os.path.join(dir_path, filename)
            
            if os.path.isfile(file_path) and self.file_filter.should_include_file(file_path):
                try:
                    file_stat = os.stat(file_path)
                    files_info[file_path] = {
                        'path': file_path,
                        'size': file_stat.st_size,
                        'mod_time': file_stat.st_mtime
                    }
                    self.scanned_files.add(file_path)
                except Exception as e:
                    pass
        
        return files_info
    
    def update_dir_scan_record(self, dir_path: str):
        """
        更新目录扫描记录
        
        Args:
            dir_path: 目录路径
        """
        dir_mod_time = os.path.getmtime(dir_path)
        self.dir_scan_records[dir_path] = {
            'last_dir_mod_time': dir_mod_time
        }
    
    def get_stability_checker(self) -> StabilityChecker:
        """
        获取稳定性检查器
        
        Returns:
            稳定性检查器
        """
        return self.stability_checker