import streamlit as st
import cv2
import numpy as np
import json
import os
from PIL import Image, ImageDraw, ImageFont
from room_analyzer import extract_room_dimensions, color_maps, room_types
import base64
from io import BytesIO

# Page configuration
st.set_page_config(
    page_title="Furniture Placement Designer",
    page_icon="🪑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #4CAF50;
        color: white;
    }
    .furniture-item {
        padding: 10px;
        margin: 5px;
        border: 2px solid #ddd;
        border-radius: 5px;
        background-color: white;
    }
    h1 {
        color: #2c3e50;
    }
    .info-box {
        padding: 15px;
        background-color: #e8f4f8;
        border-radius: 5px;
        border-left: 5px solid #3498db;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

class FurniturePlacementApp:
    def __init__(self):
        self.furniture_dir = "furniture_crops"
        self.measurements_file = os.path.join(self.furniture_dir, "furniture_measurements.json")
        self.segmented_image_path = "segmented_rooms.png"
        self.pixel_to_meter_ratio = 0.1
        
        # Initialize session state
        if 'rooms_info' not in st.session_state:
            st.session_state.rooms_info = None
        if 'placed_furniture' not in st.session_state:
            st.session_state.placed_furniture = []
        if 'selected_furniture' not in st.session_state:
            st.session_state.selected_furniture = None
        if 'floor_plan_loaded' not in st.session_state:
            st.session_state.floor_plan_loaded = False
        if 'scale_factor' not in st.session_state:
            st.session_state.scale_factor = 1.0
    
    def load_furniture_data(self):
        """Load furniture measurements and images"""
        with open(self.measurements_file, 'r') as f:
            measurements = json.load(f)
        
        furniture_data = {}
        for filename, dims in measurements.items():
            filepath = os.path.join(self.furniture_dir, filename)
            if os.path.exists(filepath):
                furniture_type = filename.split('_', 1)[1].replace('.png', '').replace('-', ' ')
                furniture_data[filename] = {
                    'name': furniture_type.title(),
                    'width': dims['width_m'],
                    'height': dims['height_m'],
                    'image_path': filepath,
                    'filename': filename
                }
        return furniture_data
    
    def load_floor_plan(self):
        """Load and analyze the floor plan"""
        if not os.path.exists(self.segmented_image_path):
            return None, None
        
        segmented = cv2.imread(self.segmented_image_path)
        segmented_rgb = cv2.cvtColor(segmented, cv2.COLOR_BGR2RGB)
        
        rooms_info = extract_room_dimensions(
            segmented_rgb, 
            color_maps, 
            room_types, 
            self.pixel_to_meter_ratio
        )
        
        return segmented_rgb, rooms_info
    
    def point_in_room(self, point, room_data):
        """Check if a point is inside a room's contour"""
        contour = room_data['contour']
        result = cv2.pointPolygonTest(contour, point, False)
        return result >= 0
    
    def furniture_fits_in_room(self, x, y, width_pixels, height_pixels, room_data):
        """Check if furniture corners are all within room boundaries"""
        corners = [
            (x, y),
            (x + width_pixels, y),
            (x, y + height_pixels),
            (x + width_pixels, y + height_pixels),
            (x + width_pixels/2, y + height_pixels/2)  # center point
        ]
        
        contour = room_data['contour']
        for corner in corners:
            result = cv2.pointPolygonTest(contour, corner, False)
            if result < 0:
                return False
        return True
    
    def get_room_at_position(self, x, y, rooms_info):
        """Get the room at a specific position"""
        for room_name, room_data in rooms_info.items():
            if self.point_in_room((x, y), room_data):
                return room_name, room_data
        return None, None
    
    def render_floor_plan_with_furniture(self, floor_plan, rooms_info, placed_furniture, scale_factor=1.0):
        """Render the floor plan with placed furniture"""
        # Create a copy of the floor plan
        canvas = floor_plan.copy()
        height, width = canvas.shape[:2]
        
        # Convert to PIL for better rendering
        pil_canvas = Image.fromarray(canvas)
        draw = ImageDraw.Draw(pil_canvas, 'RGBA')
        
        # Draw room boundaries
        for room_name, room_data in rooms_info.items():
            contour = room_data['contour']
            points = [(int(pt[0][0]), int(pt[0][1])) for pt in contour]
            if len(points) > 2:
                draw.polygon(points, outline=(255, 255, 255, 128), width=2)
        
        # Draw placed furniture
        for furniture in placed_furniture:
            x, y = furniture['position']
            width_px = furniture['width_pixels']
            height_px = furniture['height_pixels']
            
            # Load furniture image
            try:
                furn_img = Image.open(furniture['image_path']).convert('RGBA')
                furn_img = furn_img.resize((int(width_px), int(height_px)), Image.Resampling.LANCZOS)
                
                # Create a semi-transparent overlay
                overlay = Image.new('RGBA', pil_canvas.size, (255, 255, 255, 0))
                overlay.paste(furn_img, (int(x), int(y)), furn_img)
                pil_canvas = Image.alpha_composite(pil_canvas.convert('RGBA'), overlay)
                
                # Draw bounding box
                draw = ImageDraw.Draw(pil_canvas)
                draw.rectangle(
                    [x, y, x + width_px, y + height_px],
                    outline=(0, 255, 0, 255),
                    width=2
                )
                
                # Draw label
                draw.text(
                    (x + 5, y + 5),
                    furniture['name'],
                    fill=(255, 255, 255, 255)
                )
            except Exception as e:
                # Draw a rectangle if image loading fails
                draw.rectangle(
                    [x, y, x + width_px, y + height_px],
                    fill=(100, 150, 200, 128),
                    outline=(0, 255, 0, 255),
                    width=2
                )
        
        return np.array(pil_canvas.convert('RGB'))
    
    def run(self):
        """Main application loop"""
        st.title("🪑 Furniture Placement Designer")
        st.markdown("### Design your room layout by placing furniture within room boundaries")
        
        # Sidebar for controls
        with st.sidebar:
            st.header("🎨 Controls")
            
            # Load floor plan button
            if st.button("📐 Load Floor Plan", key="load_plan"):
                with st.spinner("Loading floor plan..."):
                    floor_plan, rooms_info = self.load_floor_plan()
                    if floor_plan is not None:
                        st.session_state.floor_plan = floor_plan
                        st.session_state.rooms_info = rooms_info
                        st.session_state.floor_plan_loaded = True
                        st.success("✅ Floor plan loaded successfully!")
                    else:
                        st.error("❌ Floor plan not found!")
            
            st.markdown("---")
            
            # Furniture selection
            if st.session_state.floor_plan_loaded:
                st.subheader("🛋️ Available Furniture")
                
                furniture_data = self.load_furniture_data()
                
                # Group furniture by type
                furniture_types = {}
                for filename, data in furniture_data.items():
                    ftype = data['name'].split()[0] if ' ' in data['name'] else data['name']
                    if ftype not in furniture_types:
                        furniture_types[ftype] = []
                    furniture_types[ftype].append((filename, data))
                
                # Display furniture by category
                for ftype, items in sorted(furniture_types.items()):
                    with st.expander(f"📦 {ftype}"):
                        for filename, data in items:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.text(f"{data['name']}")
                                st.caption(f"{data['width']:.1f}m × {data['height']:.1f}m")
                            with col2:
                                if st.button("➕", key=f"add_{filename}"):
                                    st.session_state.selected_furniture = {
                                        'filename': filename,
                                        'data': data
                                    }
                                    st.rerun()
                
                st.markdown("---")
                
                # Placed furniture management
                st.subheader("📋 Placed Furniture")
                if st.session_state.placed_furniture:
                    for idx, furniture in enumerate(st.session_state.placed_furniture):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.text(f"{furniture['name']}")
                            st.caption(f"Room: {furniture['room']}")
                        with col2:
                            if st.button("🗑️", key=f"remove_{idx}"):
                                st.session_state.placed_furniture.pop(idx)
                                st.rerun()
                else:
                    st.info("No furniture placed yet")
                
                if st.button("🧹 Clear All"):
                    st.session_state.placed_furniture = []
                    st.rerun()
                
                if st.button("💾 Save Layout"):
                    self.save_layout()
                    st.success("Layout saved!")
        
        # Main canvas area
        if st.session_state.floor_plan_loaded:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader("🏠 Floor Plan")
                
                # Display instructions
                if st.session_state.selected_furniture:
                    furn_data = st.session_state.selected_furniture['data']
                    st.info(f"📍 Click on the floor plan to place: **{furn_data['name']}** ({furn_data['width']:.1f}m × {furn_data['height']:.1f}m)")
                else:
                    st.info("👆 Select furniture from the sidebar to place it on the floor plan")
                
                # Render the floor plan
                rendered_plan = self.render_floor_plan_with_furniture(
                    st.session_state.floor_plan,
                    st.session_state.rooms_info,
                    st.session_state.placed_furniture
                )
                
                st.image(rendered_plan, use_container_width=True)
                
                # Click handling simulation (using number inputs as coordinates)
                st.markdown("#### 🖱️ Place Furniture")
                st.caption("Enter coordinates to place selected furniture (in pixels)")
                
                col_x, col_y, col_place = st.columns([1, 1, 1])
                with col_x:
                    click_x = st.number_input("X coordinate", min_value=0, max_value=rendered_plan.shape[1], value=100, key="click_x")
                with col_y:
                    click_y = st.number_input("Y coordinate", min_value=0, max_value=rendered_plan.shape[0], value=100, key="click_y")
                with col_place:
                    st.write("")  # Spacing
                    st.write("")  # Spacing
                    if st.button("📍 Place Here", disabled=st.session_state.selected_furniture is None):
                        if st.session_state.selected_furniture:
                            self.place_furniture(click_x, click_y)
            
            with col2:
                st.subheader("📊 Room Info")
                
                # Display room statistics
                for room_name, room_data in st.session_state.rooms_info.items():
                    with st.expander(f"🚪 {room_name}"):
                        st.write(f"**Type:** {room_data['type']}")
                        st.write(f"**Area:** {room_data['area_units']:.1f} m²")
                        st.write(f"**Dimensions:** {room_data['width_units']:.1f} × {room_data['height_units']:.1f} m")
                        st.write(f"**Shape:** {room_data['shape']}")
                        
                        # Count furniture in this room
                        furniture_count = sum(1 for f in st.session_state.placed_furniture if f['room'] == room_name)
                        st.write(f"**Furniture:** {furniture_count} items")
        else:
            st.info("👈 Click 'Load Floor Plan' in the sidebar to get started!")
            
            # Show a placeholder or instructions
            st.markdown("""
            ### How to use:
            1. **Load Floor Plan** - Click the button in the sidebar to load your floor plan
            2. **Select Furniture** - Choose furniture from the categorized list
            3. **Place Furniture** - Enter coordinates to place furniture on the floor plan
            4. **Manage Placement** - View and remove placed furniture from the sidebar
            5. **Save Layout** - Export your design when complete
            
            #### Features:
            - ✅ Automatic boundary detection
            - ✅ Room-specific placement validation
            - ✅ Real-time visualization
            - ✅ Furniture measurements in meters
            - ✅ Multi-room support
            """)
    
    def place_furniture(self, x, y):
        """Place selected furniture at the given coordinates"""
        if not st.session_state.selected_furniture:
            st.error("No furniture selected!")
            return
        
        furn_data = st.session_state.selected_furniture['data']
        
        # Convert meters to pixels
        width_pixels = furn_data['width'] / self.pixel_to_meter_ratio
        height_pixels = furn_data['height'] / self.pixel_to_meter_ratio
        
        # Check which room this position is in
        room_name, room_data = self.get_room_at_position(x, y, st.session_state.rooms_info)
        
        if room_name is None:
            st.error("❌ Cannot place furniture outside room boundaries!")
            return
        
        # Check if furniture fits entirely within the room
        if not self.furniture_fits_in_room(x, y, width_pixels, height_pixels, room_data):
            st.error(f"❌ Furniture doesn't fit within {room_name} boundaries!")
            return
        
        # Add furniture to placed list
        furniture_item = {
            'name': furn_data['name'],
            'position': (x, y),
            'width_pixels': width_pixels,
            'height_pixels': height_pixels,
            'width_meters': furn_data['width'],
            'height_meters': furn_data['height'],
            'room': room_name,
            'image_path': furn_data['image_path']
        }
        
        st.session_state.placed_furniture.append(furniture_item)
        st.session_state.selected_furniture = None
        st.success(f"✅ {furn_data['name']} placed in {room_name}!")
        st.rerun()
    
    def save_layout(self):
        """Save the current layout to a JSON file"""
        layout_data = {
            'rooms': st.session_state.rooms_info,
            'furniture': st.session_state.placed_furniture,
            'pixel_to_meter_ratio': self.pixel_to_meter_ratio
        }
        
        # Convert numpy arrays to lists for JSON serialization
        def convert_to_serializable(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, tuple):
                return list(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(item) for item in obj]
            return obj
        
        serializable_data = convert_to_serializable(layout_data)
        
        with open('furniture_layout.json', 'w') as f:
            json.dump(serializable_data, f, indent=2, default=str)

if __name__ == "__main__":
    app = FurniturePlacementApp()
    app.run()
