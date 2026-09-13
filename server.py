import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from config import get_google_api_key
from research_agents.student_agent import process_student_query
from research_agents.professor_agent import process_professor_query
from tools.load_data import ensure_chroma_loaded

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    ensure_chroma_loaded()
    yield

app = FastAPI(title="Vignan Research Matching Chatbot", lifespan=lifespan)

class QueryRequest(BaseModel):
    query: str

@app.post("/api/student")
def handle_student(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    return process_student_query(req.query.strip())

@app.post("/api/professor")
def handle_professor(req: QueryRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    response_text = process_professor_query(req.query.strip())
    return {"response": response_text}

@app.post("/api/reload")
def reload_data():
    from tools.retriever import reset_db_cache
    ensure_chroma_loaded(force=True)
    reset_db_cache()
    return {"status": "success", "message": "Vector database reloaded successfully"}

# Serve static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(static_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    print("\n=======================================================")
    print("  Starting Vignan Research Matching Chatbot Server")
    print("  Open in browser: http://localhost:8050")
    print("=======================================================\n")
    uvicorn.run("server:app", host="0.0.0.0", port=8050, reload=True)
