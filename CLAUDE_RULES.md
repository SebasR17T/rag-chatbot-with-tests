# Reglas y Estándares de Código - RAG Chatbot

## Convenciones de Nomenclatura

### Python (Backend)
```python
# ✅ Correcto - snake_case para variables y funciones
user_session_id = "12345"
def process_document(file_path: str) -> List[str]:
    pass

# ✅ Correcto - PascalCase para clases
class RAGSystem:
    pass

class DocumentProcessor:
    pass

# ✅ Correcto - UPPER_SNAKE_CASE para constantes
CHUNK_SIZE = 800
MAX_RESULTS = 5
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# ❌ Incorrecto
userSessionId = "12345"  # camelCase
def ProcessDocument():   # PascalCase para función
```

### JavaScript (Frontend)
```javascript
// ✅ Correcto - camelCase para variables y funciones
const currentSessionId = null;
let chatMessages = document.getElementById('chatMessages');

function sendMessage() {
    // implementación
}

function setupEventListeners() {
    // implementación  
}

// ✅ Correcto - PascalCase para clases/constructores
class ChatManager {
    constructor() {}
}

// ✅ Correcto - UPPER_SNAKE_CASE para constantes
const API_URL = '/api';
const MAX_MESSAGE_LENGTH = 1000;
```

### Archivos
```
# ✅ Correcto - snake_case para Python
rag_system.py
document_processor.py
vector_store.py
session_manager.py

# ✅ Correcto - kebab-case para frontend
index.html
chat-styles.css
api-client.js

# ✅ Correcto - descriptivos y específicos
search_tools.py
ai_generator.py
models.py
```

## Estructura de Código

### Organización de Imports (Python)
```python
# ✅ Correcto - orden de imports
# 1. Librería estándar
import os
from typing import List, Dict, Optional
from dataclasses import dataclass

# 2. Librerías de terceros
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import chromadb

# 3. Imports locales
from config import config
from models import Course, Lesson
from vector_store import VectorStore
```

### Organización de Clases (Python)
```python
class RAGSystem:
    """Main orchestrator for the Retrieval-Augmented Generation system"""
    
    def __init__(self, config):
        """Initialize RAG system with configuration"""
        self.config = config
        self._initialize_components()
    
    def _initialize_components(self):
        """Private method to setup system components"""
        # implementación
        
    def query(self, question: str, session_id: Optional[str] = None) -> Dict:
        """Public method to process user queries"""
        # implementación
        
    def get_stats(self) -> Dict:
        """Get system statistics"""
        # implementación
```

## Manejo de Errores

### Backend (Python)
```python
# ✅ Correcto - manejo específico de errores
try:
    result = self.vector_store.search(query)
    if not result:
        raise HTTPException(status_code=404, detail="No results found")
    return result
except chromadb.errors.ChromaError as e:
    print(f"ChromaDB error: {e}")
    raise HTTPException(status_code=500, detail="Database error")
except Exception as e:
    print(f"Unexpected error in search: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")

# ❌ Incorrecto - capturar todo sin especificar
try:
    result = self.vector_store.search(query)
except:
    pass  # Silenciar errores
```

### Frontend (JavaScript)
```javascript
// ✅ Correcto - manejo de errores async/await
async function sendMessage() {
    try {
        const response = await fetch(`${API_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: inputText, session_id: currentSessionId })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayResponse(data);
    } catch (error) {
        console.error('Error sending message:', error);
        displayError('Failed to send message. Please try again.');
    }
}
```

## Documentación y Comentarios

### Docstrings (Python)
```python
def process_document(self, file_path: str, chunk_size: int = 800) -> List[CourseChunk]:
    """
    Process a document into chunks for vector storage.
    
    Args:
        file_path: Path to the document to process
        chunk_size: Size of text chunks in characters
        
    Returns:
        List of CourseChunk objects ready for vector storage
        
    Raises:
        FileNotFoundError: If file_path does not exist
        ValueError: If chunk_size is invalid
    """
    # implementación
```

### Comentarios Inline
```python
# ✅ Correcto - comentarios explicativos
# Initialize embeddings model for semantic search
self.embedding_model = SentenceTransformer(config.EMBEDDING_MODEL)

