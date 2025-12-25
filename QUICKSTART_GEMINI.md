# 🚀 Quick Start: Gemini API Integration

## ⚡ 3-Step Setup

### 1️⃣ Get API Key
Visit: https://aistudio.google.com/app/apikey

### 2️⃣ Configure
```bash
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

### 3️⃣ Deploy
```bash
docker-compose build kafka_consumer
docker-compose up -d kafka_consumer
```

## ✅ Verify It's Working

```bash
# Check logs for success message
docker-compose logs kafka_consumer | grep "Gemini"

# Should see:
# ✅ Gemini API client initialized successfully
```

## 🧪 Test Locally

```bash
export GEMINI_API_KEY="your_key"
python3 test_gemini.py
```

## 📊 Run Full Pipeline

```bash
# Fetch jobs
docker-compose up kafka_producer

# Watch enrichment with Gemini
docker-compose logs -f kafka_consumer
```

## 📚 Full Documentation

- **Setup Guide**: `GEMINI_INTEGRATION.md`
- **Implementation Details**: `IMPLEMENTATION_SUMMARY.md`
- **Test Script**: `test_gemini.py`
- **Project Overview**: `PROJECT_STATEMENT.md`

## 💡 Key Features

✅ **Gemini 2.0 Flash** - Intelligent job analysis  
✅ **Text-Embedding-004** - Semantic embeddings (768-dim)  
✅ **Graceful Fallback** - No pipeline disruption  
✅ **Cost Effective** - ~$0.20 per 1000 jobs  

## 🆘 Troubleshooting

**No API key?**
```bash
echo "GEMINI_API_KEY=your_key" >> .env
docker-compose restart kafka_consumer
```

**Module not found?**
```bash
docker-compose build kafka_consumer
```

**Want to test without Docker?**
```bash
pip install google-genai
export GEMINI_API_KEY="your_key"
python3 test_gemini.py
```

---

**Status**: ✅ Ready to use!  
**Version**: 2.0.0
