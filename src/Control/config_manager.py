import json
import os
from typing import Dict, Any
from env import get_project_root
from crypto_utils import ConfigEncryptor


class ConfigManager:
    def __init__(self):
        self.config_dir = self._find_config_dir()
        self.dat_config_path = os.path.join(self.config_dir, 'service_config.dat')
        self.json_config_path = os.path.join(self.config_dir, 'service_config.json')
        self.config = {}
        self.encryptor = ConfigEncryptor()
        self.load_config()

    def _find_config_dir(self) -> str:
        project_root = get_project_root()
        return os.path.join(project_root, 'config')

    def load_config(self) -> bool:
        try:
            if os.path.exists(self.dat_config_path):
                self.config = self.encryptor.decrypt_config_from_file(self.dat_config_path)
                return True
            elif os.path.exists(self.json_config_path):
                with open(self.json_config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                return True
            else:
                self.config = self._get_default_config()
                os.makedirs(self.config_dir, exist_ok=True)
                with open(self.json_config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
                return True
        except Exception:
            self.config = self._get_default_config()
            return False

    def save_config(self) -> bool:
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            self.encryptor.encrypt_config_to_file(self.config, self.dat_config_path)
            return True
        except Exception:
            return False

    def get_config(self) -> Dict[str, Any]:
        return self.config

    def update_config(self, config: Dict[str, Any]) -> bool:
        try:
            self.config = config
            return self.save_config()
        except Exception:
            return False

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            "scan": {
                "root_paths": [],
                "interval": 600,
                "recursive": True,
                "always_scan_files": True
            },
            "filter": {
                "folder_mode": "whitelist",
                "include_folders": [],
                "exclude_folders": [],
                "file_mode": "whitelist",
                "include_patterns": [],
                "exclude_patterns": [],
                "exclude_hidden": True
            },
            "stability": {
                "file_check_count": 3,
                "file_check_interval": 1,
                "file_check_round": 2
            },
            "upload": {
                "enabled": True,
                "retry_count": 2,
                "file_upload_interval": 0,
                "preserve_structure": True,
                "upload_on_first_run": False,
                "sftp": {
                    "host": "", "port": 22,
                    "username": "", "password": "", "target_path": ""
                },
                "smb": {
                    "server_ip": "", "server_port": 139,
                    "username": "", "password": "",
                    "share_name": "", "target_path": ""
                },
                "destinations": []
            },
            "gating": {
                "enabled": False,
                "exe_path": "Gating.exe",
                "file_extension": ".fcs"
            },
            "database": {
                "enabled": False,
                "host": "localhost",
                "port": 3306,
                "username": "root",
                "password": "",
                "database": "phantom_courier",
                "table_name": "upload_records",
                "machine_name": "Machine-001"
            },
            "storage": {
                "upload_record_file": "uploaded.json",
                "failed_record_file": "failed.json",
                "dir_record_file": "dirs.json",
                "gating_record_file": "gating_records.json"
            },
            "logging": {
                "level": "INFO",
                "log_file": "service.log"
            }
        }
