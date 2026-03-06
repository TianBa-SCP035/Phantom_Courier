import os
from smb.SMBConnection import SMBConnection
from typing import Dict


class SMBUploader:
    """
    SMB 上传器
    """

    def __init__(self, server_ip: str, server_port: int, username: str, password: str, share_name: str, target_path: str):
        self.server_ip = server_ip
        self.server_port = server_port
        self.username = username
        self.password = password
        self.share_name = share_name
        self.target_path = target_path
        self.smb_client = None

    def connect(self):
        self.smb_client = SMBConnection(
            self.username,
            self.password,
            'client',
            self.server_ip,
            use_ntlm_v2=True,
        )
        self.smb_client.connect(self.server_ip, self.server_port, timeout=30)

    def disconnect(self):
        if self.smb_client:
            self.smb_client.close()
            self.smb_client = None

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        try:
            remote_dir = os.path.dirname(remote_path)
            self._ensure_remote_dir(remote_dir)
            with open(local_path, 'rb') as f:
                self.smb_client.storeFile(self.share_name, remote_path, f)
            return True
        except Exception:
            return False

    def _ensure_remote_dir(self, remote_dir: str):
        remote_dir = (remote_dir or "/").replace("\\", "/")
        if remote_dir in ("/", ""):
            return
        parts = [p for p in remote_dir.split("/") if p]
        cur = ""
        for p in parts:
            cur = cur + "/" + p
            try:
                self.smb_client.listPath(self.share_name, cur)
            except Exception:
                self.smb_client.createDirectory(self.share_name, cur)

    def upload_files(self, file_mapping: Dict[str, str]) -> Dict[str, bool]:
        results = {}
        for local_path, remote_path in file_mapping.items():
            results[local_path] = self.upload_file(local_path, remote_path)
        return results


if __name__ == "__main__":
    uploader = SMBUploader(
        server_ip="192.168.8.104",
        server_port=139,
        username="柴梦亚",
        password="A123456a#",
        share_name="生物信息中心",
        target_path="/jiangchuandi/test"
    )

    test_file = r"D:\Code_Base\Phantom_Courier\tests\test1.csv"

    uploader.connect()
    try:
        remote_path = os.path.join(uploader.target_path, os.path.basename(test_file))
        result = uploader.upload_file(test_file, remote_path)
        print(f"[OK] {test_file} -> {remote_path}" if result else f"[FAIL] {test_file}")
    finally:
        uploader.disconnect()