import asyncio
import threading
import queue
import os
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import subprocess

import ogiya_pscube_scraping as scraper
import pscube_calculator as calc
import logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    poller = asyncio.create_task(queue_poller())
    yield
    # Shutdown
    poller.cancel()

app = FastAPI(lifespan=lifespan)

# Mount static files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Shared state
scraping_lock = asyncio.Lock()
is_scraping = False
result_queue = queue.Queue()
connected_websockets: List[WebSocket] = []

class RunRequest(BaseModel):
    models: Optional[List[str]] = None
    specific_machines: Optional[str] = None # comma separated string

def background_scraper_thread(models, specific_machines):
    global is_scraping
    
    # Setup custom logger
    handler = scraper.QueueHandler(result_queue)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    scraper.logger.addHandler(handler)
    
    try:
        if scraper.ensure_docker_desktop_running():
            if scraper.setup_docker_proxy():
                result_queue.put({"type": "log", "message": "スクレイピングを開始します...", "level": "INFO"})
                scraper.scrape_site1_scrapling(target_models=models, specific_machines=specific_machines, result_queue=result_queue)
                result_queue.put({"type": "log", "message": "スクレイピングが完了しました。", "level": "INFO"})
                result_queue.put({"type": "done"})
            else:
                result_queue.put({"type": "log", "message": "プロキシの準備ができなかったため、処理を中止します。", "level": "ERROR"})
                result_queue.put({"type": "done"})
        else:
            result_queue.put({"type": "log", "message": "Docker Desktopが起動できなかったため、処理を中止します。", "level": "ERROR"})
            result_queue.put({"type": "done"})
    except Exception as e:
        result_queue.put({"type": "log", "message": f"予期せぬエラーが発生しました: {e}", "level": "ERROR"})
        result_queue.put({"type": "done"})
    finally:
        scraper.logger.removeHandler(handler)
        result_queue.put({"type": "log", "message": "クリーンアップ処理を開始します...", "level": "INFO"})
        subprocess.run(["docker", "rm", "-f", scraper.CONTAINER_NAME], capture_output=True)
        scraper.stop_docker_desktop()
        is_scraping = False

async def queue_poller():
    while True:
        try:
            # Non-blocking get
            while True:
                msg = result_queue.get_nowait()
                # Broadcast to all connected websockets
                to_remove = []
                for ws in connected_websockets:
                    try:
                        await ws.send_json(msg)
                    except Exception:
                        to_remove.append(ws)
                for ws in to_remove:
                    connected_websockets.remove(ws)
        except queue.Empty:
            pass
        await asyncio.sleep(0.1)

@app.get("/")
async def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/api/models")
async def get_models():
    return list(calc.BORDER_DICT.keys())

@app.post("/api/run")
async def run_scraping(req: RunRequest):
    global is_scraping
    if is_scraping:
        return {"status": "error", "message": "既にスクレイピングが実行中です。"}
        
    async with scraping_lock:
        if is_scraping:
             return {"status": "error", "message": "既にスクレイピングが実行中です。"}
        is_scraping = True
    
    specific_machines_list = None
    if req.specific_machines:
        specific_machines_list = [m.strip() for m in req.specific_machines.split(",") if m.strip()]
        
    models = req.models if req.models else list(calc.BORDER_DICT.keys())
    
    # Start thread
    thread = threading.Thread(target=background_scraper_thread, args=(models, specific_machines_list))
    thread.start()
    
    return {"status": "success", "message": "スクレイピングをバックグラウンドで開始しました。"}

@app.get("/api/status")
async def get_status():
    global is_scraping
    
    # Try to load latest data
    data = {}
    try:
        if os.path.exists("scraping_data.pkl"):
            import pickle
            with open("scraping_data.pkl", "rb") as f:
                data = pickle.load(f)
    except:
        pass
        
    return {
        "is_scraping": is_scraping,
        "data": data
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
