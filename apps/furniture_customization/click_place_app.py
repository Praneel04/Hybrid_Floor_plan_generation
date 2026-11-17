import streamlit as st
import cv2
import numpy as np
import json
import os
from PIL import Image, ImageDraw
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

# Custom CSS with drag-drop styling
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
    .furniture-selected {
        border: 3px solid #4CAF50;
        background-color: #e8f5e9;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .placement-instruction {
        background-color: #fff3cd;
        padding: 15px;
        border-left: 5px solid #ffc107;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# JavaScript for click handling
click_handler_js = """
<script>
    const canvas = window.parent.document.querySelector('img[src*="data:image"]');
    if (canvas) {
        canvas.style.cursor = 'crosshair';
        canvas.onclick = function(e) {
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.naturalWidth / rect.width;
            const scaleY = canvas.naturalHeight / rect.height;
            const x = Math.round((e.clientX - rect.left) * scaleX);
            const y = Math.round((e.clientY - rect.top) * scaleY);
            window.parent.postMessage({type: 'streamlit:setComponentValue', value: {x: x, y: y}}, '*');
        };
    }
</script>
"""

class DragDropFurnitureApp:
    def __init__(self):
        self.furniture_dir = "furniture_crops"
        self.measurements_file = os.path.join(self.furniture_dir, "furniture_measurements.json")
        self.segmented_image_path = "segmented_rooms.png"
        self.pixel_to_meter_ratio = 0.1
        
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state variables"""
        if 'rooms_info' not in st.session_state:
            st.session_state.rooms_info = None
        if 'placed_furniture' not in st.session_state:
            st.session_state.placed_furniture = []
        if 'selected_furniture' not in st.session_state:
            st.session_state.selected_furniture = None
        if 'floor_plan_loaded' not in st.session_state:
            st.session_state.floor_plan_loaded = False
        if 'floor_plan' not in st.session_state:
            st.session_state.floor_plan = None
        if 'click_count' not in st.session_state:
            st.session_state.click_count = 0
        if 'dragging_furniture' not in st.session_state:
            st.session_state.dragging_furniture = None
        if 'furniture_id_counter' not in st.session_state:
            st.session_state.furniture_id_counter = 0
    
    def load_furniture_data(self):
        """Load furniture measurements"""
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
        elif any(word in name_lower for word in ['sofa', 'chair', 'tv']):
            return 'Living Room'
        elif any(word in name_lower for word in ['sink', 'stove', 'kitchen']):
            return 'Kitchen'
        elif any(word in name_lower for word in ['bathtub', 'shower', 'commode']):
            return 'Bathroom'
        elif 'door' in name_lower:
            return 'Doors'
        elif any(word in name_lower for word in ['table', 'study', 'dining']):
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
    
    def render_floor_plan_with_furniture(self, floor_plan, rooms_info, placed_furniture, highlight_position=None):
        """Render the floor plan with placed furniture and optional highlight"""
        canvas = floor_plan.copy()
        
        # Convert to PIL for better rendering
        pil_canvas = Image.fromarray(canvas).convert('RGBA')
        overlay = Image.new('RGBA', pil_canvas.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Draw room boundaries
        for room_name, room_data in rooms_info.items():
            contour = room_data['contour']
            points = [(int(pt[0][0]), int(pt[0][1])) for pt in contour]
            if len(points) > 2:
                draw.polygon(points, outline=(255, 255, 255, 100), width=2)
        
        # Draw placed furniture
        for furniture in placed_furniture:
            x, y = furniture['position']
            width_px = furniture['width_pixels']
            height_px = furniture['height_pixels']
            
            try:
                # Load and resize furniture image
                furn_img = Image.open(furniture['image_path']).convert('RGBA')
                furn_img = furn_img.resize((int(width_px), int(height_px)), Image.Resampling.LANCZOS)
                
                # Paste furniture image
                overlay.paste(furn_img, (int(x), int(y)), furn_img)
                
                # Draw bounding box
                draw.rectangle(
                    [x, y, x + width_px, y + height_px],
                    outline=(0, 255, 0, 200),
                    width=2
                )
                
                # Draw label
                label = f"{furniture['id']}. {furniture['name']}"
                draw.text((x + 3, y + 3), label, fill=(255, 255, 255, 255))
                
            except Exception as e:
                # Fallback: draw colored rectangle
                draw.rectangle(
                    [x, y, x + width_px, y + height_px],
                    fill=(100, 150, 200, 150),
                    outline=(0, 255, 0, 200),
                    width=2
                )
        
        # Draw highlight position if provided (for preview)
        if highlight_position and st.session_state.selected_furniture:
            x, y = highlight_position
            furn_data = st.session_state.selected_furniture['data']
            width_px = furn_data['width'] / self.pixel_to_meter_ratio
            height_px = furn_data['height'] / self.pixel_to_meter_ratio
            
            # Draw semi-transparent preview
            draw.rectangle(
                [x, y, x + width_px, y + height_px],
                fill=(100, 200, 100, 100),
                outline=(0, 255, 0, 200),
                width=3
            )
            draw.text((x + 3, y + 3), "Preview", fill=(255, 255, 255, 255))
        
        # Composite overlay onto canvas
        pil_canvas = Image.alpha_composite(pil_canvas, overlay)
        
        return np.array(pil_canvas.convert('RGB'))
    
    def place_furniture_at_position(self, x, y):
        """Place selected furniture at the given coordinates"""
        if not st.session_state.selected_furniture:
            return False, "No furniture selected!"
        
        furn_data = st.session_state.selected_furniture['data']
        
        # Convert meters to pixels
        width_pixels = furn_data['width'] / self.pixel_to_meter_ratio
        height_pixels = furn_data['height'] / self.pixel_to_meter_ratio
        
        # Check which room this position is in
        room_name, room_data = self.get_room_at_position(x, y, st.session_state.rooms_info)
        
        if room_name is None:
            return False, "❌ Cannot place furniture outside room boundaries!"
        
        # Check if furniture fits entirely within the room
        if not self.furniture_fits_in_room(x, y, width_pixels, height_pixels, room_data):
            return False, f"❌ {furn_data['name']} doesn't fit within {room_name} boundaries!"
        
        # Add furniture to placed list
        st.session_state.furniture_id_counter += 1
        furniture_item = {
            'id': st.session_state.furniture_id_counter,
            'name': furn_data['name'],
            'position': (int(x), int(y)),
            'width_pixels': width_pixels,
            'height_pixels': height_pixels,
            'width_meters': furn_data['width'],
            'height_meters': furn_data['height'],
            'room': room_name,
            'image_path': furn_data['image_path']
        }
        
        st.session_state.placed_furniture.append(furniture_item)
        return True, f"✅ {furn_data['name']} placed in {room_name}!"
    
    def save_layout(self):
        """Save the current layout"""
        layout_data = {
            'furniture': []
        }
        
        for furniture in st.session_state.placed_furniture:
            layout_data['furniture'].append({
                'id': furniture['id'],
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
        if st.session_state.floor_plan is not None:
            rendered = self.render_floor_plan_with_furniture(
                st.session_state.floor_plan,
                st.session_state.rooms_info,
                st.session_state.placed_furniture
            )
            cv2.imwrite('furniture_layout.png', cv2.cvtColor(rendered, cv2.COLOR_RGB2BGR))
    
    def run(self):
        """Main application"""
        st.title("🪑 Interactive Furniture Placement Designer")
        st.markdown("### Click on the floor plan to place furniture!")
        
        # Sidebar
        with st.sidebar:
            st.header("🎛️ Control Panel")
            
            # Load floor plan
            if st.button("📐 Load Floor Plan", key="load_btn"):
                with st.spinner("Loading floor plan..."):
                    floor_plan, rooms_info = self.load_floor_plan()
                    if floor_plan is not None:
                        st.session_state.floor_plan = floor_plan
                        st.session_state.rooms_info = rooms_info
                        st.session_state.floor_plan_loaded = True
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
                                st.caption(f"📏 {data['width']:.1f}m × {data['height']:.1f}m")
                            with col2:
                                btn_key = f"select_{filename}"
                                if st.button("🎯", key=btn_key, help="Select to place"):
                                    st.session_state.selected_furniture = {
                                        'filename': filename,
                                        'data': data
                                    }
                                    st.rerun()
                
                st.markdown("---")
                
                # Currently selected
                if st.session_state.selected_furniture:
                    furn = st.session_state.selected_furniture['data']
                    st.markdown(f"""
                    <div class="furniture-selected">
                        <strong>📌 Selected:</strong><br>
                        {furn['name']}<br>
                        <small>{furn['width']:.1f}m × {furn['height']:.1f}m</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("❌ Cancel Selection"):
                        st.session_state.selected_furniture = None
                        st.rerun()
                else:
                    st.info("👆 Select furniture to place")
                
                st.markdown("---")
                
                # Placed furniture list
                st.subheader("📋 Placed Items")
                if st.session_state.placed_furniture:
                    for idx, furniture in enumerate(st.session_state.placed_furniture):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.text(f"{furniture['id']}. {furniture['name']}")
                            st.caption(f"📍 {furniture['room']}")
                        with col2:
                            if st.button("🗑️", key=f"remove_{furniture['id']}"):
                                st.session_state.placed_furniture.pop(idx)
                                st.rerun()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🧹 Clear All"):
                            st.session_state.placed_furniture = []
                            st.rerun()
                    with col2:
                        if st.button("💾 Save"):
                            self.save_layout()
                            st.success("✅ Saved!")
                else:
                    st.info("No furniture placed yet")
                
                st.markdown("---")
                
                # Quick stats
                st.subheader("📊 Statistics")
                st.metric("Total Furniture", len(st.session_state.placed_furniture))
                st.metric("Rooms", len(st.session_state.rooms_info))
        
        # Main area
        if st.session_state.floor_plan_loaded:
            # Instructions
            if st.session_state.selected_furniture:
                furn = st.session_state.selected_furniture['data']
                st.markdown(f"""
                <div class="placement-instruction">
                    <strong>🎯 PLACEMENT MODE ACTIVE</strong><br>
                    Click anywhere on the floor plan below to place: <strong>{furn['name']}</strong> ({furn['width']:.1f}m × {furn['height']:.1f}m)<br>
                    <small>The furniture will snap to where you click. Green outline = valid placement.</small>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("👆 Select furniture from the sidebar, then click on the floor plan to place it")
            
            # Create two columns for canvas and info
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader("🏠 Floor Plan Canvas")
                
                # Render the floor plan
                rendered_plan = self.render_floor_plan_with_furniture(
                    st.session_state.floor_plan,
                    st.session_state.rooms_info,
                    st.session_state.placed_furniture
                )
                
                # Display image with click detection
                img_height, img_width = rendered_plan.shape[:2]
                
                # Show the image
                st.image(rendered_plan, use_column_width=True, caption="👆 Click to place furniture")
                
                # Click coordinate input (simulating click)
                st.markdown("#### 🎯 Click Position (Manual Input)")
                st.caption("Use sliders to simulate clicking on the canvas")
                
                col_x, col_y, col_btn = st.columns([2, 2, 1])
                
                with col_x:
                    click_x = st.slider(
                        "X coordinate", 
                        0, img_width-1, 
                        img_width//2,
                        key="click_x_slider"
                    )
                
                with col_y:
                    click_y = st.slider(
                        "Y coordinate", 
                        0, img_height-1, 
                        img_height//2,
                        key="click_y_slider"
                    )
                
                with col_btn:
                    st.write("")
                    st.write("")
                    if st.button("📍 Place Here", disabled=st.session_state.selected_furniture is None):
                        success, message = self.place_furniture_at_position(click_x, click_y)
                        if success:
                            st.success(message)
                            st.session_state.selected_furniture = None
                            st.rerun()
                        else:
                            st.error(message)
                
                # Show preview at current slider position
                if st.session_state.selected_furniture:
                    preview = self.render_floor_plan_with_furniture(
                        st.session_state.floor_plan,
                        st.session_state.rooms_info,
                        st.session_state.placed_furniture,
                        highlight_position=(click_x, click_y)
                    )
                    st.image(preview, use_column_width=True, caption="👁️ Preview at current position")
            
            with col2:
                st.subheader("📊 Room Details")
                
                # Display room information
                for room_name, room_data in st.session_state.rooms_info.items():
                    with st.expander(f"🚪 {room_name}"):
                        st.markdown(f"""
                        **Type:** {room_data['type']}  
                        **Area:** {room_data['area_units']:.1f} m²  
                        **Size:** {room_data['width_units']:.1f} × {room_data['height_units']:.1f} m
                        """)
                        
                        # Count furniture
                        furniture_in_room = [f for f in st.session_state.placed_furniture if f['room'] == room_name]
                        st.markdown(f"**Items:** {len(furniture_in_room)}")
                        
                        if furniture_in_room:
                            for f in furniture_in_room:
                                st.caption(f"• {f['id']}. {f['name']}")
        
        else:
            # Welcome screen
            st.markdown("""
            <div style='text-align: center; padding: 50px;'>
                <h2>Welcome! 🏠</h2>
                <p style='font-size: 18px;'>
                    Click <strong>'Load Floor Plan'</strong> in the sidebar to get started
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                ### 📐 Step 1
                Load your floor plan with room detection
                """)
            
            with col2:
                st.markdown("""
                ### 🛋️ Step 2
                Select furniture from the sidebar
                """)
            
            with col3:
                st.markdown("""
                ### 🎯 Step 3
                Click on the floor plan to place
                """)

if __name__ == "__main__":
    app = DragDropFurnitureApp()
    app.run()
