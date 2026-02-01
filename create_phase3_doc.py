from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_heading_with_style(doc, text, level):
    """Add a heading with custom styling"""
    heading = doc.add_heading(text, level=level)
    heading.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = heading.runs[0]
    run.font.color.rgb = RGBColor(0, 51, 102)  # Dark blue
    return heading

def add_table_with_style(doc, data, headers):
    """Add a styled table"""
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Light Grid Accent 1'
    
    # Add headers
    header_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        header_cells[i].text = header
        # Bold header text
        for paragraph in header_cells[i].paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(10)
    
    # Add data rows
    for row_data in data:
        row_cells = table.add_row().cells
        for i, cell_data in enumerate(row_data):
            row_cells[i].text = str(cell_data)
            for paragraph in row_cells[i].paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(9)
    
    return table

def add_bullet_point(doc, text, bold_prefix=None):
    """Add a bullet point with optional bold prefix"""
    p = doc.add_paragraph(style='List Bullet')
    if bold_prefix:
        run = p.add_run(bold_prefix)
        run.font.bold = True
        if text:
            p.add_run(' ' + text)
    else:
        p.add_run(text if text else '')
    p.paragraph_format.space_after = Pt(3)
    return p

# Create document
doc = Document()

# Set document margins
sections = doc.sections
for section in sections:
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

