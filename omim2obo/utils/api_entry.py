from pathlib import Path


def check_version(file_path):
    print(Path(file_path).stat())

