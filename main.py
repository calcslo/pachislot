import asyncio
import threading
import queue
import os
import uvicorn
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager, contextmanager
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import subprocess
import ogiya_pscube_scraping as scraper
import cosmoobu_teramoba_scraping as cosmo_scraper
import pscube_calculator as calc
import logging

# Centralized logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT
)

LOG_DEDUP_WINDOW_SECONDS = 2.0
_log_dedup_lock = threading.Lock()
_last_log_messages = {}


@contextmanager
def queue_logging(target_logger, handler_cls, log_queue):
    """Temporarily route one module logger to one queue handler."""
    handler = handler_cls(log_queue)
    handler._pachislot_queue_handler = True
    handler.setFormatter(logging.Formatter(LOG_FORMAT))

    previous_handlers = [
        h for h in target_logger.handlers[:]
        if not getattr(h, "_pachislot_queue_handler", False)
        and not isinstance(h, handler_cls)
    ]
    previous_propagate = target_logger.propagate

    target_logger.handlers = [handler]
    target_logger.propagate = False
    try:
        yield
    finally:
        target_logger.handlers = previous_handlers
        target_logger.propagate = previous_propagate
        handler.close()


def should_drop_duplicate_log(stream_name: str, msg: dict) -> bool:
    if msg.get("type") != "log":
        return False

    signature = (msg.get("level"), msg.get("message"))
    now = time.monotonic()
    with _log_dedup_lock:
        last_signature, last_time = _last_log_messages.get(stream_name, (None, 0.0))
        if signature == last_signature and now - last_time < LOG_DEDUP_WINDOW_SECONDS:
            return True
        _last_log_messages[stream_name] = (signature, now)
    return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    poller = asyncio.create_task(queue_poller())
    poller_cosmo = asyncio.create_task(queue_poller_cosmo())
    yield
    # Shutdown
    poller.cancel()
    poller_cosmo.cancel()

app = FastAPI(lifespan=lifespan)

# Mount static files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Shared state for Ogiya Handa
scraping_lock = asyncio.Lock()
is_scraping = False
result_queue = queue.Queue()
connected_websockets = set()
stop_event = threading.Event()

# Shared state for Cosmo Obu
scraping_lock_cosmo = asyncio.Lock()
is_scraping_cosmo = False
result_queue_cosmo = queue.Queue()
connected_websockets_cosmo = set()
stop_event_cosmo = threading.Event()

# Docker proxy uses a fixed host port, so only one scraper can own it at a time.
docker_runtime_lock = threading.Lock()

class RunRequest(BaseModel):
    models: Optional[List[str]] = None
    specific_machines: Optional[str] = None # comma separated string

def background_scraper_thread(models, specific_machines, stop_event):
    global is_scraping
    try:
        with queue_logging(scraper.logger, scraper.QueueHandler, result_queue):
            try:
                with docker_runtime_lock:
                    if not scraper.ensure_docker_desktop_running():
                        result_queue.put({"type": "log", "message": "Docker Desktopが起動できなかったため、処理を中止します。", "level": "ERROR"})
                        return
                    if not scraper.setup_docker_proxy():
                        result_queue.put({"type": "log", "message": "プロキシの準備ができなかったため、処理を中止します。", "level": "ERROR"})
                        return

                    result_queue.put({"type": "log", "message": "スクレイピングを開始します...", "level": "INFO"})
                    scraper.scrape_site1_scrapling(target_models=models, specific_machines=specific_machines, result_queue=result_queue, stop_event=stop_event)
                    result_queue.put({"type": "log", "message": "スクレイピングが完了しました。", "level": "INFO"})
            except Exception as e:
                result_queue.put({"type": "log", "message": f"予期せぬエラーが発生しました: {e}", "level": "ERROR"})
            finally:
                result_queue.put({"type": "log", "message": "クリーンアップ処理を開始します...", "level": "INFO"})
                subprocess.run(["docker", "rm", "-f", scraper.CONTAINER_NAME], capture_output=True)
                scraper.stop_docker_desktop()
    except Exception as e:
        result_queue.put({"type": "log", "message": f"予期せぬエラーが発生しました: {e}", "level": "ERROR"})
    finally:
        is_scraping = False
        result_queue.put({"type": "done"})

async def queue_poller():
    while True:
        try:
            # Non-blocking get
            while True:
                msg = result_queue.get_nowait()
                if should_drop_duplicate_log("ogiya", msg):
                    continue
                # Broadcast to all connected websockets
                to_remove = []
                for ws in list(connected_websockets):
                    try:
                        # Try to send with a short timeout to detect dead connections
                        await asyncio.wait_for(ws.send_json(msg), timeout=1.0)
                    except Exception:
                        to_remove.append(ws)
                
                for ws in to_remove:
                    if ws in connected_websockets:
                        connected_websockets.remove(ws)
        except queue.Empty:
            pass
        await asyncio.sleep(0.1)