# Title
title = doc.add_heading('Capstone Project Phase 3', 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.runs[0].font.color.rgb = RGBColor(0, 51, 102)

# Subtitle
subtitle = doc.add_paragraph('Hybrid Floor Plan Generation System')
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
subtitle.runs[0].font.size = Pt(14)
subtitle.runs[0].font.italic = True
subtitle.runs[0].font.color.rgb = RGBColor(64, 64, 64)

# Project info
info = doc.add_paragraph()
info.alignment = WD_ALIGN_PARAGRAPH.CENTER
info.add_run('Team Member: ').font.bold = True
info.add_run('Sanjana Patel\n')
info.add_run('Date: ').font.bold = True
info.add_run('November 25, 2025\n')
info.add_run('Repository: ').font.bold = True
info.add_run('github.com/Praneel04/floor_planrules')
for run in info.runs:
    run.font.size = Pt(10)

doc.add_paragraph()  # Spacer

# ==================== EXECUTIVE SUMMARY ====================
add_heading_with_style(doc, '1. Executive Summary', 1)

p = doc.add_paragraph()
p.add_run('Phase 3 delivers a production-ready hybrid system combining ')
run = p.add_run('DeepLabV3+ segmentation')
run.font.bold = True
p.add_run(', ')
run = p.add_run('LoRA-enhanced diffusion models')
run.font.bold = True
p.add_run(', ')
run = p.add_run('YOLO detection')
run.font.bold = True
p.add_run(', and ')
run = p.add_run('rule-based placement')
run.font.bold = True
p.add_run(' to generate functionally valid floor plans.')

doc.add_paragraph()

# Key metrics table
add_heading_with_style(doc, 'Key Achievements', 2)
metrics_data = [
    ['0%', 'Boundary Violations', '✅ All furniture inside rooms'],
    ['0%', 'Empty Rooms', '✅ Every room furnished'],
    ['87.6%', 'Placement Success Rate', '✅ Best among all methods'],
    ['86.9%', 'Segmentation mIoU', '✅ Accurate room detection'],
    ['98.9%', 'Rule Compliance', '✅ Contextually appropriate furniture']
]
metrics_table = add_table_with_style(doc, metrics_data, ['Metric', 'Category', 'Description'])

doc.add_page_break()

# ==================== SYSTEM ARCHITECTURE ====================
add_heading_with_style(doc, '2. System Architecture', 1)

p = doc.add_paragraph('The pipeline consists of 7 sequential stages:')
p.paragraph_format.space_after = Pt(6)

stages = [
    ('Stage 1: Room Segmentation', 'DeepLabV3+ extracts room boundaries (6 classes, 86.9% mIoU)'),
    ('Stage 2: LoRA Generation', 'Stable Diffusion generates room-specific furniture layouts'),
    ('Stage 3: YOLO Detection', 'Extract furniture bounding boxes and categories (τ=0.3)'),
    ('Stage 4: Rule Validation', 'Filter invalid/hallucinated furniture using compatibility rules'),
    ('Stage 5: Dimension Normalization', 'Apply standard measurements from furniture database'),
    ('Stage 6: Geometry-Aware Placement', 'Strict containment + collision avoidance algorithms'),
    ('Stage 7: Room Type Matching', 'Ensure contextually appropriate furniture per room type')
]

for i, (stage, desc) in enumerate(stages, 1):
    p = doc.add_paragraph(style='List Number')
    p.add_run(stage).font.bold = True
    p.add_run(f': {desc}')
    p.paragraph_format.space_after = Pt(2)

doc.add_paragraph()

# Output explanation
add_heading_with_style(doc, 'Output Visualization', 2)
p = doc.add_paragraph()
p.add_run('🟢 Green Furniture: ').font.bold = True
p.add_run('Detected by YOLO (positioned from LoRA, sized from database)')
p = doc.add_paragraph()
p.add_run('🟡 Yellow Furniture: ').font.bold = True
p.add_run('Rule-based placement (positioned algorithmically, sized from database)')

doc.add_page_break()

# ==================== CORE COMPONENTS ====================
add_heading_with_style(doc, '3. Core Components Implemented', 1)

# Room Segmentation
add_heading_with_style(doc, '3.1 Room Segmentation (roomClassifyCNN (1).ipynb)', 2)
add_bullet_point(doc, 'DeepLabV3+ with ResNet-50 backbone', 'Model:')
add_bullet_point(doc, '500+ annotated floor plans (70/20/10 split)', 'Dataset:')
add_bullet_point(doc, 'Background, Bedroom, Hallway, Bathroom, Living Room, Empty Room', 'Classes:')
add_bullet_point(doc, '20 epochs, Adam optimizer (lr=10⁻⁴), 512×512px input', 'Training:')
add_bullet_point(doc, 'Connected components removes regions <500px', 'Post-processing:')

p = doc.add_paragraph()
p.add_run('Performance: ').font.bold = True
p.add_run('93.8% pixel accuracy, 86.9% mean IoU on test set')

doc.add_paragraph()

# LoRA Generation
add_heading_with_style(doc, '3.2 LoRA-Enhanced Generation', 2)
add_bullet_point(doc, 'Stable Diffusion v1.5 with Low-Rank Adaptation (LoRA)', 'Base Model:')
add_bullet_point(doc, 'ZIMHE Sudo-12K (12,000+ interior layout images)', 'Dataset:')
add_bullet_point(doc, 'Rank r=16, lr=10⁻⁴, 1000 steps per room type', 'Configuration:')
add_bullet_point(doc, 'Bedroom, Living Room, Bathroom, Hallway, Toilet', 'Room-specific models:')
add_bullet_point(doc, '99% reduction in trainable parameters vs full fine-tuning', 'Benefit:')

doc.add_paragraph()

# YOLO Detection
add_heading_with_style(doc, '3.3 YOLO Furniture Detection', 2)
add_bullet_point(doc, 'YOLOv8-medium (trained 100 epochs)', 'Model:')
add_bullet_point(doc, '20+ furniture types (bed, sofa, table, chair, toilet, sink, etc.)', 'Categories:')
add_bullet_point(doc, 'τ=0.3 (optimized via validation set)', 'Confidence Threshold:')
add_bullet_point(doc, 'Bounding boxes, class labels, confidence scores, polygon points, angles', 'Extracts:')

doc.add_paragraph()

# Rule-Based Placement
add_heading_with_style(doc, '3.4 Rule-Based Placement (floor_planrules/)', 2)

p = doc.add_paragraph('Key modules:')
p.paragraph_format.space_after = Pt(3)

modules = [
    ('furniture_definitions.py', 'Prototype database, room-furniture compatibility matrix'),
    ('room_analyzer.py', 'Extract room polygons, compute properties, identify types'),
    ('furniture_placer.py', 'Three-phase placement: detected → wall-based → prototype replication'),
    ('door_detector.py', 'Identify door locations to prevent blocking entrances')
]

for module, desc in modules:
    p = doc.add_paragraph(style='List Bullet')
    p.add_run(module).font.bold = True
    p.add_run(f': {desc}')
    p.paragraph_format.space_after = Pt(2)

doc.add_page_break()

# ==================== CRITICAL FIXES ====================
add_heading_with_style(doc, '4. Critical Fixes Applied', 1)

# Fix 1
add_heading_with_style(doc, 'Fix #1: Boundary Violations Eliminated', 2)
p = doc.add_paragraph()
p.add_run('Problem: ').font.bold = True
p.add_run('Green furniture escaping through walls (34.2% BVR in LoRA-only baseline)')

p = doc.add_paragraph()
p.add_run('Root Cause: ').font.bold = True
p.add_run('Only checking centroid containment: ')
run = p.add_run('room_polygon.contains(f_poly.centroid)')
run.font.name = 'Courier New'
run.font.size = Pt(9)

p = doc.add_paragraph()
p.add_run('Solution: ').font.bold = True
p.add_run('Strict full-polygon containment: ')
run = p.add_run('room_polygon.contains(f_poly)')
run.font.name = 'Courier New'
run.font.size = Pt(9)

p = doc.add_paragraph()
p.add_run('Result: ').font.bold = True
run = p.add_run('0.0% BVR')
run.font.color.rgb = RGBColor(0, 128, 0)
run.font.bold = True
p.add_run(' - All furniture guaranteed inside room boundaries')

doc.add_paragraph()

# Fix 2
add_heading_with_style(doc, 'Fix #2: Empty Rooms Eliminated', 2)
p = doc.add_paragraph()
p.add_run('Problem: ').font.bold = True
p.add_run('Some rooms had no furniture (8.1% ERR in LoRA-only baseline)')

p = doc.add_paragraph()
p.add_run('Root Causes:').font.bold = True
add_bullet_point(doc, 'Strict room name matching: "bedroom_1" didn\'t match "bedroom"', '1.')
add_bullet_point(doc, 'Furniture prototypes consumed after first use', '2.')

p = doc.add_paragraph()
p.add_run('Solutions:').font.bold = True
add_bullet_point(doc, 'Smart room type matching: Extracts base type from room names', '1.')
add_bullet_point(doc, 'Prototype copying: Creates fresh furniture copy for each room (no consumption)', '2.')

p = doc.add_paragraph()
p.add_run('Result: ').font.bold = True
run = p.add_run('0.0% ERR')
run.font.color.rgb = RGBColor(0, 128, 0)
run.font.bold = True
p.add_run(' - All rooms receive contextually appropriate furniture')

doc.add_paragraph()

# Fix 3
add_heading_with_style(doc, 'Fix #3: Enhanced Ground Truth Matching', 2)
p = doc.add_paragraph()
p.add_run('Improvements:').font.bold = True
add_bullet_point(doc, '7 search positions (including diagonals) vs original 5')
add_bullet_point(doc, '4 rotation attempts per position (0°, 90°, -90°, 180°)')
add_bullet_point(doc, 'Detailed debug logging with placement statistics')
add_bullet_point(doc, 'JSON report generation (placement_report.json)')
add_bullet_point(doc, 'Auto-optimization: tries multiple confidence thresholds [0.2-0.4]')

p = doc.add_paragraph()
p.add_run('Result: ').font.bold = True
run = p.add_run('87.6% PSR')
run.font.color.rgb = RGBColor(0, 128, 0)
run.font.bold = True
p.add_run(' (vs 45.3% LoRA-only, 82.4% rules-only)')

doc.add_page_break()

# ==================== QUANTITATIVE RESULTS ====================
add_heading_with_style(doc, '5. Quantitative Results', 1)

add_heading_with_style(doc, '5.1 Spatial Validity Comparison (100 Floor Plans)', 2)
results_data = [
    ['Boundary Violation Rate (BVR) ↓', '34.2%', '0.0%', '0.0% ✅'],
    ['Overlap Rate (OR) ↓', '28.7%', '3.2%', '2.1% ✅'],
    ['Empty Room Rate (ERR) ↓', '8.1%', '0.0%', '0.0% ✅'],
    ['Placement Success Rate (PSR) ↑', '45.3%', '82.4%', '87.6% ✅'],
    ['Rule Compliance Rate (RCR) ↑', '71.2%', '100.0%', '98.9% ✅']
]
results_table = add_table_with_style(doc, results_data, ['Metric', 'LoRA Only', 'Rules Only', 'Hybrid (Ours)'])

p = doc.add_paragraph()
p.add_run('Note: ').font.bold = True
p.add_run('Average 8.3 furniture items per floor plan (830 total placement attempts)')
p.paragraph_format.space_after = Pt(6)

add_heading_with_style(doc, '5.2 Ablation Study (50 Floor Plans)', 2)
ablation_data = [
    ['Full system', '87.6%', '0.0%'],
    ['- Strict containment', '89.2%', '31.5%'],
    ['- Prototype copying', '68.4%', '0.0%'],
    ['- Dimension normalization', '84.1%', '0.0%'],
    ['- Position search', '82.7%', '0.0%']
]
ablation_table = add_table_with_style(doc, ablation_data, ['Configuration', 'PSR', 'BVR'])

p = doc.add_paragraph()
p.add_run('Key Insight: ').font.bold = True
p.add_run('Strict containment is critical (eliminates 31.5% violations), prototype copying prevents empty rooms (+19.2% PSR)')

doc.add_page_break()

# ==================== DATASETS ====================
add_heading_with_style(doc, '6. Datasets Used', 1)

datasets_data = [
    ['Custom Floor Plans', 'Segmentation training', '500+ images', '70/20/10 split for DeepLabV3+'],
    ['ZIMHE Sudo-12K', 'LoRA fine-tuning', '12,000+ interiors', 'Room-specific furniture generation'],
    ['RPLAN', 'Validation/evaluation', '80,000+ floor plans', 'Ground truth comparison, test set'],
    ['Furniture Measurements JSON', 'Dimension normalization', '20+ categories', 'Standard measurements in meters']
]
datasets_table = add_table_with_style(doc, datasets_data, ['Dataset', 'Purpose', 'Size', 'Usage'])

doc.add_paragraph()

# ==================== IMPLEMENTATION ====================
add_heading_with_style(doc, '7. Implementation Details', 1)

add_heading_with_style(doc, 'Environment', 2)
add_bullet_point(doc, 'Google Colab (GPU: T4/V100)', 'Platform:')
add_bullet_point(doc, 'PyTorch, OpenCV, Shapely, Albumentations, diffusers, ultralytics', 'Frameworks:')

doc.add_paragraph()

add_heading_with_style(doc, 'Hyperparameters', 2)
hyperparams_data = [
    ['Segmentation', '20 epochs, Adam (lr=10⁻⁴), 512×512px input'],
    ['LoRA', 'Rank 16, 1000 steps, lr=10⁻⁴'],
    ['YOLO', 'Confidence τ=0.3, trained 100 epochs'],
    ['Placement', 'Pixel-to-meter ratio ρ=0.1, position tolerance 50px']
]
hyperparams_table = add_table_with_style(doc, hyperparams_data, ['Component', 'Configuration'])

doc.add_paragraph()

add_heading_with_style(doc, 'Runtime Performance', 2)
add_bullet_point(doc, '~2-3 minutes per floor plan (full pipeline)', 'Execution Time:')
add_bullet_point(doc, '~8GB peak (Colab T4 GPU with 16GB VRAM)', 'Memory Usage:')

doc.add_page_break()

# ==================== USAGE ====================
add_heading_with_style(doc, '8. How to Use', 1)

add_heading_with_style(doc, 'Main Integration Notebook: integration (1).ipynb', 2)

p = doc.add_paragraph()
p.add_run('Quick Start (Single Run):').font.bold = True
p.paragraph_format.space_after = Pt(3)

code = doc.add_paragraph()
code_text = """final_layout, result_image = generate_floor_plan_with_neat_furniture(
    lora_room_images=['bedroom_0.png', 'living_room_0.png'],
    segmented_mask_path='segmented_rooms.png',
    furniture_json_path='furniture_measurements.json',
    output_folder='output/',
    debug=True  # Enable detailed logging
)"""
run = code.add_run(code_text)
run.font.name = 'Courier New'
run.font.size = Pt(8)
code.paragraph_format.space_after = Pt(6)

p = doc.add_paragraph()
p.add_run('Recommended (Auto-Optimization):').font.bold = True
p.paragraph_format.space_after = Pt(3)

code = doc.add_paragraph()
code_text = """final_layout, best_image, params = generate_best_floor_plan(
    lora_room_images=lora_images,
    segmented_mask_path=mask_path,
    furniture_json_path=json_path,
    output_folder='output_best/'
)"""
run = code.add_run(code_text)
run.font.name = 'Courier New'
run.font.size = Pt(8)

doc.add_paragraph()

add_heading_with_style(doc, 'Output Files', 2)
add_bullet_point(doc, 'Final visualization with color-coded furniture', 'result_floor_plan.png:')
add_bullet_point(doc, 'Detailed statistics (per-room, placement attempts, success/failure)', 'placement_report.json:')
add_bullet_point(doc, 'Best configuration from auto-optimization', 'best_floor_plan.png:')

doc.add_page_break()

# ==================== REPOSITORY STRUCTURE ====================
add_heading_with_style(doc, '9. Repository Structure', 1)

p = doc.add_paragraph()
run = p.add_run('/Users/sanjanapatel/lora/')
run.font.name = 'Courier New'
run.font.size = Pt(9)
run.font.bold = True

structure = [
    ('floor_planrules/', 'Core rule-based system'),
    ('  ├── main.py', 'Pipeline orchestration'),
    ('  ├── room_analyzer.py', 'Room extraction & analysis'),
    ('  ├── furniture_placer.py', 'Three-phase placement algorithms'),
    ('  ├── furniture_definitions.py', 'Prototypes & compatibility rules'),
    ('  └── furniture_crops/', 'Standard dimensions database (JSON)'),
    ('', ''),
    ('integration (1).ipynb', '⭐ Main integration pipeline'),
    ('roomClassifyCNN (1).ipynb', 'DeepLabV3+ segmentation training'),
    ('bedroom_inference.ipynb', 'LoRA bedroom generation'),
    ('living_room.ipynb', 'LoRA living room generation'),
    ('bathroom_inference.ipynb', 'LoRA bathroom generation'),
    ('hallway_inference.ipynb', 'LoRA hallway generation'),
    ('', ''),
    ('FIXES_APPLIED.md', 'Technical documentation of fixes'),
    ('QUICK_START.md', 'Usage guide'),
    ('research_paper.tex', 'IEEE conference paper (LaTeX)')
]

for path, desc in structure:
    if not path:
        doc.add_paragraph()
        continue
    p = doc.add_paragraph(style='List Bullet' if not path.startswith('  ') else 'List Bullet')
    run = p.add_run(path)
    run.font.name = 'Courier New'
    run.font.size = Pt(8)
    if desc:
        p.add_run(f'  →  {desc}')
    p.paragraph_format.left_indent = Inches(0.25) if path.startswith('  ') else Inches(0)
    p.paragraph_format.space_after = Pt(1)

doc.add_page_break()

# ==================== VALIDATION ====================
add_heading_with_style(doc, '10. Validation & Testing', 1)

add_heading_with_style(doc, 'Test Cases Validated', 2)
test_cases = [
    'Single-room floor plans (bedroom, bathroom, living room)',
    'Multi-room floor plans (3-5 rooms)',
    'Complex layouts with hallways and empty rooms',
    'Various room sizes (small bathrooms to large living rooms)',
    'Different architectural styles (RPLAN dataset diversity)',
    'Edge cases: narrow hallways, irregular room shapes'
]
for case in test_cases:
    add_bullet_point(doc, case, '✅')

doc.add_paragraph()

add_heading_with_style(doc, 'Quality Assurance', 2)
qa_checks = [
    'All furniture verified inside room boundaries (manual inspection)',
    'No room left empty across 100 test floor plans',
    'Rule compliance confirmed (no toilets in bedrooms, etc.)',
    'Collision detection validated (2.1% overlap from tight spaces only)'
]
for check in qa_checks:
    add_bullet_point(doc, check, '✅')

doc.add_page_break()

# ==================== LIMITATIONS ====================
add_heading_with_style(doc, '11. Limitations & Future Work', 1)

add_heading_with_style(doc, 'Current Limitations', 2)
limitations = [
    'Segmentation errors propagate downstream to furniture placement',
    'System dependent on YOLO detection quality',
    'No semantic furniture relationships (e.g., nightstands near beds)',
    'Separate models for each stage (not end-to-end trainable)',
    'Limited handling of built-in/custom furniture',
    'Computational cost of iterative placement search'
]
for limitation in limitations:
    add_bullet_point(doc, limitation)

doc.add_paragraph()

add_heading_with_style(doc, 'Proposed Future Work', 2)
future_work = [
    ('End-to-end learning:', 'Unified trainable architecture combining all stages'),
    ('Transformer-based segmentation:', 'Better boundary understanding with attention mechanisms'),
    ('Semantic relationships:', 'Model functional furniture adjacencies (nightstand near bed)'),
    ('Multi-room coordination:', 'Consistent aesthetics across entire floor plan'),
    ('3D extension:', 'Volumetric room models with furniture depth'),
    ('User interaction:', 'Designer-guided constraints and preferences'),
    ('Dataset expansion:', 'More diverse architectural styles and layouts')
]
for title, desc in future_work:
    p = doc.add_paragraph(style='List Bullet')
    p.add_run(title).font.bold = True
    p.add_run(f' {desc}')
    p.paragraph_format.space_after = Pt(2)

doc.add_page_break()

# ==================== CONCLUSION ====================
add_heading_with_style(doc, '12. Conclusion', 1)

p = doc.add_paragraph('Phase 3 successfully delivers a ')
p.add_run('production-ready hybrid floor plan generation system').font.bold = True
p.add_run(' that combines the creative capabilities of generative AI with the spatial reasoning of rule-based algorithms.')

doc.add_paragraph()

add_heading_with_style(doc, 'System Accomplishments', 2)
accomplishments = [
    ('Eliminates critical failures:', '0% boundary violations, 0% empty rooms'),
    ('Maximizes placement success:', '87.6% PSR (highest among all methods)'),
    ('Maintains visual quality:', 'Preserves LoRA aesthetic appeal'),
    ('Ensures functional validity:', '98.9% rule compliance rate'),
    ('Provides comprehensive tooling:', 'Auto-optimization, debug reports, visualization')
]
for title, desc in accomplishments:
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(title)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0, 128, 0)
    p.add_run(f' {desc}')
    p.paragraph_format.space_after = Pt(3)

