"""
CLI entry point for hydrophone_downloader.

To run as a module:
    python -m hydrophone_downloader.cli
"""


import hydra
from omegaconf import DictConfig
from dotenv import load_dotenv, set_key
import os

from .downloader import download_data



# Set config path relative to this file
LOCAL_PATH = os.path.abspath(__file__)
CONFIG_PATH = os.path.join(os.path.dirname(LOCAL_PATH), 'configs')


@hydra.main(config_path=CONFIG_PATH, config_name="config", version_base="1.3")
def main(cfg: DictConfig):
    """
    Main entry point for data download.
    """
    download_data(
        min_lat=cfg.min_latitude, 
        max_lat=cfg.max_latitude,
        min_lon=cfg.min_longitude, 
        max_lon=cfg.max_longitude, 
        min_depth=cfg.min_depth,
        max_depth=cfg.max_depth,
        license=cfg.license,
        start_time=cfg.start_time,
        end_time=cfg.end_time,
        save_dir=cfg.save_dir,
    )

@hydra.main(config_path=CONFIG_PATH, config_name="token_config")
def set_token(cfg: DictConfig):
    """
    Command to set the API token and store it in .env file.
    """
    dotenv_file = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)), '.env')
    set_key(dotenv_file, "ONC_TOKEN", cfg.ONC_token)
    print(f"ONC API token set successfully.")

if __name__ == "__main__":
    main()

