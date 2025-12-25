# 🚀 FastAPI Semantic Search - Complete!

## ✅ What's Been Created

I've built a complete **FastAPI semantic search endpoint** for your job recommendation system!

---

## 📁 Files Created

### **Permanent Service Files:**

1. **`backend/app/services/vector_search.py`**
   - **Type:** Permanent service module
   - **Purpose:** Core vector similarity search logic
   - **Functions:**
     - `search_similar_jobs()` - Semantic search
     - `find_similar_to_job()` - Job-to-job similarity
     - `get_job_by_id()` - Retrieve specific job
     - `cosine_similarity()` - Similarity calculation

2. **`backend/app/models/search.py`**
   - **Type:** Permanent data models
   - **Purpose:** Pydantic models for API validation
   - **Models:**
     - `SearchQuery` - Search request
     - `SearchResponse` - Search results
     - `JobResult` - Individual job result
     - `SimilarJobsQuery` - Similar jobs request

3. **`backend/app/routes/search.py`**
   - **Type:** Permanent API endpoints
   - **Purpose:** HTTP interface for search
   - **Endpoints:**
     - `POST /api/search/semantic` - Semantic search
     - `POST /api/search/similar` - Find similar jobs
     - `GET /api/search/job/{id}` - Get job details
     - `GET /api/search/stats` - Search statistics

4. **`backend/app/main.py`** (updated)
   - **Type:** Permanent application entry point
   - **Changes:** Added search router and CORS middleware

### **Testing/Utility Files:**

5. **`test_search_api.py`**
   - **Type:** One-time utility (for testing)
   - **Purpose:** Test all search endpoints
   - **Should be run:** After starting the API server

---

## 🎯 API Endpoints

### 1. **Semantic Search**
```http
POST /api/search/semantic
```

**Request:**
```json
{
  "query": "Python machine learning engineer",
  "limit": 10,
  "min_similarity": 0.5,
  "seniority": "Senior",  // optional
  "skills": ["Python", "TensorFlow"]  // optional
}
```

**Response:**
```json
{
  "query": "Python machine learning engineer",
  "results": [
    {
      "id": "test-12345",
      "company": "TechCorp AI",
      "position": "Senior Python Developer - Machine Learning",
      "location": "Remote (US)",
      "url": "https://...",
      "skills": ["python", "tensorflow", "pytorch", ...],
      "seniority": "Senior",
      "summary": "We are seeking...",
      "similarity": 0.8542
    }
  ],
  "count": 10,
  "processing_time_ms": 245.67
}
```

### 2. **Find Similar Jobs**
```http
POST /api/search/similar
```

**Request:**
```json
{
  "job_id": "test-12345",
  "limit": 5
}
```

**Response:**
```json
{
  "reference_job_id": "test-12345",
  "results": [...],
  "count": 5
}
```

### 3. **Get Job Details**
```http
GET /api/search/job/{job_id}
```

**Response:**
```json
{
  "id": "test-12345",
  "company": "TechCorp AI",
  "position": "Senior Python Developer",
  "description": "Full job description...",
  ...
}
```

### 4. **Search Statistics**
```http
GET /api/search/stats
```

**Response:**
```json
{
  "total_jobs": 116,
  "jobs_with_embeddings": 116,
  "embedding_dimension": 768,
  "seniority_distribution": {
    "Senior": 65,
    "Mid": 40,
    "Junior": 11
  },
  "unique_skills": 245,
  "top_skills": ["python", "javascript", ...]
}
```

---

## 🚀 How to Start the API

### **Step 1: Install Dependencies**
```bash
cd backend
pip install fastapi uvicorn numpy scikit-learn
```

