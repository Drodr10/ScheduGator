# ScheduGator Backend API

Flask REST API connecting the React frontend to Python backend (Gemma 3 + Solver).

## Quick Start

### 1. Activate virtual environment and start server:
```bash
# Windows PowerShell
.\.venv\Scripts\python.exe backend\api.py

# Or if venv is activated
python backend/api.py
```

Server runs on: `http://localhost:5000`

### 2. Test the API:
```bash
# Health check
curl http://localhost:5000/api/health

# Search courses
curl -X POST http://localhost:5000/api/search -H "Content-Type: application/json" -d "{\"query\":\"COP\",\"req_limit\":5}"
```

## API Endpoints

### `GET /api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "brain": "ready",
    "solver": "ready",
    "catalog_size": 6119
  }
}
```

---

### `POST /api/chat`
Send a message to Gemma 3 AI brain for conversational assistance.

**Request:**
```json
{
  "message": "Show me CS tracking courses"
}
```

**Response:**
```json
{
  "response": "Here are the CS tracking courses...",
  "status": "success"
}
```

---

### `POST /api/search`
Search for courses with filters.

**Request:**
```json
{
  "query": "COP",
  "dept": "Computer Science",
  "min_level": 3000,
  "max_level": 4000,
  "req_limit": 15
}
```

**Response:**
```json
{
  "results": [...],
  "count": 12,
  "status": "success"
}
```

---

### `POST /api/generate-schedule`
Generate a conflict-free schedule using the backtracking solver.

**Request:**
```json
{
  "courses": ["COP 3502", "MAC 2312", "PHY 2048"],
  "major_code": "CPS"
}
```

**Response:**
```json
{
  "success": true,
  "schedule": [...],
  "courses_scheduled": 3,
  "status": "success"
}
```

---

### `GET /api/majors`
Get list of all available majors.

**Response:**
```json
{
  "majors": [
    {
      "major_code": "CPS",
      "college": "Engineering",
      "total_credits": 120
    }
  ],
  "count": 5,
  "status": "success"
}
```

---

### `GET /api/major/<major_code>`
Get detailed requirements for a specific major.

**Example:** `GET /api/major/CPS`

**Response:**
```json
{
  "major": {
    "major_code": "CPS",
    "college": "Engineering",
    "total_credits": 120,
    "gpa_gate": {...},
    "technical_electives": {...}
  },
  "status": "success"
}
```

## Architecture

```
Frontend (React) 
    ↓ HTTP
API Server (Flask)
    ↓
┌─────────────────┬──────────────┐
│   Gemma 3 Brain │    Solver    │
│  (Function Call)│ (Backtrack)  │
└─────────────────┴──────────────┘
         ↓                ↓
    search.py      conflicts.py
         ↓                ↓
    universal_base_catalog.json (6,119 courses)
```

## Development

Run tests:
```bash
python backend/test_api.py
```

Enable debug mode (auto-reload on file changes):
```python
# Already enabled in api.py
app.run(debug=True)
```
