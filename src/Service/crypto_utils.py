import json
from cryptography.fernet import Fernet


class ConfigDecryptor:
    def __init__(self, key: bytes = None):
        if key is None:
            key = b'672q4nfuqDVExT7GVEy4jMjzUV_jbfn1AoBPN7FfS0o='
        self.cipher = Fernet(key)

    def decrypt_config(self, encrypted_data: bytes) -> dict:
        decrypted_bytes = self.cipher.decrypt(encrypted_data)
        json_str = decrypted_bytes.decode('utf-8')
        return json.loads(json_str)

    def decrypt_config_from_file(self, file_path: str) -> dict:
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
        return self.decrypt_config(encrypted_data)