async def queue_poller_cosmo():
    while True:
        try:
            while True:
                msg = result_queue_cosmo.get_nowait()
                if should_drop_duplicate_log("cosmo", msg):
                    continue
                to_remove = []
                for ws in list(connected_websockets_cosmo):
                    try:
                        await asyncio.wait_for(ws.send_json(msg), timeout=1.0)
                    except Exception:
                        to_remove.append(ws)
                
                for ws in to_remove:
                    if ws in connected_websockets_cosmo:
                        connected_websockets_cosmo.remove(ws)
        except queue.Empty:
            pass
        await asyncio.sleep(0.1)

def background_scraper_thread_cosmo(models, specific_machines, stop_event):
    global is_scraping_cosmo
    try:
        with queue_logging(cosmo_scraper.logger, cosmo_scraper.QueueHandler, result_queue_cosmo):
            try:
                with docker_runtime_lock:
                    cosmo_scraper.run_cosmo_obu_scraping(
                        target_models=models,
                        specific_machines=specific_machines,
                        result_queue=result_queue_cosmo,
                        stop_desktop_when_done=False,
                        stop_event=stop_event,
                    )
            except Exception as e:
                result_queue_cosmo.put({"type": "log", "message": f"予期せぬエラーが発生しました: {e}", "level": "ERROR"})
    except Exception as e:
        result_queue_cosmo.put({"type": "log", "message": f"予期せぬエラーが発生しました: {e}", "level": "ERROR"})
    finally:
        is_scraping_cosmo = False
        result_queue_cosmo.put({"type": "done"})

@app.get("/")
async def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/api/models")
async def get_models():
    return list(calc.OGIYA_BORDER_DICT.keys())

@app.post("/api/run")
async def run_scraping(req: RunRequest):
    global is_scraping
    if is_scraping or is_scraping_cosmo or docker_runtime_lock.locked():
        return {"status": "error", "message": "既にスクレイピングが実行中です。"}
        
    async with scraping_lock:
        if is_scraping or is_scraping_cosmo or docker_runtime_lock.locked():
             return {"status": "error", "message": "既にスクレイピングが実行中です。"}
        is_scraping = True
    
    specific_machines_list = None
    if req.specific_machines:
        specific_machines_list = [m.strip() for m in req.specific_machines.split(",") if m.strip()]
        
    models = req.models if req.models else list(calc.OGIYA_BORDER_DICT.keys())
    
    # Start thread
    stop_event.clear()
    thread = threading.Thread(target=background_scraper_thread, args=(models, specific_machines_list, stop_event), daemon=True)
    thread.start()
    
    return {"status": "success", "message": "スクレイピングをバックグラウンドで開始しました。"}

@app.post("/api/stop")
async def stop_scraping():
    global is_scraping
    if not is_scraping:
        return {"status": "error", "message": "スクレイピングは実行中ではありません。"}
    stop_event.set()
    return {"status": "success", "message": "停止信号を送信しました。"}

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
    connected_websockets.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)
    finally:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)

@app.get("/cosmo_obu")
async def get_cosmo_obu_index():
    with open("static/cosmo_obu_index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.get("/api/cosmo_obu/models")
async def get_models_cosmo():
    return list(calc.COSMO_BORDER_DICT.keys())

@app.post("/api/cosmo_obu/run")
async def run_scraping_cosmo(req: RunRequest):
    global is_scraping_cosmo
    if is_scraping_cosmo or is_scraping or docker_runtime_lock.locked():
        return {"status": "error", "message": "既にスクレイピングが実行中です。"}
        
    async with scraping_lock_cosmo:
        if is_scraping_cosmo or is_scraping or docker_runtime_lock.locked():
             return {"status": "error", "message": "既にスクレイピングが実行中です。"}
        is_scraping_cosmo = True
    
    specific_machines_list = None
    if req.specific_machines:
        specific_machines_list = [m.strip() for m in req.specific_machines.split(",") if m.strip()]
        
    models = req.models if req.models else list(calc.COSMO_BORDER_DICT.keys())
    
    stop_event_cosmo.clear()
    thread = threading.Thread(target=background_scraper_thread_cosmo, args=(models, specific_machines_list, stop_event_cosmo), daemon=True)
    thread.start()
    
    return {"status": "success", "message": "スクレイピングをバックグラウンドで開始しました。"}

@app.post("/api/cosmo_obu/stop")
async def stop_scraping_cosmo():
    global is_scraping_cosmo
    if not is_scraping_cosmo:
        return {"status": "error", "message": "スクレイピングは実行中ではありません。"}
    stop_event_cosmo.set()
    return {"status": "success", "message": "停止信号を送信しました。"}

@app.get("/api/cosmo_obu/status")
async def get_status_cosmo():
    global is_scraping_cosmo
    
    data = {}
    try:
        if os.path.exists("scraping_data_cosmo_obu.pkl"):
            import pickle
            with open("scraping_data_cosmo_obu.pkl", "rb") as f:
                data = pickle.load(f)
    except:
        pass
        
    return {
        "is_scraping": is_scraping_cosmo,
        "data": data
    }

@app.websocket("/ws/cosmo_obu")
async def websocket_endpoint_cosmo(websocket: WebSocket):
    await websocket.accept()
    connected_websockets_cosmo.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in connected_websockets_cosmo:
            connected_websockets_cosmo.remove(websocket)
    finally:
        if websocket in connected_websockets_cosmo:
            connected_websockets_cosmo.remove(websocket)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
