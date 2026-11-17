import streamlit as st
import streamlit.components.v1 as components
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
    page_title="Room-by-Room Furniture Designer",
    page_icon="🏠",
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
        width: 100%;
        border-radius: 5px;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .room-selected {
        background-color: #e3f2fd;
        padding: 15px;
        border-left: 5px solid #2196F3;
        border-radius: 5px;
        margin: 10px 0;
    }
    .furniture-active {
        background-color: #fff3cd;
        padding: 10px;
        border-left: 5px solid #ffc107;
        border-radius: 5px;
        margin: 5px 0;
    }
    .instruction-box {
        background-color: #d1ecf1;
        padding: 15px;
        border-left: 5px solid #17a2b8;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

class RoomByRoomDesigner:
    def __init__(self):
        self.furniture_dir = "furniture_crops"
        self.measurements_file = os.path.join(self.furniture_dir, "furniture_measurements.json")
        self.segmented_image_path = "segmented_rooms.png"
        self.pixel_to_meter_ratio = 0.1
        self.zoom_padding = 30  # Padding around room when zooming
        self.max_display_size = 800  # Maximum size for display (will scale down if needed)
        
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state"""
        if 'rooms_info' not in st.session_state:
            st.session_state.rooms_info = None
        if 'placed_furniture' not in st.session_state:
            st.session_state.placed_furniture = {}  # Dict by room name
        if 'selected_furniture' not in st.session_state:
            st.session_state.selected_furniture = None
        if 'floor_plan_loaded' not in st.session_state:
            st.session_state.floor_plan_loaded = False
        if 'floor_plan' not in st.session_state:
            st.session_state.floor_plan = None
        if 'current_room' not in st.session_state:
            st.session_state.current_room = None
        if 'room_image' not in st.session_state:
            st.session_state.room_image = None
        if 'room_offset' not in st.session_state:
            st.session_state.room_offset = (0, 0)
        if 'furniture_id_counter' not in st.session_state:
            st.session_state.furniture_id_counter = 0
        if 'click_data' not in st.session_state:
            st.session_state.click_data = None
        if 'room_scale' not in st.session_state:
            st.session_state.room_scale = 1.0
        if 'last_click_x' not in st.session_state:
            st.session_state.last_click_x = None
        if 'last_click_y' not in st.session_state:
            st.session_state.last_click_y = None
    
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
    
    def extract_room_region(self, floor_plan, room_data):
        """Extract and zoom into a specific room with padding - no scaling to avoid cutoffs"""
        # Get bounding box from contour
        contour = room_data['contour']
        x, y, w, h = cv2.boundingRect(contour)
        
        # Add generous padding to ensure full room is visible
        padding = 50
        x_start = max(0, x - padding)
        y_start = max(0, y - padding)
        x_end = min(floor_plan.shape[1], x + w + padding)
        y_end = min(floor_plan.shape[0], y + h + padding)
        
        # Extract region - no scaling, keep original size
        room_image = floor_plan[y_start:y_end, x_start:x_end].copy()
        
        # Store offset for coordinate transformation
        offset = (x_start, y_start)
        scale = 1.0  # No scaling
        
        # Shift contour to room region coordinates
        contour_shifted = contour.copy()
        contour_shifted[:, 0, 0] = contour_shifted[:, 0, 0] - x_start
        contour_shifted[:, 0, 1] = contour_shifted[:, 0, 1] - y_start
        
        # Draw room boundary
        room_image_pil = Image.fromarray(room_image).convert('RGBA')
        overlay = Image.new('RGBA', room_image_pil.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Draw contour
        points = [(int(pt[0][0]), int(pt[0][1])) for pt in contour_shifted]
        if len(points) > 2:
            draw.polygon(points, outline=(255, 255, 0, 255), width=4)
        
        room_image_pil = Image.alpha_composite(room_image_pil, overlay)
        
        return np.array(room_image_pil.convert('RGB')), offset, contour_shifted, scale
    
    def point_in_room(self, point, contour):
        """Check if a point is inside room contour"""
        result = cv2.pointPolygonTest(contour, point, False)
        return result >= 0
    
    def furniture_fits_in_room(self, x, y, width_pixels, height_pixels, contour):
        """Check if furniture fits within room boundaries"""
        corners = [
            (x, y),
            (x + width_pixels, y),
            (x, y + height_pixels),
            (x + width_pixels, y + height_pixels),
            (x + width_pixels/2, y + height_pixels/2)
        ]
        
        for corner in corners:
            result = cv2.pointPolygonTest(contour, corner, False)
            if result < 0:
                return False
        return True
    
    def render_room_with_furniture(self, room_image, room_name, room_contour, offset, scale=1.0):
        """Render room with placed furniture"""
        canvas = room_image.copy()
        pil_canvas = Image.fromarray(canvas).convert('RGBA')
        overlay = Image.new('RGBA', pil_canvas.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Draw room boundary
        points = [(int(pt[0][0]), int(pt[0][1])) for pt in room_contour]
        if len(points) > 2:
            draw.polygon(points, outline=(255, 255, 0, 200), width=3)
        
        # Draw placed furniture in this room (no scaling since scale=1.0)
        if room_name in st.session_state.placed_furniture:
            for furniture in st.session_state.placed_furniture[room_name]:
                x, y = furniture['position']
                width_px = furniture['width_pixels']
                height_px = furniture['height_pixels']
                
                try:
                    # Load furniture image
                    furn_img = Image.open(furniture['image_path']).convert('RGBA')
                    furn_img = furn_img.resize((int(width_px), int(height_px)), Image.Resampling.LANCZOS)
                    
                    # Paste furniture
                    overlay.paste(furn_img, (int(x), int(y)), furn_img)
                    
                    # Draw bounding box
                    draw.rectangle(
                        [x, y, x + width_px, y + height_px],
                        outline=(0, 255, 0, 255),
                        width=3
                    )
                    
                    # Label
                    label = f"{furniture['id']}. {furniture['name']}"
                    draw.text((x + 5, y + 5), label, fill=(0, 255, 0, 255))
                    
                except Exception as e:
                    # Fallback rectangle
                    draw.rectangle(
                        [x, y, x + width_px, y + height_px],
                        fill=(100, 150, 200, 150),
                        outline=(0, 255, 0, 255),
                        width=3
                    )
        
        pil_canvas = Image.alpha_composite(pil_canvas, overlay)
        return np.array(pil_canvas.convert('RGB'))
    
    def place_furniture_at_click(self, click_x, click_y, room_name, room_contour, scale=1.0):
        """Place furniture at clicked position (scale=1.0 means no scaling)"""
        if not st.session_state.selected_furniture:
            return False, "No furniture selected!"
        
        furn_data = st.session_state.selected_furniture['data']
        
        # Convert meters to pixels
        width_pixels = furn_data['width'] / self.pixel_to_meter_ratio
        height_pixels = furn_data['height'] / self.pixel_to_meter_ratio
        
        # Center furniture on click point
        x = click_x - width_pixels / 2
        y = click_y - height_pixels / 2
        
        # Check if furniture fits
        if not self.furniture_fits_in_room(x, y, width_pixels, height_pixels, room_contour):
            return False, f"❌ {furn_data['name']} doesn't fit at this position!"
        
        # Add furniture
        st.session_state.furniture_id_counter += 1
        furniture_item = {
            'id': st.session_state.furniture_id_counter,
            'name': furn_data['name'],
            'position': (int(x), int(y)),
            'width_pixels': width_pixels,
            'height_pixels': height_pixels,
            'width_meters': furn_data['width'],
            'height_meters': furn_data['height'],
            'image_path': furn_data['image_path']
        }
        
        # Initialize room list if needed
        if room_name not in st.session_state.placed_furniture:
            st.session_state.placed_furniture[room_name] = []
        
        st.session_state.placed_furniture[room_name].append(furniture_item)
        return True, f"✅ {furn_data['name']} placed!"
    
    def create_clickable_image(self, image, key):
        """Create an image with click detection using Streamlit components"""
        height, width = image.shape[:2]
        
        # Convert image to base64
        pil_img = Image.fromarray(image)
        buffered = BytesIO()
        pil_img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # HTML with JavaScript for click handling
        html_code = f"""
        <div id="image-container-{key}" style="position: relative; cursor: crosshair;">
            <img id="clickable-image-{key}" src="data:image/png;base64,{img_str}" 
                 style="width: 100%; border: 3px solid #2196F3; border-radius: 5px;">
            <div id="click-indicator-{key}" style="position: absolute; display: none; 
                 width: 20px; height: 20px; border: 3px solid red; border-radius: 50%; 
                 transform: translate(-50%, -50%); pointer-events: none;"></div>
        </div>
        <div id="coords-{key}" style="margin-top: 10px; padding: 10px; background: #e3f2fd; 
             border-radius: 5px; font-family: monospace;">
            Click on the image to place furniture | Last click: <span id="last-click-{key}">None</span>
        </div>
        <script>
            (function() {{
                const img = document.getElementById('clickable-image-{key}');
                const indicator = document.getElementById('click-indicator-{key}');
                const lastClick = document.getElementById('last-click-{key}');
                
                img.addEventListener('click', function(e) {{
                    const rect = img.getBoundingClientRect();
                    const scaleX = {width} / rect.width;
                    const scaleY = {height} / rect.height;
                    const x = Math.round((e.clientX - rect.left) * scaleX);
                    const y = Math.round((e.clientY - rect.top) * scaleY);
                    
                    // Show indicator
                    indicator.style.left = e.clientX - rect.left + 'px';
                    indicator.style.top = e.clientY - rect.top + 'px';
                    indicator.style.display = 'block';
                    
                    // Update display
                    lastClick.textContent = 'X=' + x + ', Y=' + y;
                    
                    // Send to Streamlit
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        key: '{key}',
                        value: {{x: x, y: y}}
                    }}, '*');
                }});
            }})();
        </script>
        """
        
        # Render component
        click_data = components.html(html_code, height=height + 80, scrolling=False)
        return click_data
    
    def save_layout(self):
        """Save the complete layout"""
        layout_data = {'rooms': {}}
        
        for room_name, furniture_list in st.session_state.placed_furniture.items():
            layout_data['rooms'][room_name] = [
                {
                    'id': f['id'],
                    'name': f['name'],
                    'position': f['position'],
                    'dimensions': {
                        'width_m': f['width_meters'],
                        'height_m': f['height_meters']
                    }
                }
                for f in furniture_list
            ]
        
        with open('furniture_layout.json', 'w') as f:
            json.dump(layout_data, f, indent=2)
        
        # Render complete floor plan with all furniture
        if st.session_state.floor_plan is not None:
            self.render_complete_floor_plan()
    
    def render_complete_floor_plan(self):
        """Render the complete floor plan with all placed furniture"""
        canvas = st.session_state.floor_plan.copy()
        pil_canvas = Image.fromarray(canvas).convert('RGBA')
        overlay = Image.new('RGBA', pil_canvas.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Draw all rooms and their furniture
        for room_name, room_data in st.session_state.rooms_info.items():
            # Draw room boundary
            contour = room_data['contour']
            points = [(int(pt[0][0]), int(pt[0][1])) for pt in contour]
            if len(points) > 2:
                draw.polygon(points, outline=(255, 255, 255, 150), width=2)
            
            # Draw furniture in this room (need to convert coordinates back to global)
            if room_name in st.session_state.placed_furniture:
                # Get room offset
                x, y, w, h = cv2.boundingRect(contour)
                x_offset = max(0, x - self.zoom_padding)
                y_offset = max(0, y - self.zoom_padding)
                
                for furniture in st.session_state.placed_furniture[room_name]:
                    fx, fy = furniture['position']
                    # Convert from room coordinates to global
                    global_x = fx + x_offset
                    global_y = fy + y_offset
                    
                    width_px = furniture['width_pixels']
                    height_px = furniture['height_pixels']
                    
                    try:
                        furn_img = Image.open(furniture['image_path']).convert('RGBA')
                        furn_img = furn_img.resize((int(width_px), int(height_px)), Image.Resampling.LANCZOS)
                        overlay.paste(furn_img, (int(global_x), int(global_y)), furn_img)
                        
                        draw.rectangle(
                            [global_x, global_y, global_x + width_px, global_y + height_px],
                            outline=(0, 255, 0, 200),
                            width=2
                        )
                    except:
                        pass
        
        pil_canvas = Image.alpha_composite(pil_canvas, overlay)
        final_image = np.array(pil_canvas.convert('RGB'))
        cv2.imwrite('furniture_layout.png', cv2.cvtColor(final_image, cv2.COLOR_RGB2BGR))
    
    def run(self):
        """Main application"""
        st.title("🏠 Room-by-Room Furniture Designer")
        st.markdown("### Select a room, click to place furniture, move to next room!")
        
        # Sidebar
        with st.sidebar:
            st.header("🎛️ Control Panel")
            
            # Load floor plan
            if st.button("📐 Load Floor Plan"):
                with st.spinner("Loading..."):
                    floor_plan, rooms_info = self.load_floor_plan()
                    if floor_plan is not None:
                        st.session_state.floor_plan = floor_plan
                        st.session_state.rooms_info = rooms_info
                        st.session_state.floor_plan_loaded = True
                        st.success("✅ Loaded!")
                        st.rerun()
            
            if st.session_state.floor_plan_loaded:
                st.markdown("---")
                
                # Room selection
                st.subheader("🚪 Select Room")
                room_names = list(st.session_state.rooms_info.keys())
                
                for room_name in room_names:
                    room_data = st.session_state.rooms_info[room_name]
                    furniture_count = len(st.session_state.placed_furniture.get(room_name, []))
                    
                    button_label = f"{room_data['type']} ({furniture_count} items)"
                    if st.button(button_label, key=f"room_{room_name}"):
                        st.session_state.current_room = room_name
                        # Extract room region
                        room_img, offset, contour, scale = self.extract_room_region(
                            st.session_state.floor_plan,
                            room_data
                        )
                        st.session_state.room_image = room_img
                        st.session_state.room_offset = offset
                        st.session_state.room_contour = contour
                        st.session_state.room_scale = scale
                        st.rerun()
                
                st.markdown("---")
                
                # Furniture selection (filtered by room type if room selected)
                st.subheader("🛋️ Select Furniture")
                
                furniture_data = self.load_furniture_data()
                
                # Group by category
                categories = {}
                for filename, data in furniture_data.items():
                    cat = data['category']
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append((filename, data))
                
                # Show relevant categories first if room selected
                if st.session_state.current_room:
                    room_type = st.session_state.rooms_info[st.session_state.current_room]['type']
                    st.caption(f"💡 Showing furniture for: {room_type}")
                
                for category, items in sorted(categories.items()):
                    with st.expander(f"📦 {category} ({len(items)})"):
                        for filename, data in sorted(items, key=lambda x: x[1]['name']):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.text(data['name'])
                                st.caption(f"{data['width']:.1f}m × {data['height']:.1f}m")
                            with col2:
                                if st.button("✓", key=f"sel_{filename}"):
                                    st.session_state.selected_furniture = {
                                        'filename': filename,
                                        'data': data
                                    }
                                    st.rerun()
                
                # Show selected furniture
                if st.session_state.selected_furniture:
                    furn = st.session_state.selected_furniture['data']
                    st.markdown(f"""
                    <div class="furniture-active">
                        <strong>✓ Selected:</strong><br>
                        {furn['name']}<br>
                        <small>{furn['width']:.1f}m × {furn['height']:.1f}m</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("✗ Deselect"):
                        st.session_state.selected_furniture = None
                        st.rerun()
                
                st.markdown("---")
                
                # Save and navigation
                st.subheader("💾 Actions")
                
                if st.button("💾 Save Complete Layout"):
                    self.save_layout()
                    st.success("✅ Layout saved!")
                
                total_items = sum(len(items) for items in st.session_state.placed_furniture.values())
                st.metric("Total Furniture", total_items)
                st.metric("Rooms Furnished", len(st.session_state.placed_furniture))
        
        # Main area
        if st.session_state.floor_plan_loaded:
            if st.session_state.current_room:
                # Show current room zoomed in
                room_name = st.session_state.current_room
                room_data = st.session_state.rooms_info[room_name]
                
                st.markdown(f"""
                <div class="room-selected">
                    <h3>🎯 Currently Editing: {room_name}</h3>
                    <p><strong>Type:</strong> {room_data['type']} | 
                       <strong>Area:</strong> {room_data['area_units']:.1f} m² | 
                       <strong>Size:</strong> {room_data['width_units']:.1f} × {room_data['height_units']:.1f} m</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Render room with furniture
                room_rendered = self.render_room_with_furniture(
                    st.session_state.room_image,
                    room_name,
                    st.session_state.room_contour,
                    st.session_state.room_offset,
                    st.session_state.room_scale
                )
                
                if st.session_state.selected_furniture:
                    furn = st.session_state.selected_furniture['data']
                    st.markdown(f"""
                    <div class="instruction-box">
                        <strong>� PLACE FURNITURE:</strong> 
                        <strong>{furn['name']}</strong> ({furn['width']:.1f}m × {furn['height']:.1f}m)
                        <br><small>Use the sliders below OR enter coordinates directly</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Simple placement interface with coordinates
                    col_x, col_y, col_btn = st.columns([2, 2, 1])
                    
                    height, width = room_rendered.shape[:2]
                    
                    with col_x:
                        place_x = st.number_input("X coordinate", 0, width, width//2, key=f"place_x_{room_name}")
                    with col_y:
                        place_y = st.number_input("Y coordinate", 0, height, height//2, key=f"place_y_{room_name}")
                    with col_btn:
                        st.write("")  # Spacing
                        st.write("")  # Spacing
                        if st.button("🎯 Place Here", key=f"place_btn_{room_name}"):
                            success, message = self.place_furniture_at_click(
                                place_x, place_y, room_name, st.session_state.room_contour,
                                st.session_state.room_scale
                            )
                            
                            if success:
                                st.success(message)
                                st.session_state.selected_furniture = None
                                # Refresh room image
                                room_img, offset, contour, scale = self.extract_room_region(
                                    st.session_state.floor_plan,
                                    room_data
                                )
                                st.session_state.room_image = room_img
                                st.session_state.room_scale = scale
                                st.rerun()
                            else:
                                st.error(message)
                else:
                    st.info("👈 Select furniture from the sidebar")
                
                # Display room image with furniture
                st.subheader(f"🖼️ {room_name} View")
                st.image(room_rendered, use_column_width=True, caption="Yellow boundary shows the room area")
                
                # Show placed furniture list in sidebar
                with st.sidebar:
                    st.markdown("---")
                    st.subheader(f"📋 Furniture in {room_name}")
                    
                    if room_name in st.session_state.placed_furniture and st.session_state.placed_furniture[room_name]:
                        for idx, furniture in enumerate(st.session_state.placed_furniture[room_name]):
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.text(f"{furniture['id']}. {furniture['name']}")
                            with col_b:
                                if st.button("🗑️", key=f"del_{room_name}_{furniture['id']}"):
                                    st.session_state.placed_furniture[room_name].pop(idx)
                                    st.rerun()
                    else:
                        st.info("No furniture yet")
                    
                    st.markdown("---")
                    if st.button("✓ Done with this room", key="done_room"):
                        st.session_state.current_room = None
                        st.session_state.selected_furniture = None
                        st.rerun()
            
            else:
                # Show overview
                st.markdown("""
                <div class="instruction-box">
                    <h3>👈 Select a room from the sidebar to start designing</h3>
                    <p>Each room can be designed individually. Click on a room name to zoom in and place furniture.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Show floor plan overview
                st.subheader("🗺️ Floor Plan Overview")
                st.image(st.session_state.floor_plan, use_column_width=True)
                
                # Show summary
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Rooms", len(st.session_state.rooms_info))
                
                with col2:
                    furnished_rooms = len(st.session_state.placed_furniture)
                    st.metric("Rooms Furnished", furnished_rooms)
                
                with col3:
                    total_items = sum(len(items) for items in st.session_state.placed_furniture.values())
                    st.metric("Total Furniture", total_items)
                
                # Show room list
                st.subheader("📊 Room Summary")
                for room_name, room_data in st.session_state.rooms_info.items():
                    furniture_count = len(st.session_state.placed_furniture.get(room_name, []))
                    status = "✅" if furniture_count > 0 else "⭕"
                    
                    with st.expander(f"{status} {room_name} - {room_data['type']} ({furniture_count} items)"):
                        st.write(f"**Area:** {room_data['area_units']:.1f} m²")
                        st.write(f"**Dimensions:** {room_data['width_units']:.1f} × {room_data['height_units']:.1f} m")
                        
                        if room_name in st.session_state.placed_furniture:
                            st.write("**Furniture:**")
                            for f in st.session_state.placed_furniture[room_name]:
                                st.write(f"• {f['id']}. {f['name']}")
        
        else:
            # Welcome screen
            st.markdown("""
            <div style='text-align: center; padding: 50px;'>
                <h2>Welcome to Room-by-Room Designer! 🏠</h2>
                <p style='font-size: 18px;'>
                    Click <strong>'Load Floor Plan'</strong> in the sidebar to begin
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                ### 📐 Step 1
                Load your floor plan
                """)
            
            with col2:
                st.markdown("""
                ### 🚪 Step 2
                Select a room to design
                """)
            
            with col3:
                st.markdown("""
                ### 🖱️ Step 3
                Click to place furniture
                """)

if __name__ == "__main__":
    app = RoomByRoomDesigner()
    app.run()
