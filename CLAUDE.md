# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A capstone research project: hybrid floor plan generation that combines CNN room segmentation, per-room LoRA diffusion generation, YOLO furniture detection, and rule-based furniture placement. There is no package, build system, test suite, or linter. All code lives in **Google Colab notebooks** (`*.ipynb`) that run against data, model weights, and helper modules stored on Google Drive (`/content/drive/MyDrive/...`). The notebooks cannot run locally as written; to execute them, open them in Colab with a GPU and the expected Drive layout.

Layout: `notebooks/` (one subfolder per stage, plus `pipelines/` and `archive/`), `src/floor_planrules/` (placement modules), `apps/furniture_customization/` (Streamlit app), `data/furniture_crops/`, `docs/` (`reports/`, `notes/`, `scripts/`, `figures/`), and `papers/`. `docs/scripts/create_phase3_doc.py` and `create_chapter10_doc.py` generate the `.docx` reports into `docs/reports/` with `python-docx`. `research_paper.tex` finds its figures via `\graphicspath{{../figures/}}`. `notebooks/archive/` holds alternate versions of notebooks; the copies in the stage folders are canonical.

## Pipeline architecture

The stages, in order, with the notebook that owns each stage:

1. **Room segmentation**: `notebooks/01_segmentation/roomClassifyCNN.ipynb` trains a torchvision `deeplabv3_resnet50` with 6 classes (`background, bedroom, hallway, bathroom, living_room, empty_room`) on 512×512 inputs. The model is saved to `cnn_dataset/best_model_final_4.pth`. Masks are color-coded with a fixed `COLOR_MAP` (bedroom `[255,154,0]`, hallway `[50,99,155]`, bathroom `[0,155,255]`, living `[155,255,0]`, empty `[100,80,71]`). Downstream code relies on these exact RGB values to extract rooms, so keep them consistent across notebooks. `room_inference.ipynb` runs inference and room-dimension analysis.
2. **Per-room LoRA generation** (`notebooks/02_lora_generation/`): `bedroom_inference`, `living_room_inference`, `bathroom_inference`, `toilet_inference`, `hallway_inference`, and `master.ipynb` (all room types in one notebook). Each loads `black-forest-labs/FLUX.1-dev` (fp16) and adds a room-specific FLUX LoRA `.safetensors` from `outputs_<room>*/`. Note that the reports say "Stable Diffusion", but the code uses FLUX. Each notebook generates a furnished room image conditioned on the extracted room mask, then crops the room back out (`extract_<room>`).
3. **Furniture detection**: `notebooks/03_furniture_detection/furniture_detection.ipynb` uses the Roboflow `inference_sdk` (model `furniture-ya4pe/1`) to detect furniture and crop it to `furniture_crops/`. Real-world sizes come from `furniture_measurements.json` (copy in `data/furniture_crops/`).
4. **Integration and rule-based placement**: `notebooks/04_integration/integration.ipynb` holds `FurnitureDetector`, `FurnitureMapper` (the room↔furniture compatibility rules that filter hallucinations), and `EnhancedFurniturePlacer`. It combines the per-room generated images onto the segmented plan and places furniture. Detected items are drawn in green and rule-based items in yellow. It writes `placement_report.json` per output.
5. **Evaluation**: `notebooks/05_evaluation/furniture_polygon_eval.ipynb` computes spatial metrics from the output PNGs and placement reports: boundary violations, overlap, ERR (empty-room rate), PSR (placement success rate), and RCR (rule compliance rate).

`notebooks/pipelines/lora_inference_pipeline.ipynb` chains stages 1–2. `full_pipeline.ipynb` chains everything (`run_full_pipeline`, `run_batch_pipeline`) and inlines copies of the classes from the stage notebooks.

### `src/floor_planrules/` helper modules

The integration and full-pipeline notebooks add `/content/drive/MyDrive/floor_planrules` to `sys.path` and import `room_analyzer.extract_room_dimensions`, `furniture_definitions.load_furniture_prototypes`, and `furniture_placer.FurniturePlacer` from it. A copy lives in `src/floor_planrules/`, but the notebooks import the Drive copy, which may differ. Changes here must be uploaded to Drive to take effect.

### Placement invariants (from FIXES_APPLIED.md)

- Containment checks must test the whole furniture polygon (`room_polygon.buffer(2.0).contains(f_poly)`), not just its centroid.
- Furniture prototypes are copied, never `pop()`ed, so multiple rooms of the same type all get furniture.
- Room names match on base type (`"bedroom_1".split('_')[0]`), so numbered instances still receive detected furniture.

## Working with the notebooks

- Downloads from Colab arrive with `(1)`-style suffixes. Rename them to match the existing file and put them in the right stage folder. The class definitions are duplicated across `integration.ipynb` and `full_pipeline.ipynb`, so a fix in one may need to be mirrored in the other.
- Edit notebooks as JSON (`NotebookEdit`, or Python on `cell['source']`). Some cells in `full_pipeline.ipynb` have scrambled line order (for example, the Drive-mount cell), so check that a cell's code is valid before trusting it.
- Configuration lives at the top of each notebook as hard-coded Drive paths (a `CONFIG` cell in the pipeline notebooks). `full_pipeline.ipynb` also hard-codes a Roboflow API key.
