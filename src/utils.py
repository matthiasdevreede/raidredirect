import logging
import yaml
import datetime as dt
import os

class LoggerSetup:
    # A utility class to configure and return a logger instance.

    def __init__(self,name):
        """
        Initialize the logger setup.

        Parameters
        ----------
        name : str
            The name used for the logger.
        """

        self.name = name
        self.log_dir = "logs/"
        self.level = logging.INFO
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """
        Set up the logger with file and console handlers.

        Returns
        -------
        logger : logging.Logger
            Configured logger instance.
        """
        
        # Create logger
        logger = logging.getLogger('Logger')
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s] %(message)s')

        # Setup where and how logging files should be used
        log_filename = os.path.join(self.log_dir, f"{dt.datetime.now().strftime('%Y-%m-%d')}.log")
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setLevel(self.level)
        file_handler.setFormatter(formatter)

        # Setup console logs for more in depth debugging.
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger

    def get_logger(self):
        """
        Retrieve the configured logger.

        Returns
        -------
        logger : logging.Logger
            The logger instance.
        """

        return self.logger

class YAMLReader:
    # Class to read .yaml files.
    def __init__(self, logger=None):
        """
        Initialize the YAML reader.

        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance. If None, a default logger is used.
        """

        self.logger = logger or logging.getLogger("UtilLogger")
    
    def get_yaml(self,config_path):
        """
        Load a YAML configuration file.

        Parameters
        ----------
        config_path : str
            Path to the YAML configuration file.

        Returns
        -------
        config : dict
            Parsed configuration dictionary. Returns empty dictionary on failure.
        """

        # Try to get config file and load it in as a dictionary.
        try:
            with open(config_path) as stream:
                self.config = yaml.safe_load(stream)
        except yaml.YAMLError as exception:
            self.logger.error(f"Error loading config: {exception}")
            self.config = {}

        return self.config