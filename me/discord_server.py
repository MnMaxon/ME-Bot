import dataclasses

from pathlib import Path

import yaml

from me import me_util

_IGNORE_ON_LOAD_CONFIG_KEYS = ['example_old_config_key', 'path']
_IGNORE_ON_SAVE_CONFIG_KEYS = ['path']


@dataclasses.dataclass
class ServerManager:
    pass


@dataclasses.dataclass
class ServerConfig:
    path = None

    def save(self, path: Path = None):
        if path is None:
            if self.path is None:
                raise ValueError("path cannot be null in both the 'save' function and 'ServerConfig' instance")
            path = self.path
        conf_dict = self.__dict__.copy()
        conf_dict = {k: v for k, v in conf_dict.items() if k not in _IGNORE_ON_SAVE_CONFIG_KEYS}
        path.parent.mkdir(exist_ok=True, parents=True)
        with path.open('w') as f:
            yaml.dump(conf_dict, f)
        return conf_dict


def load_config(path: Path):
    with open(path, 'r') as f:
        conf = yaml.safe_load(f)
    return {k: v for k, v in conf.items() if k not in _IGNORE_ON_LOAD_CONFIG_KEYS}


@dataclasses.dataclass
class DiscordServer:
    server_id: str

    def get_folder_path(self):
        return me_util.get_data_folder() / 'server_id'

    def get_config_path(self):
        folder_path = self.get_folder_path()
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path / 'server_config.yaml'

    def get_config(self) -> ServerConfig:
        config_path = self.get_config_path()
        conf_dict = load_config(config_path)
        conf_dict['path'] = config_path
        return ServerConfig(**conf_dict)
