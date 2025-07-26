import json
import os
from pathlib import Path


class CubacelSDKConfig:
    def __init__(self, custom_config_file=None, **kwargs):
        if not custom_config_file:
            custom_config_file = Path(os.path.join(Path(__file__).resolve().parent.parent, 'config', 'cubacel.json'))

        self.CONFIG_FILE = custom_config_file

        if self.CONFIG_FILE.exists():
            with self.CONFIG_FILE.open('r') as f:
                data = json.load(f)
        else:
            data = {}

        if 'password' not in data:
            data['password'] = os.getenv('CUBACEL_PASSWORD', '')

        self.PASSWORD = data['password']

        self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with self.CONFIG_FILE.open('w') as f:
            json.dump(data, f, indent=2)

        self.HOST = os.getenv('CUBACEL_HOST', '')
        self.USERNAME = os.getenv('CUBACEL_USERNAME', '')
        self.SIM_TUR_ID = os.getenv('CUBACEL_SIM_TUR_ID', '')
        self.MIN_BATCH_SIM_TUR = os.getenv('CUBACEL_MIN_BATCH_SIMTUR', '')
        self.MAX_BATCH_SIM_TUR = os.getenv('CUBACEL_MAX_BATCH_SIMTUR', '')
        self.ENVIRONMENT = os.getenv('CUBACEL_ENVIRONMENT', '')
        self.VERBOSE_ENABLED = bool(int(os.getenv('CUBACEL_VERBOSE_ENABLED', '0')))

    def change_password(self, password):
        with self.CONFIG_FILE.open('r') as file_read:
            data = json.load(file_read)
            data['password'] = password

            with self.CONFIG_FILE.open('w') as file_write:
                json.dump(data, file_write, indent=2)
