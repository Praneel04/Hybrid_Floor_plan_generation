# 🪑 Furniture Placement Designer

An interactive web application for designing room layouts with intelligent furniture placement and boundary detection.

## ✨ Features

- **Interactive Floor Plan**: Visual representation of your segmented room layout
- **Smart Boundary Detection**: Furniture can only be placed within room boundaries
- **Automatic Validation**: System validates if furniture fits in the selected room
- **Real-time Updates**: See your layout changes instantly
- **Accurate Measurements**: All dimensions displayed in meters
- **Multi-room Support**: Design complete floor plans with multiple rooms
- **Category Organization**: Furniture organized by room type (Bedroom, Living Room, Kitchen, etc.)
- **Save & Export**: Save layouts as JSON and PNG files

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## 🚀 Installation

1. **Navigate to your project directory**:
   ```bash
   cd /Users/sanjanapatel/furniture_customization
   ```

2. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Or install packages individually:
   ```bash
   pip install streamlit opencv-python numpy Pillow matplotlib streamlit-drawable-canvas
   ```

## 🎮 Usage

### Running the Application

1. **Start the Streamlit app**:
   ```bash
   streamlit run interactive_furniture_app.py
   ```
   
   Or use the simpler version:
   ```bash
   streamlit run furniture_placement_app.py
   ```

2. **Access the application**:
   - The app will automatically open in your default browser
   - Default URL: `http://localhost:8501`

### Using the Application

#### Step 1: Load Floor Plan
1. Click the **"📐 Load Floor Plan"** button in the sidebar
2. The application will load and analyze your `segmented_rooms.png` file
3. Room boundaries will be automatically detected

#### Step 2: Select Furniture
1. Browse furniture categories in the sidebar (Bedroom, Living Room, Kitchen, etc.)
2. Click the **"➕"** button next to any furniture item to select it
3. View furniture dimensions (width × height in meters)

#### Step 3: Place Furniture
1. With furniture selected, click on the floor plan where you want to place it
2. Or use the manual placement controls:
   - Enter X and Y coordinates
   - Click **"📍 Place"** button
3. The system will validate:
   - If the position is within a room
   - If the furniture fits completely within the room boundaries
4. Successfully placed furniture appears with a green bounding box

#### Step 4: Manage Your Layout
- **View Placed Items**: See all placed furniture in the sidebar
- **Remove Items**: Click the **"🗑️"** button next to any item
- **Clear All**: Remove all furniture at once
- **Save Layout**: Export your design as `furniture_layout.json` and `furniture_layout.png`

## 📁 Project Structure

```
furniture_customization/
├── furniture_placement_app.py          # Main Streamlit application
├── interactive_furniture_app.py        # Enhanced version with better UI
├── room_analyzer.py                    # Room detection and analysis
├── requirements.txt                    # Python dependencies
├── segmented_rooms.png                 # Your floor plan image
├── furniture_crops/                    # Furniture images and data
│   ├── furniture_measurements.json     # Furniture dimensions
│   └── *.png                          # Individual furniture images
└── furniture_layout.json              # Saved layout (generated)
```

## 🎨 Application Components

### Sidebar Controls
- **Load Floor Plan**: Import and analyze the floor plan
- **Furniture Categories**: Organized furniture selection
- **Placed Items**: List of all placed furniture with remove options
- **Save/Clear**: Layout management controls

### Main Canvas
- **Interactive Floor Plan**: Visual representation with placed furniture
- **Room Information**: Details about each room (area, dimensions, shape)
- **Manual Placement**: Precise coordinate-based placement
- **Statistics**: Overview of furniture count and distribution

### Room Information Panel
- Room type and dimensions
- Area in square meters
- Shape classification (rectangular, L-shaped, irregular)
- Count of furniture items in each room

## 🔧 Configuration

You can modify these parameters in the code:

```python
# In the app initialization
self.pixel_to_meter_ratio = 0.1  # Adjust based on your floor plan scale
```

## 💾 Output Files

### furniture_layout.json
JSON file containing:
- List of all placed furniture
- Position coordinates
- Dimensions in meters
- Room assignments

Example:
```json
{
  "furniture": [
    {
      "name": "Bed",
      "position": [150, 200],
      "dimensions": {
        "width_m": 6.8,
        "height_m": 7.9
      },
      "room": "bedroom_1"
    }
  ]
}
```

### furniture_layout.png
Visual representation of your final layout with:
- Floor plan background
- All placed furniture with images
- Room boundaries
- Labels and numbering

## 🎯 Tips for Best Results

1. **Start with Large Items**: Place beds and sofas first to establish the layout
2. **Check Dimensions**: Compare furniture size to room dimensions before placing
3. **Use Manual Controls**: For precise positioning, use the X/Y coordinate inputs
4. **Room-Specific Furniture**: Pay attention to furniture categories matching room types
5. **Save Frequently**: Save your work periodically to avoid losing progress

## ⚠️ Troubleshooting

### Floor Plan Not Loading
- Ensure `segmented_rooms.png` exists in the project directory
- Check that the image uses the correct color mapping defined in `room_analyzer.py`

### Furniture Not Placing
- Verify the click position is within a room boundary (not on walls or outside)
- Ensure the furniture dimensions fit within the selected room
- Check that furniture images exist in the `furniture_crops/` directory

### Import Errors
- Install all dependencies: `pip install -r requirements.txt`
- Verify Python version is 3.8 or higher: `python --version`

## 🔄 Workflow Example

1. Load floor plan → Rooms detected: bedroom_1, living_room_1, bathroom_1
2. Select "Bed" from Bedroom category (6.8m × 7.9m)
3. Click in bedroom_1 area → Bed placed successfully ✅
4. Select "Sofa" from Living Room (2.8m × 6.6m)
5. Click in living_room_1 → Sofa placed ✅
6. Continue adding furniture...
7. Save layout → Files generated: `furniture_layout.json`, `furniture_layout.png`

## 📊 Room Analysis

The application automatically analyzes each room:
- **Area**: Calculated in square meters
- **Dimensions**: Width and height using minimum bounding rectangle
- **Shape**: Classified as rectangular, L-shaped, or irregular
- **Size Category**: Small (<50m²), Medium (50-200m²), Large (>200m²)

## 🎨 Customization

### Adding Custom Furniture
1. Add furniture image to `furniture_crops/` directory
2. Update `furniture_measurements.json` with dimensions:
   ```json
   {
     "29_custom_item.png": {
       "width_m": 2.5,
       "height_m": 3.0
     }
   }
   ```
3. Restart the application

### Modifying Color Scheme
Edit the CSS in the application file:
```python
st.markdown("""
<style>
    .stButton>button {
        background-color: #YOUR_COLOR;  # Change button color
    }
</style>
""", unsafe_allow_html=True)
```

## 📝 License

This project is for educational and personal use.

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Verify all files are in the correct locations
3. Ensure all dependencies are installed

## 🚀 Future Enhancements

Potential features to add:
- Drag-and-drop furniture placement
- Rotation controls for furniture
- Undo/redo functionality
- Multiple layout versions
- 3D visualization
- Collision detection between furniture items
- Suggested layouts based on room type
- Export to PDF or other formats

---

**Happy Designing! 🏠✨**
