# 🎉 Debug Consumer Setup Complete!

## ✅ What's Been Created

I've created a comprehensive debug script to help you verify the Gemini enrichment pipeline:

### 📁 Files Created

1. **`debug_consumer.py`** - Main debug script
   - Connects to Kafka `jobs_raw` topic
   - Consumes ONE message
   - Runs Gemini enrichment and embedding
   - Displays detailed results

2. **`run_debug.sh`** - Helper script
   - Checks for GEMINI_API_KEY
   - Provides helpful prompts
   - Runs the debug script

3. **`DEBUG_CONSUMER_GUIDE.md`** - Comprehensive guide
   - Detailed usage instructions
   - Expected output examples
   - Troubleshooting tips

4. **`RUN_DEBUG.md`** - Quick reference
   - Quick start commands
   - Current status
   - What to expect

## 🚀 Current Status

✅ **Docker services running:**
- Kafka & Zookeeper
- PostgreSQL
- Redis
- Kafka Producer (sent messages)
- Kafka Consumer (processing jobs)
- Backend API

✅ **Messages in Kafka:**
- Topic: `jobs_raw`
- Real job postings from RemoteOK
- Examples: "Software Engineer Infrastructure", "Staff DevOps Engineer", etc.

✅ **Dependencies installed:**
- `google-genai` package installed locally
- Ready for Gemini API calls

⚠️ **Need to set:**
- `GEMINI_API_KEY` environment variable (for real enrichment)

## 🎯 How to Use

### Option 1: Quick Run (Recommended)

```bash
# Set your API key
export GEMINI_API_KEY="your-api-key-here"

# Run the helper script
./run_debug.sh
```

### Option 2: Direct Run

```bash
# Set your API key
export GEMINI_API_KEY="your-api-key-here"

# Run directly
python3 debug_consumer.py
```

### Option 3: Test Without API Key

```bash
# Run with placeholder functions (no API key needed)
python3 debug_consumer.py
```

## 📊 What the Script Shows

When you run the debug script, you'll see:

### 1. **Raw Job Data**
```
📥 RAW MESSAGE RECEIVED
Job ID: 1129217
Company: xAI
Position: Software Engineer Infrastructure Supercomputing
Location: Remote
Description: [full job description]
```

### 2. **Gemini Enrichment Results**
```
🤖 RUNNING GEMINI ENRICHMENT
⏱️  Enrichment took 1.2 seconds

📊 EXTRACTED INFORMATION:
  Skills (12 found):
    1. Python
    2. Kubernetes
    3. Docker
    4. AWS
    5. Terraform
    ...

  Seniority Level: Senior

  Summary:
    We are seeking an experienced Software Engineer to build...
```

### 3. **Embedding Vector**
```
🧮 GENERATING EMBEDDING VECTOR
⏱️  Embedding generation took 0.8 seconds

📐 EMBEDDING VECTOR:
  Dimension: 768
  First 10 values: [0.023, -0.041, 0.015, ...]
  Min value: -0.234567
  Max value: 0.456789
  Mean value: 0.012345
```

### 4. **Performance Metrics**
```
📈 SUMMARY
✅ Successfully processed job: 1129217
✅ Extracted 12 skills
✅ Determined seniority: Senior
✅ Generated 768-dimensional embedding vector

⏱️  Total processing time: 2.1 seconds
   - Enrichment: 1.2s
   - Embedding: 0.8s
```

## 🔑 Getting a Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key
5. Export it: `export GEMINI_API_KEY="your-key"`

## 🔍 What This Verifies

Running this script will confirm:

✅ **Kafka Connection** - Can connect and consume messages
✅ **Gemini API** - Successfully calling Gemini for enrichment
✅ **Skills Extraction** - AI is extracting relevant technical skills
✅ **Seniority Detection** - AI is determining job level correctly
✅ **Summary Generation** - AI is creating concise summaries
✅ **Embedding Generation** - Creating 768-dimensional vectors
✅ **Performance** - See how long each operation takes

## 🎬 Next Steps

1. **Get your Gemini API key** from Google AI Studio
2. **Export it** in your terminal
3. **Run the debug script**: `./run_debug.sh`
4. **Review the output** to verify enrichment is working correctly
5. **Check the consumer logs** to see it processing jobs in real-time

## 📝 Notes

- The script **does not commit offsets**, so you can run it multiple times
- It processes **only ONE message** and then exits
- Works with or without Gemini API key (falls back to placeholders)
- The consumer container is already running with placeholder functions
- To enable Gemini in the container, add `GEMINI_API_KEY` to `.env` file

## 🐛 Troubleshooting

### "No messages received"
```bash
# Restart the producer to send more messages
docker compose restart kafka_producer
```

### "Connection refused"
```bash
# Check if Kafka is running
docker compose ps kafka
```

### "google-genai not found"
```bash
# Install the package
pip3 install google-genai
```

## 🎉 You're All Set!

Everything is ready to test the Gemini enrichment pipeline. Just set your API key and run the script!

```bash
export GEMINI_API_KEY="your-key-here"
./run_debug.sh
```

Enjoy seeing your job enrichment in action! 🚀
