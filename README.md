# Hybrid Floor Plan Generation

Capstone project. It generates furnished floor plans with a hybrid pipeline:

1. **CNN room segmentation** (DeepLabV3-ResNet50, 6 classes)
2. **Per-room LoRA diffusion generation** (FLUX.1-dev with a LoRA for each room type)
3. **Furniture detection** (Roboflow / YOLO)
4. **Rule-based furniture placement and integration**
5. **Spatial evaluation** (boundary violations, overlap, ERR, PSR, RCR)

## Repository layout

```
notebooks/                  Colab notebooks, one folder per pipeline stage
  01_segmentation/          roomClassifyCNN (training), room_inference
  02_lora_generation/       bedroom, living room, bathroom, toilet, hallway, master
  03_furniture_detection/   furniture_detection
  04_integration/           integration (FurnitureDetector, FurnitureMapper, EnhancedFurniturePlacer)
  05_evaluation/            furniture_polygon_eval
  pipelines/                full_pipeline (end to end), lora_inference_pipeline (stages 1-2)
  archive/                  older or alternate notebook versions
src/floor_planrules/        rule-based placement modules (room_analyzer, furniture_placer, ...)
apps/furniture_customization/  Streamlit app for interactive furniture placement
data/furniture_crops/       furniture crop images + furniture_measurements.json
docs/
  reports/                  phase reports (.docx/.pages) and research_paper.tex
  notes/                    markdown reports, fixes log, quick start
  scripts/                  python-docx generators for the reports
  figures/                  figures used in the paper and reports
papers/                     reference papers
```

## Running

The notebooks run on **Google Colab with a GPU**. They read data, model weights, and the
`floor_planrules` modules from Google Drive (`/content/drive/MyDrive/...`). Edit the path
config cell at the top of each notebook to match your Drive layout. Model weights (`*.pth`,
`*.safetensors`) are not stored in this repo.

Interactive placement app:

```bash
cd apps/furniture_customization
pip install -r requirements.txt
streamlit run interactive_furniture_app.py
```

Regenerate a report:

```bash
pip install python-docx
python docs/scripts/create_phase3_doc.py
```

Build the paper from `docs/reports/`. Figures resolve through `\graphicspath{{../figures/}}`.
