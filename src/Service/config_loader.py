import json
import os
import sys
from typing import Dict, List, Any


class ConfigLoader:
    """
    配置文件加载器
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径，如果为 None 则自动查找
        """
        self.config_path = config_path
        self.config = {}
        
        if config_path is None:
            self.config_path = self._find_config_file()
        
        self.load_config()
    
    def _find_config_file(self) -> str:
        """
        查找配置文件
        
        Returns:
            配置文件路径
        """
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            if os.path.basename(exe_dir) == 'Service':
                project_root = os.path.dirname(os.path.dirname(exe_dir))
            else:
                project_root = os.path.dirname(exe_dir)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.join(os.path.dirname(current_dir), 'workspace_env')
        
        config_file = os.path.join(project_root, 'config', 'service_config.json')
        
        if not os.path.exists(config_file):
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self._get_default_config(), f, indent=4, ensure_ascii=False)
        
        return config_file
    
    def load_config(self):
        """
        加载配置文件
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            raise ValueError(f"加载配置文件失败: {e}")
        
        self._validate_config()
        self._set_default_values()
    
    def _validate_config(self):
        """
        验证配置参数
        """
        required_keys = ['scan', 'filter', 'upload']
        for key in required_keys:
            if key not in self.config:
                raise ValueError(f"配置文件缺少必需的键: {key}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            默认配置字典
        """
        return {
            'scan': {
                'root_paths': [],
                'interval': 600,
                'recursive': True,
                'always_scan_files': True
            },
            'filter': {
                'folder_mode': 'whitelist',
                'include_folders': [],
                'exclude_folders': [],
                'file_mode': 'whitelist',
                'include_patterns': [],
                'exclude_patterns': [],
                'exclude_hidden': True
            },
            'stability': {
                'file_check_count': 3,
                'file_check_interval': 1,
                'file_check_round': 2
            },
            'upload': {
                'enabled': True,
                'retry_count': 2,
                'preserve_structure': True,
                'upload_on_first_run': False,
                'sftp': {
                    'host': '',
                    'port': 22,
                    'username': '',
                    'password': '',
                    'target_path': ''
                },
                'smb': {
                    'server_ip': '',
                    'server_port': 139,
                    'username': '',
                    'password': '',
                    'share_name': '',
                    'target_path': ''
                },
                'destinations': []
            },
            'gating': {
                'enabled': False,
                'exe_path': 'Gating.exe',
                'file_extension': '.fcs'
            },
            'storage': {
                'upload_record_file': 'uploaded.json',
                'failed_record_file': 'failed.json',
                'dir_record_file': 'dirs.json',
                'gating_record_file': 'gating_records.json'
            },
            'logging': {
                'level': 'INFO',
                'log_file': 'service.log'
            }
        }
    
    def _set_default_values(self):
        """
        设置默认值
        """
        defaults = self._get_default_config()
        
        for section, section_defaults in defaults.items():
            if section not in self.config:
                self.config[section] = {}
            for key, value in section_defaults.items():
                if key not in self.config[section]:
                    self.config[section][key] = value
        
        self._fill_destinations_with_defaults()
    
    def _fill_destinations_with_defaults(self):
        """
        使用默认配置填充 destinations 数组
        """
        upload_config = self.config.get('upload', {})
        sftp_defaults = upload_config.get('sftp', {})
        smb_defaults = upload_config.get('smb', {})
        destinations = upload_config.get('destinations', [])
        
        for dest in destinations:
            protocol = dest.get('protocol', '')
            
            if protocol == 'sftp':
                for key, value in sftp_defaults.items():
                    if key not in dest or not dest[key]:
                        dest[key] = value
            elif protocol == 'smb':
                for key, value in smb_defaults.items():
                    if key not in dest or not dest[key]:
                        dest[key] = value
        
        upload_config['destinations'] = destinations
        self.config['upload'] = upload_config
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键（支持点号分隔，如 'scan.interval'）
            default: 默认值
        
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_scan_config(self) -> Dict[str, Any]:
        """
        获取扫描配置
        
        Returns:
            扫描配置字典
        """
        return self.config.get('scan', {})
    
    def get_filter_config(self) -> Dict[str, Any]:
        """
        获取过滤配置
        
        Returns:
            过滤配置字典
        """
        return self.config.get('filter', {})
    
    def get_stability_config(self) -> Dict[str, Any]:
        """
        获取稳定性配置
        
        Returns:
            稳定性配置字典
        """
        return self.config.get('stability', {})
    
    def get_upload_config(self) -> Dict[str, Any]:
        """
        获取上传配置
        
        Returns:
            上传配置字典
        """
        return self.config.get('upload', {})
    
    def get_gating_config(self) -> Dict[str, Any]:
        """
        获取 Gating 配置
        
        Returns:
            Gating 配置字典
        """
        return self.config.get('gating', {})
    
    def get_storage_config(self) -> Dict[str, Any]:
        """
        获取存储配置
        
        Returns:
            存储配置字典
        """
        return self.config.get('storage', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        获取日志配置
        
        Returns:
            日志配置字典
        """
        return self.config.get('logging', {})
    
    def get_project_root(self) -> str:
        """
        获取项目根目录
        
        Returns:
            项目根目录路径
        """
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            if os.path.basename(exe_dir) == 'Service':
                return os.path.dirname(os.path.dirname(exe_dir))
            return os.path.dirname(exe_dir)
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(os.path.dirname(current_dir), 'workspace_env')
    
    def get_data_dir(self) -> str:
        """
        获取数据目录
        
        Returns:
            数据目录路径
        """
        return os.path.join(self.get_project_root(), 'data')
    
    def get_logs_dir(self) -> str:
        """
        获取日志目录
        
        Returns:
            日志目录路径
        """
        return os.path.join(self.get_project_root(), 'logs')
    
    def get_config_dir(self) -> str:
        """
        获取配置目录
        
        Returns:
            配置目录路径
        """
        return os.path.join(self.get_project_root(), 'config')
    
    def get_bin_dir(self) -> str:
        """
        获取可执行文件目录
        
        Returns:
            可执行文件目录路径
        """
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(os.path.abspath(sys.executable))
            if os.path.basename(exe_dir) == 'Service':
                return os.path.dirname(exe_dir)
            return exe_dir
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(current_dir, '..', 'Gating')
    
    def save_config(self):
        """
        保存配置文件
        """
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise ValueError(f"保存配置文件失败: {e}")