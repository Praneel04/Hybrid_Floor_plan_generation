#!/bin/bash

# Furniture Placement Designer - Installation Script
echo "🪑 Installing Furniture Placement Designer..."
echo "=============================================="

# Check Python version
echo "📋 Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Install dependencies
echo ""
echo "📦 Installing required packages..."
pip3 install streamlit opencv-python numpy Pillow matplotlib streamlit-drawable-canvas

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Installation completed successfully!"
    echo ""
    echo "🚀 To run the application, use one of these commands:"
    echo "   streamlit run interactive_furniture_app.py"
    echo "   or"
    echo "   streamlit run furniture_placement_app.py"
    echo ""
else
    echo "❌ Installation failed. Please check the errors above."
    exit 1
fi
