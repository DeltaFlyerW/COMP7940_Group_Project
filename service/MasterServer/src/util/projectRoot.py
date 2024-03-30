from pathlib import Path

projectRoot = Path(__file__)
while "MasterServer" not in projectRoot.name:
    projectRoot = projectRoot.parent