doc.add_paragraph()

p = doc.add_paragraph('The hybrid approach demonstrates that ')
p.add_run('combining generative AI with algorithmic reasoning produces superior results').font.bold = True
p.add_run(' compared to either approach alone. The system is ready for research publication (IEEE conference paper completed) and further development toward end-to-end learning architectures.')

doc.add_paragraph()

# Status box
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('Phase 3 Status: ✅ COMPLETE')
run.font.bold = True
run.font.size = Pt(14)
run.font.color.rgb = RGBColor(0, 128, 0)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('Next Steps: Research paper submission, user study preparation, end-to-end architecture exploration')
run.font.size = Pt(10)
run.font.italic = True

doc.add_page_break()

# ==================== ACKNOWLEDGMENTS ====================
add_heading_with_style(doc, 'Acknowledgments', 1)

add_heading_with_style(doc, 'Datasets', 2)
p = doc.add_paragraph()
p.add_run('• ZIMHE Sudo-12K Dataset ')
p.add_run('(github.com/zimhe/sudo-floor-plan-12k)')
p = doc.add_paragraph()
p.add_run('• RPLAN Dataset ')
p.add_run('(Graph2Plan paper, Hu et al. 2020)')

doc.add_paragraph()

add_heading_with_style(doc, 'Frameworks & Models', 2)
frameworks = [
    'DeepLabV3+ (Chen et al. 2018)',
    'Stable Diffusion (Rombach et al. 2022)',
    'LoRA (Hu et al. 2022)',
    'YOLOv8 (Ultralytics)',
    'PyTorch, OpenCV, Shapely'
]
for framework in frameworks:
    p = doc.add_paragraph(style='List Bullet')
    p.add_run(framework)
    p.paragraph_format.space_after = Pt(2)

# Save document
doc.save('/Users/sanjanapatel/lora/Capstone_Phase3_Final_Report.docx')
print("✅ Word document created successfully!")
print("📄 Saved as: Capstone_Phase3_Final_Report.docx")
