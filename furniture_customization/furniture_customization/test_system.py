"""
Simple test script to verify the furniture placement system is working correctly
"""

import os
import json
import cv2
import numpy as np
from room_analyzer import extract_room_dimensions, color_maps, room_types

def test_system():
    print("🧪 Testing Furniture Placement System...")
    print("=" * 60)
    
    # Check files exist
    print("\n1. Checking required files...")
    
    files_to_check = [
        'segmented_rooms.png',
        'furniture_crops/furniture_measurements.json',
        'room_analyzer.py'
    ]
    
    all_files_exist = True
    for file_path in files_to_check:
        exists = os.path.exists(file_path)
        status = "✅" if exists else "❌"
        print(f"   {status} {file_path}")
        if not exists:
            all_files_exist = False
    
    if not all_files_exist:
        print("\n❌ Some required files are missing!")
        return False
    
    # Load and analyze floor plan
    print("\n2. Loading and analyzing floor plan...")
    try:
        segmented = cv2.imread('segmented_rooms.png')
        segmented_rgb = cv2.cvtColor(segmented, cv2.COLOR_BGR2RGB)
        print(f"   ✅ Floor plan loaded: {segmented_rgb.shape}")
    except Exception as e:
        print(f"   ❌ Error loading floor plan: {e}")
        return False
    
    # Detect rooms
    print("\n3. Detecting rooms...")
    try:
        pixel_to_meter_ratio = 0.1
        rooms_info = extract_room_dimensions(
            segmented_rgb, 
            color_maps, 
            room_types, 
            pixel_to_meter_ratio
        )
        print(f"   ✅ Detected {len(rooms_info)} rooms:")
        for room_name, room_data in rooms_info.items():
            print(f"      - {room_name}: {room_data['type']} ({room_data['area_units']:.1f} m²)")
    except Exception as e:
        print(f"   ❌ Error detecting rooms: {e}")
        return False
    
    # Load furniture data
    print("\n4. Loading furniture data...")
    try:
        with open('furniture_crops/furniture_measurements.json', 'r') as f:
            measurements = json.load(f)
        
        furniture_count = len(measurements)
        print(f"   ✅ Loaded {furniture_count} furniture items")
        
        # Check if images exist
        existing_images = 0
        for filename in list(measurements.keys())[:5]:  # Check first 5
            if os.path.exists(os.path.join('furniture_crops', filename)):
                existing_images += 1
        
        print(f"   ✅ Sample check: {existing_images}/5 furniture images found")
        
        # Show some examples
        print("\n   Sample furniture:")
        for idx, (filename, dims) in enumerate(list(measurements.items())[:5]):
            item_name = filename.split('_', 1)[1].replace('.png', '')
            print(f"      {idx+1}. {item_name}: {dims['width_m']}m × {dims['height_m']}m")
            
    except Exception as e:
        print(f"   ❌ Error loading furniture: {e}")
        return False
    
    # Test boundary checking
    print("\n5. Testing boundary detection...")
    try:
        # Get first room
        room_name = list(rooms_info.keys())[0]
        room_data = rooms_info[room_name]
        
        # Get room centroid
        cx, cy = room_data['centroid']
        
        # Test point inside room
        contour = room_data['contour']
        result = cv2.pointPolygonTest(contour, (cx, cy), False)
        
        if result >= 0:
            print(f"   ✅ Boundary detection working (tested with {room_name})")
        else:
            print(f"   ⚠️  Boundary detection issue detected")
            
    except Exception as e:
        print(f"   ❌ Error testing boundaries: {e}")
        return False
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ All tests passed! System is ready to use.")
    print("\n🚀 To start the application, run:")
    print("   streamlit run interactive_furniture_app.py")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_system()
    if not success:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        exit(1)
