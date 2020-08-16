import errno
import logging
import os
import re
import shutil
import sys

from gdal import ConfigurePythonLogging, UseExceptions
from typing import Final, Tuple

TILEMILL_DATA_LOCATION: Final = "/tiledata"

def get_base_path() -> str:
    return os.environ.get("DATA_LOCATION", TILEMILL_DATA_LOCATION)

def get_data_path(path_parts: Tuple[str] = None) -> str:
    return os.path.join(*(os.path.dirname(__file__), "..", "data", *(path_parts if path_parts else list())))

def get_local_features_path() -> str:
    return os.environ["LOCAL_FEATURES_LOCATION"]

def get_cache_path(path_parts: Tuple[str] = None) -> str:
    return os.path.join(*(get_base_path(), "cache", *(path_parts if path_parts else list())))

def get_run_data_path(run_id: str, path_parts: Tuple[str] = None) -> str:
    return os.path.join(*(get_base_path(), "run", run_id, *(path_parts if path_parts else list())))

def get_style_path(file_name: str) -> str:
    return os.path.join(*(os.path.dirname(__file__), "styles", file_name))

def get_export_path(path_parts: Tuple[str] = None) -> str:
    return os.path.join(*(get_base_path(), "export", *(path_parts if path_parts else list())))

def get_result_path(path_parts: Tuple[str] = None) -> str:
    return os.path.join(*(get_base_path(), "result", *(path_parts if path_parts else list())))

def delete_directory_contents(directory: str) -> str:
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
            raise e

# https://stackoverflow.com/a/10840586/519575
def silent_delete(path: str) -> None:
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occurred

# https://unix.stackexchange.com/a/510724/328901
def merge_dirs(source_root: str, dest_root: str) -> None:
    for path, dirs, files in os.walk(source_root, topdown=False):
        dest_dir = os.path.join(
            dest_root,
            os.path.relpath(path, source_root)
        )
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        for filename in files:
            os.replace(
                os.path.join(path, filename),
                os.path.join(dest_dir, filename)
            )
        for dirname in dirs:
            os.rmdir(os.path.join(path, dirname))
    shutil.rmtree(source_root)

def configure_logging():
    requestedLogLevel = os.environ.get("LOG_LEVEL", "info")
    logLevelMapping = {
        "debug": logging.DEBUG,
        "info":  logging.INFO,
        "warn":  logging.WARN,
        "error": logging.ERROR
    }
    handlers = [logging.StreamHandler(stream = sys.stdout),]
    logging.basicConfig(handlers = handlers, level = logLevelMapping.get(requestedLogLevel, logging.INFO), format = '%(levelname)s %(asctime)s %(message)s')

    ConfigurePythonLogging(logging.getLogger().name, logging.getLogger().level == logging.DEBUG)
    UseExceptions()

def swallow_unimportant_warp_error(ex: Exception) -> None:
    if re.match(r"Attempt to create 0x\d+ dataset is illegal\,sizes must be larger than zero", str(ex)):
        logging.debug(f"Bouding box intersects too few pixels to clip a new image")
    else:
        raise ex
