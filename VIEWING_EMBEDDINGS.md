# 📍 Where to View Your Embeddings

## Overview

Your job embeddings are stored in **PostgreSQL** and can be accessed in multiple ways. This guide shows you all the options.

---

## 🗄️ **1. PostgreSQL Database (Primary Storage)**

### Connection Details:
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `jobs`
- **Username**: `user`
- **Password**: `pass`
- **Table**: `jobs_enriched`
- **Column**: `embedding` (stored as JSON text)

### Direct SQL Query:

```bash
# Connect to PostgreSQL
psql -h localhost -U user -d jobs

# View embeddings
SELECT id, position, company, 
       jsonb_array_length(embedding::jsonb) as embedding_dim,
       created_at 
FROM jobs_enriched 
ORDER BY created_at DESC;

# Get a specific embedding
SELECT id, position, embedding 
FROM jobs_enriched 
WHERE id = 'test-12345';
```

### Using Python:

```python
import psycopg2
import json

conn = psycopg2.connect(
    host='localhost',
    database='jobs',
    user='user',
    password='pass',
    port='5432'
)

cursor = conn.cursor()
cursor.execute("SELECT id, position, embedding FROM jobs_enriched")

for row in cursor.fetchall():
    job_id, position, embedding_json = row
    embedding = json.loads(embedding_json)
    print(f"{position}: {len(embedding)} dimensions")
    print(f"First 5 values: {embedding[:5]}")
```

---

## 🔍 **2. Interactive Embedding Viewer (Recommended)**

We've created a custom viewer script that shows embeddings with statistics and similarities:

```bash
python3 view_embeddings.py
```

**Features:**
- ✅ Lists all embeddings with metadata
- ✅ Shows embedding statistics (mean, std dev, min, max)
- ✅ Calculates similarity between jobs
- ✅ Identifies real vs placeholder embeddings
- ✅ Displays first 10 values of each embedding

**Example Output:**
```
1. Senior Python Developer - Machine Learning at TechCorp AI
   Job ID: test-12345
   Seniority: Senior
   Embedding dimension: 768
   Type: ✅ Real Gemini
   First 10 values: [0.029, -0.018, 0.007, -0.036, 0.019, ...]
   Statistics:
      Mean: 0.000123
      Std Dev: 0.045678
      Min: -0.234567
      Max: 0.456789
```

---

## 💾 **3. Export Embeddings**

### Export to JSON:
```bash
python3 export_embeddings.py --format json
# Creates: embeddings.json
```

### Export to NumPy (for ML/analysis):
```bash
python3 export_embeddings.py --format numpy
# Creates: embeddings.npz

# Load in Python:
import numpy as np
data = np.load('embeddings.npz')
embeddings = data['embeddings']  # Shape: (n_jobs, 768)
ids = data['ids']
positions = data['positions']
```

### Export to CSV:
```bash
python3 export_embeddings.py --format csv
# Creates: embeddings.csv (metadata)
#          embeddings_vectors.csv (768-dim vectors)
```

### Export All Formats:
```bash
python3 export_embeddings.py --format all
```

---

## 🔧 **4. Using Database Tools**

### pgAdmin (GUI):
1. Download [pgAdmin](https://www.pgadmin.org/)
2. Connect to `localhost:5432`
3. Navigate to: `jobs` → `Schemas` → `public` → `Tables` → `jobs_enriched`
4. Right-click → View/Edit Data

### DBeaver (GUI):
1. Download [DBeaver](https://dbeaver.io/)
2. Create PostgreSQL connection to `localhost:5432`
3. Browse to `jobs_enriched` table
4. View `embedding` column

### TablePlus (GUI - Mac):
1. Download [TablePlus](https://tableplus.com/)
2. Connect to PostgreSQL at `localhost:5432`
3. Browse `jobs_enriched` table

---

## 🐳 **5. Docker Container Access**

### Access PostgreSQL from Docker:
```bash
# Enter PostgreSQL container
docker compose exec postgres psql -U user -d jobs

# Query embeddings
SELECT id, position, 
       length(embedding) as embedding_size,
       created_at 
FROM jobs_enriched 
ORDER BY created_at DESC 
LIMIT 5;
```

---

## 📊 **6. Verification Script**

Use the verification script we created earlier:

```bash
python3 verify_thinking.py
```

This shows:
- Position
- Gemini-generated summary
- First 5 embedding values
- Embedding dimension and type

---

## 🔗 **7. Redis Cache (Temporary)**

Recent jobs are also cached in Redis:

```bash
# Connect to Redis
docker compose exec redis redis-cli

# List all keys
KEYS *

# Get a cached job
GET job:test-12345
```

---

## 📈 **8. Programmatic Access**

### Using the existing modules:

```python
# Import the database module
import sys
sys.path.append('/Users/sawanttej/Desktop/W')

from services.db.postgres import get_all_jobs

# Get all jobs with embeddings
jobs = get_all_jobs(limit=10)

for job in jobs:
    print(f"{job['position']}: {len(job.get('embedding', []))} dimensions")
```

---

## 🎯 **Quick Reference**

| Method | Command | Best For |
|--------|---------|----------|
| **Interactive Viewer** | `python3 view_embeddings.py` | Exploring & analyzing |
| **Verification** | `python3 verify_thinking.py` | Quick check (latest 3) |
| **Export JSON** | `python3 export_embeddings.py --format json` | Backup & sharing |
| **Export NumPy** | `python3 export_embeddings.py --format numpy` | ML/analysis |
| **SQL Query** | `psql -h localhost -U user -d jobs` | Direct database access |
| **Docker** | `docker compose exec postgres psql -U user -d jobs` | Container access |

---

## 🚀 **Next Steps**

### Analyze Embeddings:
```python
import numpy as np

# Load embeddings
data = np.load('embeddings.npz')
embeddings = data['embeddings']

# Calculate similarity matrix
from sklearn.metrics.pairwise import cosine_similarity
similarity_matrix = cosine_similarity(embeddings)

# Find most similar jobs
most_similar = np.argsort(similarity_matrix[0])[::-1][1:6]
print("Top 5 similar jobs:", data['positions'][most_similar])
```

### Visualize Embeddings:
```python
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

# Reduce to 2D
pca = PCA(n_components=2)
embeddings_2d = pca.fit_transform(embeddings)

# Plot
plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1])
plt.title('Job Embeddings (2D PCA)')
plt.show()
```

---

## 📝 **Summary**

Your embeddings are:
- ✅ Stored in PostgreSQL (`jobs_enriched.embedding`)
- ✅ Accessible via Python scripts
- ✅ Exportable to JSON, NumPy, CSV
- ✅ Viewable with database tools
- ✅ Cached temporarily in Redis

**Recommended workflow:**
1. Use `view_embeddings.py` to explore
2. Use `export_embeddings.py` to export for analysis
3. Use SQL for custom queries
4. Use `verify_thinking.py` for quick checks
