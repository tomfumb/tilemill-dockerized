import os

from gdal import ogr
from typing import Final, List

from provisioning.app.common.bbox import BBOX
from provisioning.app.sources.common.ogr_to_shp import ogr_to_shp
from provisioning.app.tilemill.ProjectLayerType import ProjectLayerType
from provisioning.app.util import delete_directory_contents, get_data_path, get_output_path

CACHE_DIR_NAME: Final = "shelters"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = ProjectLayerType.POINT

def provision(bbox: BBOX) -> List[str]:
    output_dir = get_output_path((CACHE_DIR_NAME,))
    os.makedirs(output_dir, exist_ok = True)
    delete_directory_contents(output_dir)
    driver = ogr.GetDriverByName("GPKG")
    datasource = driver.Open(get_data_path(("relevant-features.gpkg",)))
    result = ogr_to_shp(
        bbox,
        datasource.GetLayerByName("shelters"),
        get_output_path((CACHE_DIR_NAME, "shelters.shp")),
        "shelters",
        OUTPUT_CRS_CODE
    )
    datasource = None
    return result