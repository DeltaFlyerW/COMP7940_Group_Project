from pathlib import Path
import logging
projectRoot = Path(__file__)
while "MasterServer" not in projectRoot.name:
    projectRoot = projectRoot.parent

logging.info("Project root %s", projectRoot)
