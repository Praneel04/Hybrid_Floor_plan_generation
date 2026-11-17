#!/bin/bash

# Launch script for Furniture Placement Designer

echo "🪑 Furniture Placement Designer"
echo "================================"
echo ""
echo "Starting the application..."
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null
then
    echo "❌ Streamlit is not installed."
    echo "Run: pip install -r requirements.txt"
    exit 1
fi

# Launch the app
streamlit run interactive_furniture_app.py

# Alternative: Use the simpler version
# streamlit run furniture_placement_app.py
