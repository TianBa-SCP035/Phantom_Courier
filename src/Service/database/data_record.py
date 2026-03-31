import os
import uuid
import threading
from typing import Dict, Any
import time
import logging


class DataRecorder:
    """
    数据记录器（数据库写入）
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        """
        初始化数据记录器
        
        Args:
            db_config: 数据库配置（包含machine_name、table_name）
        """
        self.enabled = db_config.get('enabled', False)
        self.host = db_config.get('host', 'localhost')
        self.port = db_config.get('port', 3306)
        self.username = db_config.get('username', 'root')
        self.password = db_config.get('password', '')
        self.database = db_config.get('database', 'phantom_courier')
        self.table_name = db_config.get('table_name', 'upload_records')
        self.machine_name = db_config.get('machine_name', 'Unknown')
        self.mac_address = self._get_mac_address()
        
        self.connection = None
        self.logger = logging.getLogger('DataRecorder')
    
    def _get_mac_address(self) -> str:
        """
        获取机器MAC地址
        
        Returns:
            MAC地址字符串
        """
        try:
            mac = uuid.getnode()
            mac_address = ':'.join(['{:02x}'.format((mac >> elements) & 0xff) for elements in range(0, 2*6, 2)][::-1])
            return mac_address
        except Exception:
            return '00:00:00:00:00:00'
    
    def connect(self) -> bool:
        """
        连接数据库
        
        Returns:
            True: 连接成功
            False: 连接失败
        """
        if not self.enabled:
            return False
        
        try:
            import pymysql
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database,
                charset='utf8mb4'
            )
            return True
        except ImportError:
            self.logger.error("pymysql 模块未安装，请运行: pip install pymysql")
            return False
        except Exception as e:
            self.logger.error(f"数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """
        断开数据库连接
        """
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            finally:
                self.connection = None
    
    def save_upload_records_async(self, upload_snapshot: Dict[str, Dict]):
        """
        异步保存上传记录
        
        Args:
            upload_snapshot: 本次上传结果快照
                {
                    'file_path1': {
                        'name': 'filename',
                        'size': 1024,
                        'mod_time': 1234567890,
                        'destinations': [
                            {
                                'protocol': 'sftp',
                                'ip': '192.168.1.1',
                                'target_path': '/path/to/file',
                                'upload_time': '2026-03-31 10:00:00',
                                'status': 'success'
                            },
                            ...
                        ]
                    },
                    ...
                }
        """
        if not self.enabled:
            return
        
        thread = threading.Thread(
            target=self._save_upload_records,
            args=(upload_snapshot,),
            daemon=True
        )
        thread.start()
    
    def _save_upload_records(self, upload_snapshot: Dict[str, Dict]):
        """
        保存上传记录到数据库（在线程中执行）
        
        Args:
            upload_snapshot: 本次上传结果快照
        """
        try:
            if not self.connect():
                return
            
            cursor = self.connection.cursor()
            
            for file_path, file_data in upload_snapshot.items():
                mod_time_datetime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_data.get('mod_time', 0)))
                
                for dest in file_data.get('destinations', []):
                    sql = f"""
                    INSERT INTO {self.table_name} (
                        mac_address, machine_name,
                        file_path, file_name, file_size, mod_time,
                        protocol, dest_addr, dest_path,
                        status, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        machine_name = VALUES(machine_name),
                        file_name = VALUES(file_name),
                        file_size = VALUES(file_size),
                        mod_time = VALUES(mod_time),
                        status = VALUES(status),
                        updated_at = VALUES(updated_at)
                    """
                    cursor.execute(sql, (
                        self.mac_address,
                        self.machine_name,
                        file_path,
                        file_data.get('name', ''),
                        file_data.get('size', 0),
                        mod_time_datetime,
                        dest.get('protocol', ''),
                        dest.get('ip', ''),
                        dest.get('target_path', ''),
                        dest.get('status', ''),
                        time.strftime('%Y-%m-%d %H:%M:%S')
                    ))
            
            self.connection.commit()
            cursor.close()
        except Exception as e:
            self.logger.error(f"保存上传记录到数据库失败: {e}")
            if self.connection:
                try:
                    self.connection.rollback()
                except Exception:
                    pass
        finally:
            self.disconnect()
