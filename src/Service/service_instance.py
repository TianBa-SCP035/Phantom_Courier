import os
import time
import json
import threading
from typing import Dict, List, Optional
from config_loader import ConfigLoader
from logger import Logger
from scanner.file_scanner import FileScanner
from scanner.stability_checker import StabilityChecker
from uploader.sftp_uploader import SFTPUploader
from uploader.smb_uploader import SMBUploader
from gating.gating_manager import GatingManager


class ServiceInstance:
    """
    服务实例
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化服务实例
        
        Args:
            config_path: 配置文件路径
        """
        self.config_loader = ConfigLoader(config_path)
        
        scan_config = self.config_loader.get_scan_config()
        filter_config = self.config_loader.get_filter_config()
        stability_config = self.config_loader.get_stability_config()
        upload_config = self.config_loader.get_upload_config()
        gating_config = self.config_loader.get_gating_config()
        storage_config = self.config_loader.get_storage_config()
        logging_config = self.config_loader.get_logging_config()
        
        self.logger = Logger(
            'ServiceInstance',
            log_file=os.path.join(self.config_loader.get_logs_dir(), logging_config.get('log_file', 'service.log')),
            level=logging_config.get('level', 'INFO')
        )
        
        self.root_paths = scan_config.get('root_paths', [])
        self.scan_interval = scan_config.get('interval', 1800)
        self.recursive = scan_config.get('recursive', True)
        
        self.upload_record_file = os.path.join(self.config_loader.get_data_dir(), storage_config.get('upload_record_file', 'uploaded.json'))
        self.failed_record_file = os.path.join(self.config_loader.get_data_dir(), storage_config.get('failed_record_file', 'failed.json'))
        self.dir_record_file = os.path.join(self.config_loader.get_data_dir(), storage_config.get('dir_record_file', 'dirs.json'))
        
        self.uploaded_records: Dict[str, Dict] = {}
        self.failed_records: Dict[str, Dict] = {}
        self.dir_records: Dict[str, Dict] = {}
        
        self.is_first_run = not os.path.exists(self.dir_record_file)
        
        self._load_records()
        
        scan_config = self.config_loader.get_scan_config()
        always_scan_files = scan_config.get('always_scan_files', False)
        self.file_scanner = FileScanner(self.root_paths, filter_config, stability_config, self.dir_records, always_scan_files)
        self.stability_checker = self.file_scanner.get_stability_checker()
        
        self.upload_enabled = upload_config.get('enabled', True)
        self.upload_retry_count = upload_config.get('retry_count', 2)
        self.file_check_round = stability_config.get('file_check_round', 2)
        
        self.sftp_uploader = None
        self.smb_uploader = None
        self._init_uploaders(upload_config)
        
        storage_config = self.config_loader.get_storage_config()
        gating_record_file = storage_config.get('gating_record_file', 'gating_records.json')
        
        self.gating_manager = GatingManager(
            gating_config,
            self.config_loader.get_data_dir(),
            self.config_loader.get_bin_dir(),
            gating_record_file
        )
        
        self.running = False
        self.thread = None
        self.stop_event = threading.Event()
        self.is_uploading = False
    
    def _init_uploaders(self, upload_config: dict):
        """
        初始化上传器
        
        Args:
            upload_config: 上传配置
        """
        self.upload_destinations = upload_config.get('destinations', [])
        self.uploaders = []
        
        for dest in self.upload_destinations:
            protocol = dest.get('protocol', '')
            
            if protocol == 'sftp':
                uploader = SFTPUploader(
                    host=dest.get('host', ''),
                    port=dest.get('port', 22),
                    username=dest.get('username', ''),
                    password=dest.get('password', ''),
                    target_path=dest.get('target_path', '')
                )
                self.uploaders.append(uploader)
            elif protocol == 'smb':
                uploader = SMBUploader(
                    server_ip=dest.get('server_ip', ''),
                    server_port=dest.get('server_port', 139),
                    username=dest.get('username', ''),
                    password=dest.get('password', ''),
                    share_name=dest.get('share_name', ''),
                    target_path=dest.get('target_path', '')
                )
                self.uploaders.append(uploader)
    
    def _load_records(self):
        """
        加载记录文件
        """
        if os.path.exists(self.upload_record_file):
            try:
                with open(self.upload_record_file, 'r', encoding='utf-8') as f:
                    self.uploaded_records = json.load(f)
            except Exception as e:
                self.logger.error(f"加载上传记录失败: {e}")
        
        if os.path.exists(self.failed_record_file):
            try:
                with open(self.failed_record_file, 'r', encoding='utf-8') as f:
                    self.failed_records = json.load(f)
            except Exception as e:
                self.logger.error(f"加载失败记录失败: {e}")
        
        if os.path.exists(self.dir_record_file):
            try:
                with open(self.dir_record_file, 'r', encoding='utf-8') as f:
                    self.dir_records = json.load(f)
            except Exception as e:
                self.logger.error(f"加载目录记录失败: {e}")
    
    def _save_records(self):
        """
        保存记录文件
        """
        try:
            os.makedirs(os.path.dirname(self.upload_record_file), exist_ok=True)
            with open(self.upload_record_file, 'w', encoding='utf-8') as f:
                json.dump(self.uploaded_records, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存上传记录失败: {e}")
        
        try:
            with open(self.failed_record_file, 'w', encoding='utf-8') as f:
                json.dump(self.failed_records, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存失败记录失败: {e}")
        
        try:
            with open(self.dir_record_file, 'w', encoding='utf-8') as f:
                json.dump(self.dir_records, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存目录记录失败: {e}")
    
    def start(self):
        """
        启动服务
        """
        if self.running:
            self.logger.warning("服务已在运行中")
            return
        
        self.running = True
        
        filter_config = self.config_loader.get_filter_config()
        folder_mode = filter_config.get('folder_mode', filter_config.get('mode', 'whitelist'))
        file_mode = filter_config.get('file_mode', filter_config.get('mode', 'whitelist'))
        include_folders = filter_config.get('include_folders', [])
        exclude_folders = filter_config.get('exclude_folders', [])
        include_patterns = filter_config.get('include_patterns', [])
        exclude_patterns = filter_config.get('exclude_patterns', [])
        
        if folder_mode == 'whitelist':
            folder_info = "全部" if not include_folders else f"{include_folders}"
        else:
            folder_info = "全部" if not exclude_folders else f"{exclude_folders}"
        
        if file_mode == 'whitelist':
            file_info = "全部" if not include_patterns else f"{include_patterns}"
        else:
            file_info = "全部" if not exclude_patterns else f"{exclude_patterns}"
        
        self.logger.info(f"文件夹-{folder_mode}模式：{folder_info}；文件-{file_mode}模式：{file_info}")
        
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """
        停止服务
        """
        if not self.running:
            self.logger.warning("服务未运行")
            return
        
        self.running = False
        self.stop_event.set()
        
        if self.is_uploading:
            self.logger.info("等待当前上传任务完成...")
        
        if self.thread:
            self.thread.join(timeout=60)
        
        self._save_records()
        self._disconnect_uploaders()
        self.logger.info("服务已停止")
    
    def _run(self):
        """
        运行服务主循环
        """
        gating_status = "开启" if self.gating_manager.enabled else "关闭"
        
        if self.is_first_run:
            upload_config = self.config_loader.get_upload_config()
            upload_on_first_run = upload_config.get('upload_on_first_run', True)
            if upload_on_first_run:
                self.logger.info(f"开始首次扫描，上传已有文件，自动圈门{gating_status}")
            else:
                self.logger.info(f"开始首次扫描，不上传已有文件，自动圈门{gating_status}")
        else:
            self.logger.info(f"开始扫描，自动圈门{gating_status}")
        
        self._scan()
        
        while self.running:
            self.stop_event.wait(self.scan_interval)
            
            if not self.running:
                break
            
            self.logger.info(f"开始定期扫描（间隔: {self.scan_interval}秒）")
            self._scan()
    
    def _scan(self):
        """
        执行扫描
        """
        try:
            self.is_first_run = not os.path.exists(self.dir_record_file)
            
            dir_paths = self.file_scanner.scan(recursive=self.recursive)
            
            uploaded_count = 0
            for dir_path in dir_paths:
                if not self.running:
                    break
                
                self.file_scanner.update_dir_scan_record(dir_path)
                
                dir_record = self.dir_records.get(dir_path, {})
                dir_record['last_scan_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
                self.dir_records[dir_path] = dir_record
            
            for dir_path in dir_paths:
                if not self.running:
                    break
                
                uploaded_count += self._process_directory(dir_path)
            
            if not self.running:
                return
            
            self._save_records()
            self.logger.info(f"扫描完成，共处理 {len(dir_paths)} 个目录，上传了 {uploaded_count} 个文件")
        except Exception as e:
            self.logger.error(f"扫描失败: {e}")
    
    def _process_directory(self, dir_path: str) -> int:
        """
        处理目录
        
        Args:
            dir_path: 目录路径
        
        Returns:
            上传的文件数量
        """
        self.logger.info(f"处理目录: {dir_path}")
        
        uploaded_count = 0
        files_info = {}
        
        if self.upload_enabled:
            files_info = self._filter_files(dir_path)
            uploaded_count = self._upload_files(dir_path, files_info)
        
        if self.gating_manager.enabled and uploaded_count > 0:
            self._process_gating(dir_path, files_info)
        
        return uploaded_count
    
    def _filter_files(self, dir_path: str) -> Dict[str, Dict]:
        """
        文件判别阶段：过滤出需要上传的文件
        
        Args:
            dir_path: 目录路径
        
        Returns:
            文件路径到文件信息的映射
        """
        files_info = {}
        
        try:
            filenames = os.listdir(dir_path)
        except Exception as e:
            return files_info
        
        for filename in filenames:
            file_path = os.path.join(dir_path, filename)
            
            if not os.path.isfile(file_path):
                continue
            
            if not self.file_scanner.file_filter.should_include_file(file_path):
                continue
            
            try:
                file_stat = os.stat(file_path)
                files_info[file_path] = {
                    'path': file_path,
                    'size': file_stat.st_size,
                    'mod_time': file_stat.st_mtime
                }
            except Exception as e:
                pass
        
        files_to_upload = []
        
        for file_path, file_info in files_info.items():
            uploaded_record = self.uploaded_records.get(file_path)
            failed_record = self.failed_records.get(file_path)
            
            if failed_record is not None:
                if failed_record.get('mod_time') != file_info['mod_time'] or failed_record.get('size') != file_info['size']:
                    files_to_upload.append(file_path)
                else:
                    retry_count = failed_record.get('retry_count', 0)
                    if retry_count < self.upload_retry_count:
                        files_to_upload.append(file_path)
            elif uploaded_record is not None:
                if uploaded_record.get('mod_time') != file_info['mod_time'] or uploaded_record.get('size') != file_info['size']:
                    files_to_upload.append(file_path)
                else:
                    uploaded_destinations = uploaded_record.get('destinations', {})
                    
                    all_success = True
                    for dest_index in range(len(self.upload_destinations)):
                        dest_config = self.upload_destinations[dest_index]
                        protocol = dest_config.get('protocol', '')
                        target_path = dest_config.get('target_path', '')
                        ip = dest_config.get('host', '') if protocol == 'sftp' else dest_config.get('server_ip', '')
                        
                        for root_path in self.root_paths:
                            if file_path.startswith(root_path):
                                relative_path = os.path.relpath(file_path, root_path)
                                break
                        else:
                            relative_path = os.path.basename(file_path)
                        
                        expected_target_path = target_path
                        if expected_target_path and not expected_target_path.endswith('/'):
                            expected_target_path += '/'
                        expected_target_path += relative_path
                        expected_target_path = expected_target_path.replace('\\', '/')
                        
                        found = False
                        for uploaded_dest in uploaded_destinations.values():
                            if (uploaded_dest.get('protocol') == protocol and 
                                uploaded_dest.get('ip') == ip and 
                                uploaded_dest.get('target_path') == expected_target_path):
                                found = True
                                if uploaded_dest.get('status') != 'success':
                                    all_success = False
                                    break
                                break
                        
                        if not found:
                            all_success = False
                            break
                    
                    if not all_success:
                        files_to_upload.append(file_path)
            else:
                files_to_upload.append(file_path)
        
        return {file_path: files_info[file_path] for file_path in files_to_upload}
    
    def _upload_files(self, dir_path: str, files_info: Dict[str, Dict]) -> int:
        """
        上传文件
        
        Args:
            dir_path: 目录路径
            files_info: 文件信息
        
        Returns:
            上传的文件数量
        """
        self.is_uploading = True
        
        try:
            if not files_info:
                return 0
            
            upload_config = self.config_loader.get_upload_config()
            upload_on_first_run = upload_config.get('upload_on_first_run', True)
            
            if self.is_first_run and not upload_on_first_run:
                for file_path in files_info.keys():
                    file_stat = os.stat(file_path)
                    destinations = {}
                    for dest_index in range(len(self.upload_destinations)):
                        dest_key = str(dest_index)
                        dest_config = self.upload_destinations[dest_index]
                        protocol = dest_config.get('protocol', '')
                        
                        for root_path in self.root_paths:
                            if file_path.startswith(root_path):
                                relative_path = os.path.relpath(file_path, root_path)
                                break
                        else:
                            relative_path = os.path.basename(file_path)
                        
                        target_path = dest_config.get('target_path', '')
                        if target_path:
                            target_path = os.path.join(target_path, relative_path).replace('\\', '/')
                        
                        ip = dest_config.get('host', '') if protocol == 'sftp' else dest_config.get('server_ip', '')
                        
                        destinations[dest_key] = {
                            'protocol': protocol,
                            'ip': ip,
                            'target_path': target_path,
                            'upload_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'status': 'success'
                        }
                    self.uploaded_records[file_path] = {
                        'size': file_stat.st_size,
                        'mod_time': file_stat.st_mtime,
                        'destinations': destinations
                    }
                self._save_records()
                self.logger.info(f"上传 0 个文件，{len(files_info)} 个文件已标记，失败 0 个")
                return 0
            
            uploaded_count = 0
            remaining_files = list(files_info.keys())
            failed_files = set()
            
            for round_count in range(1, self.file_check_round + 1):
                if not self.running:
                    break
                
                if not remaining_files:
                    break
                
                for check_count in range(1, self.stability_checker.file_check_count + 1):
                    if not self.running:
                        break
                    
                    if check_count < self.stability_checker.file_check_count:
                        time.sleep(self.stability_checker.file_check_interval)
                
                stable_results = self.stability_checker.check_files_stability(remaining_files)
                stable_files = [file_path for file_path, is_stable in stable_results.items() if is_stable]
                
                if stable_files:
                    round_uploaded_files = self._upload_stable_files(dir_path, stable_files)
                    uploaded_count += len(round_uploaded_files)
                    remaining_files = [f for f in remaining_files if f not in stable_files]
                    failed_files.update([f for f in stable_files if f not in round_uploaded_files])
            
            failed_count = len(failed_files)
            self.logger.info(f"上传 {uploaded_count} 个文件，0 个文件已标记，失败 {failed_count} 个")
            
            return uploaded_count
        finally:
            self.is_uploading = False
    
    def _get_stable_files(self, file_paths: List[str]) -> List[str]:
        """
        获取稳定的文件列表
        
        Args:
            file_paths: 文件路径列表
        
        Returns:
            稳定的文件路径列表
        """
        stable_results = self.stability_checker.check_files_stability(file_paths)
        return [file_path for file_path, is_stable in stable_results.items() if is_stable]
    
    def _upload_stable_files(self, dir_path: str, stable_files: List[str]) -> set:
        """
        上传稳定的文件
        
        Args:
            dir_path: 目录路径
            stable_files: 稳定的文件列表
        
        Returns:
            上传成功的文件集合
        """
        if not stable_files:
            return set()
        
        uploaded_files = set()
        
        for file_path in stable_files:
            file_stat = os.stat(file_path)
            
            if file_path not in self.uploaded_records:
                self.uploaded_records[file_path] = {
                    'size': file_stat.st_size,
                    'mod_time': file_stat.st_mtime,
                    'destinations': {}
                }
            else:
                self.uploaded_records[file_path]['size'] = file_stat.st_size
                self.uploaded_records[file_path]['mod_time'] = file_stat.st_mtime
            
            all_success = True
            upload_config = self.config_loader.get_upload_config()
            preserve_structure = upload_config.get('preserve_structure', True)
            
            for dest_index, uploader in enumerate(self.uploaders):
                if uploader is None:
                    all_success = False
                    continue
                
                try:
                    uploader.connect()
                    
                    if preserve_structure:
                        for root_path in self.root_paths:
                            if file_path.startswith(root_path):
                                relative_path = os.path.relpath(file_path, root_path)
                                break
                        else:
                            relative_path = os.path.basename(file_path)
                    else:
                        relative_path = os.path.basename(file_path)
                    
                    if isinstance(uploader, SFTPUploader) and uploader.target_path:
                        remote_path = os.path.join(uploader.target_path, relative_path).replace('\\', '/')
                    elif isinstance(uploader, SMBUploader) and uploader.target_path:
                        remote_path = os.path.join(uploader.target_path, relative_path).replace('\\', '/')
                    else:
                        remote_path = os.path.join(dir_path, relative_path)
                    
                    success = uploader.upload_file(file_path, remote_path)
                    
                    if not success:
                        time.sleep(2)
                        success = uploader.upload_file(file_path, remote_path)
                    
                    if success:
                        self.uploaded_records[file_path]['destinations'][str(dest_index)] = {
                            'protocol': self.upload_destinations[dest_index].get('protocol', ''),
                            'ip': self.upload_destinations[dest_index].get('host', '') if self.upload_destinations[dest_index].get('protocol') == 'sftp' else self.upload_destinations[dest_index].get('server_ip', ''),
                            'target_path': remote_path,
                            'upload_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'status': 'success'
                        }
                    else:
                        self.uploaded_records[file_path]['destinations'][str(dest_index)] = {
                            'protocol': self.upload_destinations[dest_index].get('protocol', ''),
                            'ip': self.upload_destinations[dest_index].get('host', '') if self.upload_destinations[dest_index].get('protocol') == 'sftp' else self.upload_destinations[dest_index].get('server_ip', ''),
                            'target_path': remote_path,
                            'upload_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'status': 'failed'
                        }
                        all_success = False
                    
                    uploader.disconnect()
                except Exception as e:
                    self.logger.error(f"上传失败: {e}")
                    if uploader:
                        uploader.disconnect()
                    all_success = False
            
            if all_success:
                if file_path in self.failed_records:
                    del self.failed_records[file_path]
                uploaded_files.add(file_path)
            else:
                if file_path not in self.failed_records:
                    self.failed_records[file_path] = {
                        'size': file_stat.st_size,
                        'mod_time': file_stat.st_mtime,
                        'error': 'Upload failed',
                        'retry_count': 0,
                        'last_fail_time': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                else:
                    failed_record = self.failed_records[file_path]
                    
                    if failed_record.get('size') != file_stat.st_size or failed_record.get('mod_time') != file_stat.st_mtime:
                        retry_count = 0
                    else:
                        retry_count = failed_record.get('retry_count', 0) + 1
                    
                    self.failed_records[file_path] = {
                        'size': file_stat.st_size,
                        'mod_time': file_stat.st_mtime,
                        'error': 'Upload failed',
                        'retry_count': retry_count,
                        'last_fail_time': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
        
        self._save_records()
        return uploaded_files
    
    def _process_gating(self, dir_path: str, files_info: Dict[str, Dict]):
        """
        处理 Gating
        
        Args:
            dir_path: 目录路径
            files_info: 文件信息
        """
        self.gating_manager.submit_task_async(dir_path)
    
    def _disconnect_uploaders(self):
        """
        断开上传器连接
        """
        if self.sftp_uploader:
            try:
                self.sftp_uploader.disconnect()
            except:
                pass
        
        if self.smb_uploader:
            try:
                self.smb_uploader.disconnect()
            except:
                pass