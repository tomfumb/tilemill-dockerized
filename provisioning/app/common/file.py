import os

def skip_file_creation(path: str) -> bool:
    return os.path.exists(path) and os.stat(path).st_size > 0 and int(os.environ.get("OVERWRITE_EXISTING", 0)) == 0
