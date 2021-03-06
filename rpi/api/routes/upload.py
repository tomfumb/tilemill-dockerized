import os
from time import time
from uuid import uuid4
from fastapi import UploadFile, File, WebSocket
from fastapi.routing import APIRouter
from starlette.websockets import WebSocketDisconnect

from api.settings import UPLOADS_DIR, UPLOADS_PATH


router = APIRouter()
PREFIX_SEPARATOR = "__;__"


ws_connections = list()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
            for connection in ws_connections:
                await connection.send_json({"added_at": round(time() * 1000)})
    except WebSocketDisconnect:
        ws_connections.remove(websocket)


@router.get("/list")
async def list_uploads():
    uploads = list()
    for filename in os.listdir(UPLOADS_DIR):
        if os.path.isfile(os.path.join(UPLOADS_DIR, filename)):
            filepath = os.path.join(UPLOADS_DIR, filename)
            fileinfo = os.stat(filepath)
            uploads.append(
                {
                    "filename": filename,
                    "path": f"{UPLOADS_PATH}/{filename}",
                    "bytes": fileinfo.st_size,
                    "uploaded": int(fileinfo.st_ctime * 1000),
                }
            )
    return {
        "prefix_separator": PREFIX_SEPARATOR,
        "files": uploads,
    }


@router.post("")
async def create_file(file: UploadFile = File(...)):
    unique_filename = os.path.join(
        UPLOADS_DIR,
        f"{str(uuid4()).replace('-', '')}{PREFIX_SEPARATOR}{file.filename}",
    )
    with open(unique_filename, "wb") as file_write:
        for chunk in iter(lambda: file.file.read(10000), b""):
            file_write.write(chunk)
    return {"saved_to": unique_filename}


@router.delete("/{filename}")
async def delete_file(filename: str):
    filepath = os.path.join(UPLOADS_DIR, filename)
    if os.path.exists(filepath):
        os.unlink(filepath)