# Create chunks with overlap to maintain context between segments  
chunks = []
for i in range(0, len(text), chunk_size - overlap):
    chunk = text[i:i + chunk_size]
    chunks.append(chunk)

# ❌ Incorrecto - comentarios obvios
x = 5  # Assign 5 to x
user_name = "john"  # Set user name to john
```

### JSDoc (JavaScript)
```javascript
/**
 * Send a message to the RAG system API
 * @param {string} message - User message to send
 * @param {string} sessionId - Current session identifier
 * @returns {Promise<Object>} API response with answer and sources
 */
async function sendMessage(message, sessionId) {
    // implementación
}
```

## Estándares de API

### Modelos Pydantic
```python
# ✅ Correcto - modelos bien documentados
class QueryRequest(BaseModel):
    """Request model for course queries"""
    query: str = Field(..., min_length=1, max_length=1000, description="User question")
    session_id: Optional[str] = Field(None, description="Session identifier for conversation history")

class QueryResponse(BaseModel):
    """Response model for course queries"""
    answer: str = Field(..., description="AI-generated answer")
    sources: List[str] = Field(..., description="Source documents used")
    session_id: str = Field(..., description="Session identifier")
    metadata: Optional[Dict] = Field(None, description="Additional response metadata")
```

### Endpoints FastAPI
```python
@app.post("/api/query", response_model=QueryResponse)
async def query_courses(request: QueryRequest):
    """
    Query course materials using RAG system.
    
    - **query**: User question about course content
    - **session_id**: Optional session ID for conversation history
    """
    try:
        result = rag_system.query(request.query, request.session_id)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Testing

### Unit Tests (Python)
```python
import pytest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_query_endpoint_success():
    """Test successful query to RAG system"""
    response = client.post(
        "/api/query",
        json={"query": "What is Python?"}
    )
    assert response.status_code == 200
    assert "answer" in response.json()
    assert "sources" in response.json()

def test_query_endpoint_invalid_input():
    """Test query endpoint with invalid input"""
    response = client.post(
        "/api/query", 
        json={"query": ""}  # Empty query should fail
    )
    assert response.status_code == 422
```

## Configuración y Variables de Entorno

### Variables de Entorno
```python
# ✅ Correcto - valores por defecto seguros
@dataclass  
class Config:
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "deepseek")  
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
    MAX_RESULTS: int = int(os.getenv("MAX_RESULTS", "5"))
    
    def __post_init__(self):
        if not self.ANTHROPIC_API_KEY and self.AI_PROVIDER == "anthropic":
            raise ValueError("ANTHROPIC_API_KEY required when using anthropic provider")
```

## Seguridad

### Manejo de API Keys
```python
# ✅ Correcto - no logear secrets
def initialize_ai_client(api_key: str):
    if not api_key:
        raise ValueError("API key is required")
    
    # Log sin exponer la key
    print("Initializing AI client...")
    return Client(api_key=api_key)

# ❌ Incorrecto - exponer secrets en logs
def initialize_ai_client(api_key: str):
    print(f"Using API key: {api_key}")  # NUNCA hacer esto
```

### Validación de Input
```python  
# ✅ Correcto - validar y sanitizar input
def query(self, question: str, session_id: Optional[str] = None) -> Dict:
    if not question or len(question.strip()) == 0:
        raise ValueError("Query cannot be empty")
    
    if len(question) > 1000:
        raise ValueError("Query too long (max 1000 characters)")
    
    # Sanitizar query
    clean_query = question.strip()[:1000]
    
    # procesar query limpio
    return self._process_query(clean_query, session_id)
```

## Performance

### Chunking Eficiente
```python
# ✅ Correcto - chunking optimizado
def create_chunks(self, text: str, chunk_size: int, overlap: int) -> List[str]:
    """Create overlapping text chunks efficiently"""
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        chunks.append(chunk)
        
        if end >= len(text):
            break
            
        start += chunk_size - overlap
    
    return chunks
```

### Caching de Embeddings
```python
# ✅ Correcto - cache de embeddings costosos
def get_embedding(self, text: str) -> List[float]:
    """Get embedding with caching"""
    text_hash = hash(text)
    
    if text_hash in self._embedding_cache:
        return self._embedding_cache[text_hash]
    
    embedding = self.model.encode([text])[0].tolist()
    self._embedding_cache[text_hash] = embedding
    
    return embedding
```