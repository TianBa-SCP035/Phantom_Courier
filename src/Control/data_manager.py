import json
import os
from typing import Dict, Any
from env import get_project_root

class DataManager:
    def __init__(self):
        self.data_dir = self._find_data_dir()

    def _find_data_dir(self) -> str:
        project_root = get_project_root()
        return os.path.join(project_root, 'data')

    def _read_json(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            return {}
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except Exception as e:
            print(f"Failed to read {filename}: {e}")
            return {}

    def get_stats(self) -> Dict[str, int]:
        return {
            'uploaded_files': len(self._read_json('uploaded.json')),
            'failed_files': len(self._read_json('failed.json')),
            'monitored_dirs': len(self._read_json('dirs.json')),
            'gating_calls': len(self._read_json('gating_records.json')),
        }

    def get_raw_data(self, filename: str) -> Dict[str, Any]:
        return self._read_json(filename)

    def get_log_path(self, log_file: str = 'service.log') -> str:
        project_root = get_project_root()
        return os.path.join(project_root, 'logs', log_file)
