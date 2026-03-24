import json
import os
from typing import Dict, Any
from env import get_project_root


class ConfigManager:
    def __init__(self):
        self.config_path = self._find_config_file()
        self.config = {}
        self.load_config()

    def _find_config_file(self) -> str:
        project_root = get_project_root()
        return os.path.join(project_root, 'config', 'service_config.json')

    def load_config(self) -> bool:
        try:
            if not os.path.exists(self.config_path):
                self.config = self._get_default_config()
                return self.save_config()
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            return True
        except Exception:
            self.config = self._get_default_config()
            return False

    def save_config(self) -> bool:
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
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
                "interval": 1800,
                "recursive": True,
                "always_scan_files": False,
                "upload_on_first_run": True
            },
            "filter": {
                "folder_mode": "blacklist",
                "include_folders": [],
                "exclude_folders": ["temp", "cache"],
                "file_mode": "blacklist",
                "include_patterns": [],
                "exclude_patterns": ["temp_*"],
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
