# 🔄 Backfill Enrichment Guide

## Overview

The `backfill_enrichment.py` script re-enriches all jobs with placeholder embeddings using the Gemini API. This will convert your 116 placeholder embeddings into real 768-dimensional Gemini embeddings.

---

## 🚀 Quick Start

### 1. Dry Run (Recommended First)

See what will be processed without making changes:

```bash
export GEMINI_API_KEY="your-api-key-here"
python3 backfill_enrichment.py --dry-run
```

### 2. Run the Backfill

Process all placeholder jobs:

```bash
export GEMINI_API_KEY="your-api-key-here"
python3 backfill_enrichment.py
```

**You'll be asked to confirm before processing starts.**

---

## ⚙️ Options

### Basic Usage:
```bash
python3 backfill_enrichment.py
```

### Custom Batch Size:
```bash
# Show progress every 5 jobs instead of 10
python3 backfill_enrichment.py --batch-size 5
```

### Custom Delay (Rate Limiting):
```bash
# Wait 3 seconds between jobs instead of 2
python3 backfill_enrichment.py --delay 3.0
```

### Combined Options:
```bash
python3 backfill_enrichment.py --batch-size 5 --delay 3.0
```

---

## 📊 What It Does

1. **Identifies Placeholder Embeddings**
   - Checks for 384-dimensional embeddings (not 768)
   - Detects sequential values (0.414, 0.415, 0.416...)

2. **Re-enriches Each Job**
   - Calls Gemini API to extract skills, seniority, summary
   - Generates 768-dimensional embedding vector
   - Updates database with real data

3. **Shows Progress**
   - Real-time progress updates
   - Success/failure counts
   - Time estimates
   - Rate limiting to avoid API quotas

---

## ⏱️ Estimated Time

For **116 jobs** with 2-second delay:
- **Total time**: ~4-5 minutes
- **API calls**: 232 (116 enrichment + 116 embedding)

You can adjust the delay with `--delay` option:
- `--delay 1.0` → ~2 minutes (faster, higher rate limit risk)
- `--delay 3.0` → ~6 minutes (safer, lower rate limit risk)

---

## 📋 Example Output

```
================================================================================
  🔄 GEMINI ENRICHMENT BACKFILL
================================================================================

✅ GEMINI_API_KEY is set (length: 39)
📊 Batch size: 10
⏱️  Delay between jobs: 2.0s

🔍 Identifying jobs with placeholder embeddings...

📋 Found 116 jobs with placeholder embeddings

⚠️  This will re-enrich 116 jobs using Gemini API.
   Estimated time: ~3.9 minutes
   API calls: 232 (enrichment + embedding)

Continue? (yes/no): yes

================================================================================
  🚀 STARTING BACKFILL
================================================================================

[1/116] Processing: Partnership Head at HR Force International
   Job ID: 1129214
   🤖 Calling Gemini for enrichment...
   🧮 Generating embedding...
   💾 Updating database...
   ✅ Success!
      Skills: 10 found
      Seniority: Senior
      Embedding: 768 dimensions

[2/116] Processing: Digital Marketing Manager at mindmoneyreset
   Job ID: 1129215
   🤖 Calling Gemini for enrichment...
   🧮 Generating embedding...
   💾 Updating database...
   ✅ Success!
      Skills: 8 found
      Seniority: Mid
      Embedding: 768 dimensions

...

   📊 Progress: 10/116 (8.6%)
   ⏱️  Elapsed: 0.5m | Remaining: ~5.3m
   ✅ Successful: 10 | ❌ Failed: 0 | ⚠️  Skipped: 0

...

================================================================================
  📊 BACKFILL COMPLETE
================================================================================

✅ Successfully enriched: 116/116
❌ Failed: 0/116
⚠️  Skipped (no description): 0/116
⏱️  Total time: 3.9 minutes
⚡ Average rate: 29.7 jobs/minute

🎉 116 jobs now have real Gemini embeddings!

Verify results:
   python3 verify_thinking.py
   python3 view_embeddings.py
```

---

## 🛡️ Safety Features

### 1. **Confirmation Prompt**
You must confirm before processing starts.

### 2. **Rate Limiting**
Built-in delay between API calls to avoid quota issues.

### 3. **Error Handling**
Continues processing even if individual jobs fail.

### 4. **Progress Tracking**
Shows real-time progress and estimates.

### 5. **Interrupt Support**
Press `Ctrl+C` to stop gracefully and see progress.

---

## ⚠️ Important Notes

### API Rate Limits

Gemini API has rate limits:
- **Free tier**: 15 requests/minute
- **Paid tier**: Higher limits

**Recommendation**: Use `--delay 4.0` for free tier to stay under limits.

### Cost Considerations

- **Free tier**: Limited requests per day
- **Paid tier**: Check [Google AI pricing](https://ai.google.dev/pricing)

### Database Updates

- Jobs are updated in-place
- Original data is preserved (company, position, description, etc.)
- Only enrichment fields are updated (skills, seniority, summary, embedding)

---

## 🔍 Verification

After backfill completes, verify the results:

### 1. Quick Check (Latest 3 Jobs)
```bash
python3 verify_thinking.py
```

### 2. View All Embeddings
```bash
python3 view_embeddings.py
```

### 3. Check Statistics
```bash
python3 view_embeddings.py | grep "768-dim embeddings"
```

Should show: `Jobs with 768-dim embeddings: 117` (all jobs!)

---

## 🐛 Troubleshooting

### "GEMINI_API_KEY is not set"
```bash
export GEMINI_API_KEY="your-api-key-here"
```

### "Rate limit exceeded"
Increase delay:
```bash
python3 backfill_enrichment.py --delay 5.0
```

### "No module named 'google'"
Install dependencies:
```bash
pip3 install google-genai psycopg2-binary
```

### "Connection refused" (PostgreSQL)
Make sure PostgreSQL is running:
```bash
docker compose ps postgres
```

### Some Jobs Still Have Placeholders
- Check if they have descriptions
- Check Gemini API logs for errors
- Re-run backfill for failed jobs

---

## 📊 Monitoring Progress

### During Backfill:
- Watch the console output
- Progress updates every 10 jobs (or custom `--batch-size`)
- Time estimates update in real-time

### After Backfill:
```bash
# Check database
psql -h localhost -U user -d jobs

SELECT 
    COUNT(*) as total,
    COUNT(CASE WHEN jsonb_array_length(embedding::jsonb) = 768 THEN 1 END) as real_embeddings
FROM jobs_enriched;
```

---

## 🎯 Best Practices

1. **Start with dry run** to see what will be processed
2. **Use appropriate delay** based on your API tier
3. **Monitor progress** during backfill
4. **Verify results** after completion
5. **Keep API key secure** (don't commit to git)

---

## 📝 Command Reference

| Command | Description |
|---------|-------------|
| `--dry-run` | Preview without making changes |
| `--batch-size N` | Show progress every N jobs |
| `--delay N` | Wait N seconds between jobs |
| `-h, --help` | Show help message |

---

## ✅ Success Criteria

After successful backfill:
- ✅ All 117 jobs have 768-dimensional embeddings
- ✅ Skills are extracted from descriptions
- ✅ Seniority levels are determined
- ✅ Summaries are AI-generated
- ✅ `view_embeddings.py` shows all real embeddings

---

## 🚀 Ready to Run!

```bash
# 1. Set API key
export GEMINI_API_KEY="your-api-key-here"

# 2. Dry run first
python3 backfill_enrichment.py --dry-run

# 3. Run the backfill
python3 backfill_enrichment.py

# 4. Verify results
python3 verify_thinking.py
```

Good luck! 🎉
