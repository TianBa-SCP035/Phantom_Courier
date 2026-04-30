import json
import os
from typing import Dict, Any
from env import get_project_root

class DataManager:
    def __init__(self):
        self.data_dir = self._find_data_dir()
        self._json_cache = {}

    def _find_data_dir(self) -> str:
        project_root = get_project_root()
        return os.path.join(project_root, 'data')

    def _read_json(self, filename: str) -> Dict[str, Any]:
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            return {}
        try:
            stat = os.stat(path)
            cache = self._json_cache.get(filename)
            if cache and cache.get("mtime") == stat.st_mtime and cache.get("size") == stat.st_size:
                return cache.get("data", {})

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                data = json.loads(content) if content else {}
                self._json_cache[filename] = {
                    "mtime": stat.st_mtime,
                    "size": stat.st_size,
                    "data": data,
                }
                return data
        except Exception as e:
            print(f"Failed to read {filename}: {e}")
            return {}

    def get_stats(self, refresh_enabled: Dict[str, bool] = None) -> Dict[str, int]:
        mapping = {
            'uploaded_files': 'uploaded.json',
            'failed_files': 'failed.json',
            'monitored_dirs': 'dirs.json',
            'gating_calls': 'gating_records.json',
        }
        stats = {}
        for key, filename in mapping.items():
            if refresh_enabled is not None and not refresh_enabled.get(filename, True):
                cache = self._json_cache.get(filename)
                stats[key] = len(cache.get("data", {})) if cache else None
            else:
                stats[key] = len(self._read_json(filename))
        return stats

    def get_raw_data(self, filename: str) -> Dict[str, Any]:
        return self._read_json(filename)

    def get_log_path(self, log_file: str = 'service.log') -> str:
        project_root = get_project_root()
        return os.path.join(project_root, 'logs', log_file)
