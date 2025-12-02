import getpass
import logging

import psutil

from src.presence_manager.config import Config
from src.presence_manager.interfaces import LocalGameFetchPayload


current_user = getpass.getuser()

class LocalGetter:
    def __init__(self, config: Config):
        self.config = config

    def fetch(self) -> list[LocalGameFetchPayload]:
        logging.debug("Fetching local process information")

        return_payloads: list[LocalGameFetchPayload] = []

        desired_processes: list[psutil.Process] = {}
        desired_process_names = [process.get("process_name") for process in self.config.local.processes]

        for process in psutil.process_iter(['username', 'name']):
            # this should handle shitdows domain format "DOMAIN\\user"
            username = process.info['username'].split('\\')[-1]

            if username == current_user:
                if process.name() in desired_process_names:
                    logging.debug("found running proccess %s", process.name())
                    desired_processes[process.name()] = process

        for process_name, process in desired_processes.items():
            try:
                process_exe = process.exe()
            except Exception:
                process_exe = None
            
            display_name = None
            for config_process_entry in self.config.local.processes:
                if config_process_entry["process_name"] == process_name:
                    display_name = config_process_entry["display_name"]

            payload = LocalGameFetchPayload(
                process_name = process.name(),
                process_ID = process.pid,
                start_time = round(process.create_time()),
                process_exe = process_exe,
                display_name = display_name,
            )
            return_payloads.append(payload)

        return return_payloads
