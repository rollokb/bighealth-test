import logging.config
import yaml

# Set up logging using a yaml file
with open('logging.conf') as f:
    config = yaml.load(f)
    config.setdefault('version', 1)
    logging.config.dictConfig(config)
