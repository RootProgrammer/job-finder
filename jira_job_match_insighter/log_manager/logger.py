import logging
from pathlib import Path


class Logger(object):
    @classmethod
    def setup_logging(cls):
        main_logger = logging.getLogger("main")
        main_logger.setLevel(logging.DEBUG)

        base_dir = Path(__file__).resolve().parent.parent
        log_folder = (
                base_dir /
                "output" /
                "artifact" /
                "logs"
        )
        log_folder.mkdir(parents=True, exist_ok=True)
        log_file_path = log_folder / f"linkedin_ingestor_log.txt"

        file_handler = logging.FileHandler(str(log_file_path))
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        main_logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        main_logger.addHandler(console_handler)

        return main_logger
