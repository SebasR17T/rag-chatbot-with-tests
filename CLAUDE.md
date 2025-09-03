# Course Materials RAG System - Claude Configuration

## Project Overview
Sistema de Recuperación Aumentada (RAG) para responder preguntas sobre materiales de curso usando búsqueda semántica e IA.

**Stack Tecnológico:**
- **Backend**: FastAPI + Python 3.13
- **Frontend**: Vanilla JavaScript + HTML/CSS  
- **Vector DB**: ChromaDB
- **AI Providers**: Anthropic Claude / DeepSeek
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)

## Estructura del Proyecto
```
starting-ragchatbot-codebase/
├── CLAUDE.md              # Esta configuración
├── CLAUDE_RULES.md        # Reglas de código
├── CLAUDE_DOCS.md         # Documentación técnica
├── backend/
│   ├── app.py             # FastAPI application
│   ├── config.py          # Configuraciones
│   ├── rag_system.py      # Sistema RAG principal
│   ├── vector_store.py    # Gestión ChromaDB
│   ├── ai_generator.py    # Generación AI (Claude/DeepSeek)
│   ├── document_processor.py # Procesamiento documentos
│   ├── session_manager.py # Gestión sesiones
│   ├── search_tools.py    # Herramientas búsqueda
│   ├── models.py          # Modelos Pydantic
│   └── simple_app.py      # App simplificada
├── frontend/
│   ├── index.html         # Interfaz web principal
│   └── script.js          # JavaScript frontend
├── docs/                  # Documentación adicional
├── .env                   # Variables de entorno
├── pyproject.toml         # Dependencias Python
└── run.sh                 # Script de ejecución
```

## Comandos Principales

### Setup del Entorno
```bash
# Instalar UV (gestor de paquetes Python)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instalar dependencias
uv sync

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys
```

### Variables de Entorno Requeridas
```env
# API Keys (usar uno de los dos)
ANTHROPIC_API_KEY=tu_clave_anthropic
DEEPSEEK_API_KEY=tu_clave_deepseek

# Proveedor AI: "anthropic" o "deepseek"  
AI_PROVIDER=deepseek
```

### Ejecución de la Aplicación
```bash
# Inicio rápido
chmod +x run.sh
./run.sh

# Inicio manual
cd backend
uv run uvicorn app:app --reload --port 8000

# Aplicación simplificada
uv run python simple_app.py
```

### Acceso a la Aplicación
- **Interfaz Web**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **API Base**: http://localhost:8000/api

## Funcionalidades Principales

### API Endpoints
```bash
# Consultar curso
POST /api/query
{
  "query": "¿Qué es Python?",
  "session_id": "optional_session_id"
}

# Estadísticas cursos
GET /api/courses/stats

# Cargar documentos
POST /api/upload

# Limpiar conversación  
POST /api/clear/{session_id}
```

### Componentes del Sistema RAG

1. **Document Processor**: Chunking de documentos (800 chars, 100 overlap)
2. **Vector Store**: Almacenamiento y búsqueda semántica en ChromaDB  
3. **AI Generator**: Generación de respuestas con Claude/DeepSeek
4. **Session Manager**: Gestión de conversaciones con historial
5. **Search Tools**: Herramientas especializadas de búsqueda

### Frontend Features
- Chat interface con historial
- Visualización de fuentes
- Estadísticas de cursos disponibles
- Sesiones de conversación persistentes

## Testing y Desarrollo

### Tests Manuales
```bash
# Test API endpoints
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test question"}'

# Test estadísticas
curl http://localhost:8000/api/courses/stats
```

### Debugging
```bash
# Logs detallados
uv run uvicorn app:app --log-level debug

# Verificar ChromaDB
ls -la chroma_db/

# Test embeddings
uv run python -c "from sentence_transformers import SentenceTransformer; print('Model OK')"
```

## Configuraciones Importantes

### Modelo de Embeddings
- Por defecto: `all-MiniLM-L6-v2` (384 dimensiones)
- Cambiar en `config.py` si es necesario

### Parámetros RAG
- Chunk size: 800 caracteres
- Chunk overlap: 100 caracteres  
- Max resultados: 5
- Max historial: 2 mensajes

### Modelos AI
- **Anthropic**: `claude-sonnet-4-20250514`
- **DeepSeek**: `deepseek-chat`

## Troubleshooting Común

### Errores de Dependencias
```bash
# Reinstalar dependencias
uv sync --reinstall

# Verificar Python version
python --version  # Debe ser >=3.13
```

### Problemas con ChromaDB
```bash
# Limpiar base vectorial
rm -rf chroma_db/
# Reiniciar aplicación para recrear
```

### CORS Issues
- Frontend debe servirse desde mismo puerto que backend
- Configuración CORS en `app.py` permite todos los orígenes

## Próximos Pasos de Desarrollo
- Implementar autenticación de usuarios
- Añadir más formatos de documentos
- Mejorar interfaz de usuario
- Implementar tests automatizados
- Optimizar búsqueda semántica