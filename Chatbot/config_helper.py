import yaml
import os


def load_config(config_path='config.yml'):
    # Get the directory where config_helper.py is located
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Create absolute path to config file
    config_file_path = os.path.join(base_dir, config_path)

    with open(config_file_path, 'r') as file:
        config = yaml.safe_load(file)
    return config


# Get database parameters
def get_db_params():
    config = load_config()
    return config.get('database', {})


# Get API URLs
def get_api_urls():
    config = load_config()
    return config.get('apis', {})