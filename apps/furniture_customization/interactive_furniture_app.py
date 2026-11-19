import streamlit as st
import cv2
import numpy as np
import json
import os
from PIL import Image, ImageDraw
from room_analyzer import extract_room_dimensions, color_maps, room_types
from streamlit_drawable_canvas import st_canvas

# Page configuration
st.set_page_config(
    page_title="Furniture Placement Designer",
    page_icon="🪑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        border-radius: 5px;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    h1 {
        color: #2c3e50;
        text-align: center;
    }
    .info-box {
        padding: 15px;
        background-color: #e8f4f8;
        border-radius: 5px;
        border-left: 5px solid #3498db;
        margin: 10px 0;
    }
    .success-box {
        padding: 10px;
        background-color: #d4edda;
        border-radius: 5px;
        border-left: 5px solid #28a745;
        margin: 10px 0;
    }
    .error-box {
        padding: 10px;
        background-color: #f8d7da;
        border-radius: 5px;
        border-left: 5px solid #dc3545;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

class InteractiveFurniturePlacement:
    def __init__(self):
        self.furniture_dir = "furniture_crops"
        self.measurements_file = os.path.join(self.furniture_dir, "furniture_measurements.json")
        self.segmented_image_path = "segmented_rooms.png"
        self.pixel_to_meter_ratio = 0.1
        
        # Initialize session state
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize all session state variables"""
        if 'rooms_info' not in st.session_state:
            st.session_state.rooms_info = None
        if 'placed_furniture' not in st.session_state:
            st.session_state.placed_furniture = []
        if 'selected_furniture' not in st.session_state:
            st.session_state.selected_furniture = None
        if 'floor_plan_loaded' not in st.session_state:
            st.session_state.floor_plan_loaded = False
        if 'canvas_image' not in st.session_state:
            st.session_state.canvas_image = None
        if 'placement_mode' not in st.session_state:
            st.session_state.placement_mode = False
        if 'canvas_key' not in st.session_state:
            st.session_state.canvas_key = 0
    
    def load_furniture_data(self):
        """Load furniture measurements and categorize them"""
        with open(self.measurements_file, 'r') as f:
            measurements = json.load(f)
        
        furniture_data = {}
        for filename, dims in measurements.items():
            filepath = os.path.join(self.furniture_dir, filename)
            if os.path.exists(filepath):
                furniture_type = filename.split('_', 1)[1].replace('.png', '').replace('-', ' ')
                category = self._categorize_furniture(furniture_type)
                
                furniture_data[filename] = {
                    'name': furniture_type.title(),
                    'category': category,
                    'width': dims['width_m'],
                    'height': dims['height_m'],
                    'image_path': filepath,
                    'filename': filename
                }
        return furniture_data
    
    def _categorize_furniture(self, name):
        """Categorize furniture by type"""
        name_lower = name.lower()
        if 'bed' in name_lower:
            return 'Bedroom'
        elif any(word in name_lower for word in ['sofa', 'chair', 'tv', 'table']):
            return 'Living Room'
        elif any(word in name_lower for word in ['sink', 'stove', 'kitchen']):
            return 'Kitchen'
        elif any(word in name_lower for word in ['bathtub', 'shower', 'commode']):
            return 'Bathroom'
        elif 'door' in name_lower:
            return 'Doors'
        elif any(word in name_lower for word in ['dining', 'study']):
            return 'Dining/Study'
        else:
            return 'Other'
    
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
        """Check if all furniture corners are within room boundaries"""
        corners = [
            (x, y),
            (x + width_pixels, y),
            (x, y + height_pixels),
            (x + width_pixels, y + height_pixels),
            (x + width_pixels/2, y + height_pixels/2)
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
    
    def render_floor_plan_with_furniture(self, floor_plan, rooms_info, placed_furniture):
        """Render the floor plan with placed furniture"""
        canvas = floor_plan.copy()
        
        # Convert to PIL for better rendering
        pil_canvas = Image.fromarray(canvas)
        draw = ImageDraw.Draw(pil_canvas, 'RGBA')
        
        # Draw room boundaries with labels
        for room_name, room_data in rooms_info.items():
            contour = room_data['contour']
            points = [(int(pt[0][0]), int(pt[0][1])) for pt in contour]
            if len(points) > 2:
                draw.polygon(points, outline=(255, 255, 255, 180), width=3)
                
                # Draw room label at centroid
                cx, cy = room_data['centroid']
                room_label = f"{room_data['type']}"
                draw.text((cx - 30, cy - 10), room_label, fill=(255, 255, 255, 255))
        
        # Draw placed furniture
        for idx, furniture in enumerate(placed_furniture):
            x, y = furniture['position']
            width_px = furniture['width_pixels']
            height_px = furniture['height_pixels']
            
            try:
                # Load and resize furniture image
                furn_img = Image.open(furniture['image_path']).convert('RGBA')
                furn_img = furn_img.resize((int(width_px), int(height_px)), Image.Resampling.LANCZOS)
                
                # Paste furniture image
                pil_canvas.paste(furn_img, (int(x), int(y)), furn_img)
                
                # Draw bounding box
                draw.rectangle(
                    [x, y, x + width_px, y + height_px],
                    outline=(0, 255, 0, 255),
                    width=3
                )
                
                # Draw furniture label
                label = f"{idx+1}. {furniture['name']}"
                draw.text((x + 5, y + 5), label, fill=(0, 255, 0, 255))
                
            except Exception as e:
                # Fallback: draw colored rectangle
                draw.rectangle(
                    [x, y, x + width_px, y + height_px],
                    fill=(100, 150, 200, 180),
                    outline=(0, 255, 0, 255),
                    width=3
                )
                label = f"{idx+1}. {furniture['name']}"
                draw.text((x + 5, y + 5), label, fill=(255, 255, 255, 255))
        
        return np.array(pil_canvas.convert('RGB'))
    
    def place_furniture(self, x, y):
        """Place selected furniture at the given coordinates"""
        if not st.session_state.selected_furniture:
            st.error("❌ No furniture selected!")
            return False
        
        furn_data = st.session_state.selected_furniture['data']
        
        # Convert meters to pixels
        width_pixels = furn_data['width'] / self.pixel_to_meter_ratio
        height_pixels = furn_data['height'] / self.pixel_to_meter_ratio
        
        # Check which room this position is in
        room_name, room_data = self.get_room_at_position(x, y, st.session_state.rooms_info)
        
        if room_name is None:
            st.error("❌ Cannot place furniture outside room boundaries!")
            return False
        
        # Check if furniture fits entirely within the room
        if not self.furniture_fits_in_room(x, y, width_pixels, height_pixels, room_data):
            st.error(f"❌ {furn_data['name']} doesn't fit within {room_name} boundaries!")
            return False
        
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
        return True
    
    def save_layout(self):
        """Save the current layout"""
        layout_data = {
            'furniture': []
        }
        
        for furniture in st.session_state.placed_furniture:
            layout_data['furniture'].append({
                'name': furniture['name'],
                'position': furniture['position'],
                'dimensions': {
                    'width_m': furniture['width_meters'],
                    'height_m': furniture['height_meters']
                },
                'room': furniture['room']
            })
        
        with open('furniture_layout.json', 'w') as f:
            json.dump(layout_data, f, indent=2)
        
        # Also save the rendered image
        if st.session_state.canvas_image is not None:
            rendered = self.render_floor_plan_with_furniture(
                st.session_state.floor_plan,
                st.session_state.rooms_info,
                st.session_state.placed_furniture
            )
            cv2.imwrite('furniture_layout.png', cv2.cvtColor(rendered, cv2.COLOR_RGB2BGR))
    
    def run(self):
        """Main application"""
        st.title("🪑 Interactive Furniture Placement Designer")
        
        # Sidebar
        with st.sidebar:
            st.header("🎛️ Control Panel")
            
            # Load floor plan
            if st.button("📐 Load Floor Plan", use_container_width=True):
                with st.spinner("Loading floor plan..."):
                    floor_plan, rooms_info = self.load_floor_plan()
                    if floor_plan is not None:
                        st.session_state.floor_plan = floor_plan
                        st.session_state.rooms_info = rooms_info
                        st.session_state.floor_plan_loaded = True
                        st.session_state.canvas_image = floor_plan.copy()
                        st.success("✅ Floor plan loaded!")
                        st.rerun()
                    else:
                        st.error("❌ Floor plan not found!")
            
            if st.session_state.floor_plan_loaded:
                st.markdown("---")
                
                # Furniture selection
                st.subheader("🛋️ Select Furniture")
                
                furniture_data = self.load_furniture_data()
                
                # Group by category
                categories = {}
                for filename, data in furniture_data.items():
                    cat = data['category']
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append((filename, data))
                
                # Display by category
                for category, items in sorted(categories.items()):
                    with st.expander(f"📦 {category} ({len(items)})"):
                        for filename, data in sorted(items, key=lambda x: x[1]['name']):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.text(data['name'])
                                st.caption(f"{data['width']:.1f}m × {data['height']:.1f}m")
                            with col2:
                                btn_key = f"select_{filename}"
                                if st.button("➕", key=btn_key, use_container_width=True):
                                    st.session_state.selected_furniture = {
                                        'filename': filename,
                                        'data': data
                                    }
                                    st.session_state.placement_mode = True
                                    st.rerun()
                
                st.markdown("---")
                
                # Currently selected
                if st.session_state.selected_furniture:
                    st.info(f"📌 Selected: **{st.session_state.selected_furniture['data']['name']}**")
                    if st.button("❌ Cancel Selection", use_container_width=True):
                        st.session_state.selected_furniture = None
                        st.session_state.placement_mode = False
                        st.rerun()
                
                st.markdown("---")
                
                # Placed furniture list
                st.subheader("📋 Placed Items")
                if st.session_state.placed_furniture:
                    for idx, furniture in enumerate(st.session_state.placed_furniture):
                        with st.container():
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.text(f"{idx+1}. {furniture['name']}")
                                st.caption(f"In: {furniture['room']}")
                            with col2:
                                if st.button("🗑️", key=f"remove_{idx}", use_container_width=True):
                                    st.session_state.placed_furniture.pop(idx)
                                    st.rerun()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🧹 Clear All", use_container_width=True):
                            st.session_state.placed_furniture = []
                            st.rerun()
                    with col2:
                        if st.button("💾 Save", use_container_width=True):
                            self.save_layout()
                            st.success("Saved!")
                else:
                    st.info("No furniture placed yet")
        
        # Main area
        if st.session_state.floor_plan_loaded:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader("🏠 Interactive Floor Plan")
                
                # Instructions
                if st.session_state.selected_furniture:
                    furn = st.session_state.selected_furniture['data']
                    st.markdown(f"""
                    <div class="info-box">
                    📍 <strong>Placement Mode Active</strong><br>
                    Click on the canvas below to place: <strong>{furn['name']}</strong> ({furn['width']:.1f}m × {furn['height']:.1f}m)
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="info-box">
                    👆 Select furniture from the sidebar, then click on the floor plan to place it
                    </div>
                    """, unsafe_allow_html=True)
                
                # Render current state
                rendered_plan = self.render_floor_plan_with_furniture(
                    st.session_state.floor_plan,
                    st.session_state.rooms_info,
                    st.session_state.placed_furniture
                )
                
                # Display with click detection
                st.image(rendered_plan, use_container_width=True, caption="Click on the image to place furniture")
                
                # Manual placement controls
                st.markdown("#### 🎯 Manual Placement")
                col_x, col_y, col_btn = st.columns([2, 2, 1])
                
                with col_x:
                    click_x = st.number_input(
                        "X coordinate (pixels)", 
                        min_value=0, 
                        max_value=rendered_plan.shape[1]-1,
                        value=rendered_plan.shape[1]//2,
                        key="manual_x"
                    )
                
                with col_y:
                    click_y = st.number_input(
                        "Y coordinate (pixels)", 
                        min_value=0, 
                        max_value=rendered_plan.shape[0]-1,
                        value=rendered_plan.shape[0]//2,
                        key="manual_y"
                    )
                
                with col_btn:
                    st.write("")
                    st.write("")
                    if st.button("📍 Place", disabled=st.session_state.selected_furniture is None):
                        if self.place_furniture(click_x, click_y):
                            st.rerun()
            
            with col2:
                st.subheader("📊 Room Details")
                
                # Display room information
                for room_name, room_data in st.session_state.rooms_info.items():
                    with st.expander(f"🚪 {room_name}"):
                        st.markdown(f"""
                        **Type:** {room_data['type']}  
                        **Area:** {room_data['area_units']:.1f} m²  
                        **Dimensions:** {room_data['width_units']:.1f} × {room_data['height_units']:.1f} m  
                        **Shape:** {room_data['shape']}
                        """)
                        
                        # Count furniture
                        furniture_in_room = [f for f in st.session_state.placed_furniture if f['room'] == room_name]
                        st.markdown(f"**Furniture Count:** {len(furniture_in_room)}")
                        
                        if furniture_in_room:
                            st.markdown("**Items:**")
                            for f in furniture_in_room:
                                st.text(f"• {f['name']}")
                
                st.markdown("---")
                
                # Statistics
                st.subheader("📈 Statistics")
                total_furniture = len(st.session_state.placed_furniture)
                total_rooms = len(st.session_state.rooms_info)
                
                st.metric("Total Furniture", total_furniture)
                st.metric("Total Rooms", total_rooms)
                
                if total_rooms > 0:
                    avg_per_room = total_furniture / total_rooms
                    st.metric("Avg per Room", f"{avg_per_room:.1f}")
        
        else:
            # Welcome screen
            st.markdown("""
            <div style='text-align: center; padding: 50px;'>
                <h2>Welcome to Furniture Placement Designer! 🏠</h2>
                <p style='font-size: 18px; color: #666;'>
                    Design your dream room layout with an interactive, boundary-aware furniture placement system
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                ### 📐 Step 1: Load
                Click **'Load Floor Plan'** in the sidebar to import your segmented room layout
                """)
            
            with col2:
                st.markdown("""
                ### 🛋️ Step 2: Select
                Choose furniture from categorized lists based on room type
                """)
            
            with col3:
                st.markdown("""
                ### 📍 Step 3: Place
                Click on the floor plan to place furniture within room boundaries
                """)
            
            st.markdown("---")
            
            st.markdown("""
            ### ✨ Features:
            - ✅ **Automatic Boundary Detection** - Furniture can only be placed within room boundaries
            - ✅ **Smart Validation** - System checks if furniture fits in the selected room
            - ✅ **Real-time Visualization** - See your layout update instantly
            - ✅ **Accurate Measurements** - All dimensions shown in meters
            - ✅ **Multi-room Support** - Design entire floor plans with multiple rooms
            - ✅ **Save & Export** - Save your designs as JSON and image files
            - ✅ **Category Organization** - Furniture organized by room type
            
            ### 🎯 Tips:
            - Start with larger furniture pieces (beds, sofas) first
            - Pay attention to room dimensions when selecting furniture
            - Use the manual placement controls for precise positioning
            - The green boxes show successfully placed furniture
            """)

if __name__ == "__main__":
    app = InteractiveFurniturePlacement()
    app.run()
