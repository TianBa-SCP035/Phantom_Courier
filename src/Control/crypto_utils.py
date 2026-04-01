import json
from cryptography.fernet import Fernet


class ConfigEncryptor:
    def __init__(self, key: bytes = None):
        if key is None:
            key = b'672q4nfuqDVExT7GVEy4jMjzUV_jbfn1AoBPN7FfS0o='
        self.cipher = Fernet(key)

    def encrypt_config(self, config: dict) -> bytes:
        json_str = json.dumps(config, ensure_ascii=False)
        return self.cipher.encrypt(json_str.encode('utf-8'))

    def decrypt_config(self, encrypted_data: bytes) -> dict:
        decrypted_bytes = self.cipher.decrypt(encrypted_data)
        json_str = decrypted_bytes.decode('utf-8')
        return json.loads(json_str)

    def encrypt_config_to_file(self, config: dict, file_path: str):
        encrypted_data = self.encrypt_config(config)
        with open(file_path, 'wb') as f:
            f.write(encrypted_data)

    def decrypt_config_from_file(self, file_path: str) -> dict:
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
        return self.decrypt_config(encrypted_data)
