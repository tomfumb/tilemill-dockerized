import re
import os
import logging
import zipfile

from gdal import ogr, DEMProcessing, Warp
from typing import Final, List

from app.common.bbox import BBOX
from app.common.file import skip_file_creation, remove_intermediaries
from app.common.get_datasource_from_bbox import get_datasource_from_bbox, BBOX_LAYER_NAME
from app.common.httpRetriever import httpRetriever, RetrievalRequest
from app.tilemill.ProjectLayerType import ProjectLayerType
from app.util import get_data_path, get_cache_path, get_run_data_path, swallow_unimportant_warp_error

CACHE_DIR_NAME: Final = "bc-hillshade"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = ProjectLayerType.RASTER

class GenerationRequest(RetrievalRequest):
    dem_path: str
    prj_path: str
    hs_path: str
    run_path: str

def provision(bbox: BBOX, run_id: str) -> List[str]:
    run_directory = get_run_data_path(run_id, (CACHE_DIR_NAME,))
    os.makedirs(run_directory)
    driver = ogr.GetDriverByName("GPKG")
    grid_datasource = (driver.Open(get_data_path(("grids.gpkg",))))
    grid_layer = grid_datasource.GetLayerByName("Canada-50000")
    grid_layer.SetSpatialFilterRect(bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y)
    bbox_cells = list()
    while grid_cell := grid_layer.GetNextFeature():
        cell_name = grid_cell.GetFieldAsString("NTS_SNRC")
        cell_parent = re.sub("^0", "", re.search("^\d{2,3}[a-z]", cell_name, re.IGNORECASE)[0])
        for cardinal in ("e", "w"):
            cell_part_name = f"{cell_name.lower()}_{cardinal}"
            zip_file_name = f"{cell_part_name}.dem.zip"
            bbox_cells.append(GenerationRequest(
                url=f"https://pub.data.gov.bc.ca/datasets/175624/{cell_parent.lower()}/{zip_file_name}",
                path=get_cache_path((CACHE_DIR_NAME, zip_file_name)),
                expected_type="application/zip",
                dem_path = get_cache_path((CACHE_DIR_NAME, f"{cell_part_name}.dem")),
                prj_path = get_cache_path((CACHE_DIR_NAME, f"{cell_part_name}_prj.tif")),
                hs_path = get_cache_path((CACHE_DIR_NAME, f"{cell_part_name}_hs.tif")),
                run_path = get_run_data_path(run_id, (CACHE_DIR_NAME, f"{cell_part_name}.tif"))
            ))

    to_generate = list(filter(lambda generation_request: not skip_file_creation(generation_request.hs_path), bbox_cells))
    httpRetriever(to_generate)

    for generation_request in to_generate:
        with zipfile.ZipFile(generation_request.path, "r") as zip_ref:
            zip_ref.extractall(get_cache_path((CACHE_DIR_NAME,)))
        Warp(generation_request.prj_path, generation_request.dem_path, srcSRS="EPSG:4269", dstSRS=OUTPUT_CRS_CODE, resampleAlg="cubic")
        DEMProcessing(generation_request.hs_path, generation_request.prj_path, "hillshade", format="GTiff", band=1, azimuth=225, altitude=45, scale=1, zFactor=1)
        if remove_intermediaries():
            os.remove(generation_request.path)
            os.remove(generation_request.dem_path)
            os.remove(generation_request.prj_path)

    for generation_request in bbox_cells:
        try:
            Warp(generation_request.run_path, generation_request.hs_path, cutlineDSName=get_datasource_from_bbox(bbox, get_run_data_path(run_id, None)), cutlineLayer=BBOX_LAYER_NAME, cropToCutline=True, dstNodata=-1)
        except Exception as ex:
            swallow_unimportant_warp_error(ex)

    return list(map(lambda generation_request: generation_request.run_path, bbox_cells))

def _get_final_cache_path(cell_name: str) -> str:
    return get_cache_path((CACHE_DIR_NAME, f"{cell_name}_hs.tif"))