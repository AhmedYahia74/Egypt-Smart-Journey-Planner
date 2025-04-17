import yaml

def load_config(config_path='config.yml'):
    with open(config_path, 'r') as file:
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