import os
import re
from typing import List, Set


class FileFilter:
    """
    文件过滤器
    """
    
    def __init__(self, filter_config: dict):
        """
        初始化文件过滤器
        
        Args:
            filter_config: 过滤配置
        """
        self.folder_mode = filter_config.get('folder_mode', 'whitelist')
        self.file_mode = filter_config.get('file_mode', 'whitelist')
        self.include_folders = filter_config.get('include_folders', [])
        self.exclude_folders = filter_config.get('exclude_folders', [])
        self.include_patterns = filter_config.get('include_patterns', [])
        self.exclude_patterns = filter_config.get('exclude_patterns', [])
        self.exclude_hidden = filter_config.get('exclude_hidden', True)
    
    def should_include_folder(self, folder_path: str) -> bool:
        """
        判断是否应该包含文件夹
        
        Args:
            folder_path: 文件夹路径
        
        Returns:
            True: 应该包含
            False: 不应该包含
        """
        folder_name = os.path.basename(folder_path)
        
        if self.folder_mode == 'whitelist':
            if self.include_folders:
                for pattern in self.include_folders:
                    if re.match(pattern, folder_name):
                        return True
                return False
            return True
        else:
            for pattern in self.exclude_folders:
                if re.match(pattern, folder_name):
                    return False
            return True
    
    def should_include_file(self, file_path: str) -> bool:
        """
        判断是否应该包含文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            True: 应该包含
            False: 不应该包含
        """
        file_name = os.path.basename(file_path)
        
        if self.exclude_hidden and file_name.startswith('.'):
            return False
        
        if self.file_mode == 'whitelist':
            if self.include_patterns:
                for pattern in self.include_patterns:
                    if re.match(pattern, file_name):
                        return True
                return False
            
            return True
        else:
            for pattern in self.exclude_patterns:
                if re.match(pattern, file_name):
                    return False
            
            return True
    
    def filter_files(self, file_paths: List[str]) -> List[str]:
        """
        过滤文件列表
        
        Args:
            file_paths: 文件路径列表
        
        Returns:
            过滤后的文件路径列表
        """
        return [f for f in file_paths if self.should_include_file(f)]