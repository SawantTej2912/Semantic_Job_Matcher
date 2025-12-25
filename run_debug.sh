#!/bin/bash
# Helper script to run debug_consumer.py with Gemini API key

echo "🔍 Gemini Enrichment Debug Script"
echo "=================================="
echo ""

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  GEMINI_API_KEY is not set!"
    echo ""
    echo "To use real Gemini enrichment, set your API key:"
    echo "  export GEMINI_API_KEY=\"your-api-key-here\""
    echo ""
    echo "Get your API key from: https://aistudio.google.com/apikey"
    echo ""
    read -p "Continue with placeholder functions? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Please set GEMINI_API_KEY and try again."
        exit 1
    fi
    echo ""
    echo "Running with placeholder functions..."
else
    echo "✅ GEMINI_API_KEY is set (length: ${#GEMINI_API_KEY})"
fi

echo ""
echo "Starting debug consumer..."
echo ""

# Run the debug script
python3 debug_consumer.py