### **Step 2: Start the Server**
```bash
# From the backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Or from project root:**
```bash
cd /Users/sawanttej/Desktop/W/backend
python -m uvicorn app.main:app --reload
```

### **Step 3: Verify It's Running**
```bash
curl http://localhost:8000/
```

**Expected:**
```json
{"status": "ok", "service": "Job Recommendation System"}
```

---

## 🧪 Testing the API

### **Option 1: Use the Test Script**
```bash
# Make sure API is running first!
python3 test_search_api.py
```

### **Option 2: Manual Testing with curl**

**Health Check:**
```bash
curl http://localhost:8000/
```

**Search Stats:**
```bash
curl http://localhost:8000/api/search/stats
```

**Semantic Search:**
```bash
curl -X POST http://localhost:8000/api/search/semantic \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python machine learning engineer",
    "limit": 5,
    "min_similarity": 0.5
  }'
```

### **Option 3: Interactive API Docs**

Open in browser:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🎯 How It Works

### **Semantic Search Flow:**

1. **User Query** → "Python machine learning engineer"
2. **Convert to Embedding** → Gemini API generates 768-dim vector
3. **Calculate Similarity** → Cosine similarity with all job embeddings
4. **Rank Results** → Sort by similarity score (0-1)
5. **Apply Filters** → Optional seniority/skills filtering
6. **Return Top N** → Most relevant jobs

### **Performance:**

- **Query embedding**: ~200-500ms (Gemini API call)
- **Similarity calculation**: ~50-100ms (116 jobs)
- **Total**: ~300-600ms per search

---

## 📊 Example Queries

### **General Search:**
```json
{"query": "software engineer", "limit": 10}
```

### **Specific Role:**
```json
{"query": "Senior DevOps with Kubernetes experience", "limit": 5}
```

### **With Filters:**
```json
{
  "query": "frontend developer",
  "limit": 10,
  "seniority": "Senior",
  "skills": ["React", "TypeScript"]
}
```

### **High Precision:**
```json
{
  "query": "machine learning researcher",
  "limit": 5,
  "min_similarity": 0.7
}
```

---

## 🔧 Configuration

### **Environment Variables:**

```bash
# PostgreSQL (for embeddings)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=jobs
POSTGRES_USER=user
POSTGRES_PASSWORD=pass

# Gemini API (for query embeddings)
GEMINI_API_KEY=your-api-key-here
```

### **API Settings:**

Edit `backend/app/core/config.py`:
```python
PROJECT_NAME = "Job Recommendation System"
HOST = "0.0.0.0"
PORT = 8000
```

---

## 🎨 Frontend Integration

### **React Example:**

```javascript
// Search for jobs
const searchJobs = async (query) => {
  const response = await fetch('http://localhost:8000/api/search/semantic', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      query: query,
      limit: 10,
      min_similarity: 0.5
    })
  });
  
  const data = await response.json();
  return data.results;
};

// Find similar jobs
const findSimilar = async (jobId) => {
  const response = await fetch('http://localhost:8000/api/search/similar', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      job_id: jobId,
      limit: 5
    })
  });
  
  const data = await response.json();
  return data.results;
};
```

---

## ✅ Next Steps

### **Immediate (Now):**

1. **Start the API server:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Test the endpoints:**
   ```bash
   python3 test_search_api.py
   ```

3. **Try the interactive docs:**
   - Open http://localhost:8000/docs

### **Future Enhancements:**

1. **Caching** - Cache query embeddings in Redis
2. **Pagination** - Add offset/limit for large result sets
3. **Faceted Search** - Add location, company filters
4. **Ranking** - Combine semantic + keyword search
5. **Analytics** - Track popular queries
6. **Rate Limiting** - Protect API from abuse

---

## 📚 Documentation

- **API Docs:** http://localhost:8000/docs (when running)
- **Code:** `backend/app/routes/search.py`
- **Models:** `backend/app/models/search.py`
- **Service:** `backend/app/services/vector_search.py`

---

## 🎉 Summary

**You now have:**
- ✅ 116 jobs with real 768-dim Gemini embeddings
- ✅ FastAPI semantic search endpoint
- ✅ Vector similarity search using cosine similarity
- ✅ Job-to-job similarity ("More like this")
- ✅ Filtering by seniority and skills
- ✅ Interactive API documentation
- ✅ Test scripts for verification

**Ready to use!** Start the server and try searching! 🚀
