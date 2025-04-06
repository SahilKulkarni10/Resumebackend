#!/bin/bash

# Step 1: Get a FREE Gemini API key
# - Go to https://aistudio.google.com/app/apikey
# - Sign in with your Google account
# - Click "Create API key" to get a free API key
# - Replace the value below with your actual API key

# Set your Gemini API key here (keep the quotes)
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

# Step 2: Make this script executable
# Run this command in your terminal: chmod +x run_server.sh

# Step 3: Run the server
# Execute: ./run_server.sh

# Verify API key is set
if [ "$GEMINI_API_KEY" = "YOUR_GEMINI_API_KEY" ]; then
  echo "⚠️  Warning: You need to edit this file and add your actual Gemini API key."
  echo "   The AI feedback feature will not work without a valid API key."
  echo ""
  echo "   Get a FREE API key from: https://aistudio.google.com/app/apikey"
  echo "   No credit card required. Just sign in with your Google account."
  echo ""
  read -p "Continue anyway? (y/n) " -n 1 -r
  echo ""
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

echo "Starting server with Gemini API key..."
echo "Open http://localhost:5001 in your browser"
python app.py 