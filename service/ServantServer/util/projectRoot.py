from pathlib import Path

projectRoot = Path(__file__)
while "ServantServer" not in projectRoot.name:
    projectRoot = projectRoot.parent
