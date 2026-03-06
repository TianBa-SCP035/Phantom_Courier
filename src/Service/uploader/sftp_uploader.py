import os
import paramiko
from typing import Dict


class SFTPUploader:
    """
    SFTP 上传器
    """

    def __init__(self, host: str, port: int, username: str, password: str, target_path: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.target_path = target_path
        self.ssh_client = None
        self.sftp_client = None

    def connect(self):
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_client.connect(
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=30
        )
        self.sftp_client = self.ssh_client.open_sftp()

    def disconnect(self):
        if self.sftp_client:
            self.sftp_client.close()
            self.sftp_client = None
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        try:
            remote_dir = os.path.dirname(remote_path)
            self._ensure_remote_dir(remote_dir)
            self.sftp_client.put(local_path, remote_path)
            return True
        except Exception:
            return False

    def _ensure_remote_dir(self, remote_dir: str):
        dirs = []
        while remote_dir != '/':
            try:
                self.sftp_client.stat(remote_dir)
                break
            except IOError:
                dirs.append(remote_dir)
                remote_dir = os.path.dirname(remote_dir)
        for dir_path in reversed(dirs):
            try:
                self.sftp_client.mkdir(dir_path)
            except:
                pass

    def upload_files(self, file_mapping: Dict[str, str]) -> Dict[str, bool]:
        results = {}
        for local_path, remote_path in file_mapping.items():
            results[local_path] = self.upload_file(local_path, remote_path)
        return results


if __name__ == '__main__':
    uploader = SFTPUploader(
        host="192.168.8.34",
        port=22,
        username="zhoukegang",
        password="123456",
        target_path="/SASdata/personal/zhoukegang/gatetest/"
    )

    test_file = r"D:\Code_Base\Phantom_Courier\tests\test1.csv"

    uploader.connect()
    try:
        remote_path = os.path.join(uploader.target_path, os.path.basename(test_file))
        result = uploader.upload_file(test_file, remote_path)
        print(f"[OK] {test_file} -> {remote_path}" if result else f"[FAIL] {test_file}")
    finally:
        uploader.disconnect()