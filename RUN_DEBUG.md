# Running the Debug Consumer Script

## ✅ Setup Complete!

All services are running and the `google-genai` package is installed.

## 🔑 Set Your Gemini API Key

Before running the debug script with real Gemini enrichment, you need to set your API key:

```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
```

**To get a Gemini API key:**
1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Create a new API key
3. Copy it and export it in your terminal

## 🚀 Run the Debug Script

Once you've set the API key, run:

```bash
python3 debug_consumer.py
```

## 📊 What You'll See

The script will:
1. ✅ Connect to Kafka at `localhost:29092`
2. ✅ Consume ONE message from `jobs_raw` topic
3. ✅ Run Gemini enrichment to extract:
   - **Skills** (e.g., Python, AWS, Docker, Kubernetes)
   - **Seniority** (Junior/Mid/Senior/Lead)
   - **Summary** (2-sentence AI-generated description)
4. ✅ Generate **768-dimensional embedding vector** using Gemini
5. ✅ Display detailed statistics and timing information

## 🎯 Expected Output (with Gemini API)

```
================================================================================
  🔍 GEMINI ENRICHMENT DEBUG SCRIPT
================================================================================

✅ GEMINI_API_KEY is set (length: 39)
✅ Connected to Kafka at localhost:29092

📥 RAW MESSAGE RECEIVED
Job ID: 1129216
Position: Staff DevOps Engineer
Company: Heartflow

🤖 RUNNING GEMINI ENRICHMENT
⏱️  Enrichment took 1.2 seconds

📊 EXTRACTED INFORMATION:
  Skills (12 found):
    1. DevOps
    2. Kubernetes
    3. Docker
    4. AWS
    5. Python
    ...

  Seniority Level: Senior

  Summary:
    We are seeking an experienced Staff DevOps Engineer...

🧮 GENERATING EMBEDDING VECTOR
⏱️  Embedding generation took 0.8 seconds

📐 EMBEDDING VECTOR:
  Dimension: 768
  First 10 values: [0.023, -0.041, 0.015, ...]
  Min value: -0.234567
  Max value: 0.456789
  Mean value: 0.012345
```

## 🔄 Running Without API Key

If you run without setting `GEMINI_API_KEY`, the script will still work but use **placeholder functions**:
- Skills: Simple keyword matching
- Seniority: Keyword-based detection
- Summary: First 2 sentences
- Embedding: Hash-based pseudo-vector

## 📝 Current Status

✅ Docker services running
✅ Kafka has messages in `jobs_raw` topic  
✅ `google-genai` package installed
⚠️  Need to set `GEMINI_API_KEY` for real enrichment

## 🎬 Quick Start

```bash
# Set your API key
export GEMINI_API_KEY="your-key-here"

# Run the debug script
python3 debug_consumer.py
```

That's it! The script will show you exactly what Gemini is extracting from your job postings.
