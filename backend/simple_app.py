from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List
import uuid

# Simple in-memory session storage
sessions: Dict[str, List] = {}

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    session_id: str = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    session_id: str

class ClearSessionRequest(BaseModel):
    session_id: str

class ClearSessionResponse(BaseModel):
    success: bool
    message: str

@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    session_id = request.session_id or str(uuid.uuid4())
    
    if session_id not in sessions:
        sessions[session_id] = []
    
    # Simple response for testing
    answer = f"Respuesta de prueba para: {request.query}"
    sessions[session_id].append({"role": "user", "content": request.query})
    sessions[session_id].append({"role": "assistant", "content": answer})
    
    return QueryResponse(
        answer=answer,
        sources=["Fuente de prueba"],
        session_id=session_id
    )

@app.post("/api/clear-session", response_model=ClearSessionResponse)
async def clear_session(request: ClearSessionRequest):
    if request.session_id in sessions:
        sessions[request.session_id] = []
    
    return ClearSessionResponse(
        success=True,
        message="Session cleared successfully"
    )

@app.get("/api/courses")
async def get_course_stats():
    return {
        "total_courses": 4,
        "course_titles": ["Curso 1", "Curso 2", "Curso 3", "Curso 4"]
    }

# Serve static files
app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")