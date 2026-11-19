# 🚀 Quick Start Guide

## Installation (One-Time Setup)

### Option 1: Automatic Installation
```bash
chmod +x install.sh
./install.sh
```

### Option 2: Manual Installation
```bash
pip install -r requirements.txt
```

## Running the Application

### Interactive Version (Recommended)
```bash
streamlit run interactive_furniture_app.py
```

### Standard Version
```bash
streamlit run furniture_placement_app.py
```

The application will open automatically in your browser at `http://localhost:8501`

## Quick Tutorial

### 1️⃣ Load Your Floor Plan
- Click **"📐 Load Floor Plan"** in the left sidebar
- Wait for room detection to complete

### 2️⃣ Select Furniture
- Expand furniture categories in the sidebar
- Click **"➕"** next to any item to select it

### 3️⃣ Place Furniture
**Method A - Click Placement:**
- Click on the floor plan where you want the furniture

**Method B - Manual Coordinates:**
- Enter X and Y coordinates in the input fields
- Click **"📍 Place"** button

### 4️⃣ Manage Your Layout
- **Remove item**: Click 🗑️ next to any placed furniture
- **Clear all**: Click "🧹 Clear All" button
- **Save layout**: Click "💾 Save" button

## Features at a Glance

| Feature | Description |
|---------|-------------|
| 🏠 Room Detection | Automatically detects room boundaries |
| 📏 Smart Validation | Only places furniture within room boundaries |
| 📊 Real-time Updates | Instant visual feedback |
| 📁 Category Browser | Organized furniture by room type |
| 💾 Export | Save as JSON + PNG files |
| 🗑️ Easy Management | Add/remove furniture with one click |

## Keyboard Shortcuts (Browser)

- `Ctrl/Cmd + R` - Refresh the app
- `Ctrl/Cmd + S` - (After implementing) Quick save

## File Locations

- **Input**: `segmented_rooms.png` (your floor plan)
- **Furniture**: `furniture_crops/` directory
- **Output**: `furniture_layout.json` and `furniture_layout.png`

## Common Issues

**Problem**: App won't start
```bash
# Solution: Install dependencies
pip install streamlit opencv-python numpy Pillow matplotlib
```

**Problem**: Floor plan not loading
- Ensure `segmented_rooms.png` exists in the same directory
- Check file permissions

**Problem**: Can't place furniture
- Verify you're clicking inside a room (not on walls)
- Check that furniture fits within the room dimensions

## Tips for Success

✅ **DO:**
- Start with larger furniture (beds, sofas)
- Check room dimensions before selecting furniture
- Save your work periodically

❌ **DON'T:**
- Try to place furniture on walls or outside rooms
- Select furniture larger than the room
- Close the browser without saving

## Next Steps

1. Experiment with different layouts
2. Try all furniture categories
3. Save multiple layout versions
4. Share your designs!

## Need Help?

- Check the full `README.md` for detailed information
- Review the troubleshooting section
- Verify all files are in the correct location

---

**Ready to start designing? Run the app now! 🎨**

```bash
streamlit run interactive_furniture_app.py
```
