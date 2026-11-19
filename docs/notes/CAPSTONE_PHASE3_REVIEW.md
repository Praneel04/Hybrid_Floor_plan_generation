# Capstone Project Phase 3 - Final Implementation Review

**Project:** Hybrid Floor Plan Generation Using LoRA-Enhanced Diffusion Models with Rule-Based Furniture Placement  
**Team Member:** Sanjana Patel  
**Review Date:** November 25, 2025

---

## Executive Summary

Phase 3 successfully integrated semantic room segmentation, LoRA-based furniture generation, YOLO detection, and rule-based placement into a unified pipeline. The system generates functionally valid floor plans with **zero boundary violations**, **zero empty rooms**, and **87.6% placement success rate** across diverse room configurations.

---

## Introduction

The process of interior layout design is traditionally manual, time-consuming, and heavily reliant on human expertise. Automating this process offers significant advantages in architectural visualization, real estate planning, and rapid prototyping. However, most existing methods for interior layout generation either depend on rigid rule-based systems with limited adaptability or produce generative outputs that lack structural precision and spatial consistency.

Recent advancements in semantic segmentation architectures and diffusion-based generative models have enabled new possibilities in structured floorplan synthesis. Deep convolutional neural networks, particularly encoder-decoder architectures like DeepLabV3+, have demonstrated strong capability in extracting accurate room boundaries from floor plan images through multi-scale feature learning. Meanwhile, diffusion models—when fine-tuned using parameter-efficient methods such as Low-Rank Adaptation (LoRA)—enable contextually relevant and style-consistent furniture generation even with limited domain-specific training data. However, purely generative approaches often produce visually appealing but functionally invalid layouts, with furniture placed outside room boundaries or overlapping with other objects.

In this work, we present a **hybrid pipeline that combines semantic segmentation, generative AI, and rule-based spatial reasoning** for automated interior layout creation. The proposed framework accepts floor plan images as input and employs a multi-stage approach: (1) **DeepLabV3+ with ResNet-50 backbone** performs semantic segmentation to extract room boundaries across six room types (background, bedroom, hallway, bathroom, living room, empty room), achieving 86.9% mean IoU; (2) **LoRA-enhanced Stable Diffusion models** generate room-specific furniture layouts fine-tuned on the ZIMHE Sudo-12K dataset; (3) **YOLOv8 detection** extracts furniture information from generated images; (4) **rule-based validation** filters hallucinations using architectural design constraints; (5) **geometry-aware placement algorithms** ensure strict boundary containment and collision avoidance. This integration of structured reasoning with generative synthesis ensures both spatial coherence and visual realism—two properties rarely achieved simultaneously in prior work.

The major contributions of this work are as follows:

1. **A novel integration pipeline** combining CNN-based semantic segmentation with LoRA-enhanced diffusion models and rule-based spatial reasoning
2. **Strict boundary containment algorithms** ensuring furniture remains within room polygons through full-polygon validation (not just centroid checking)
3. **A furniture validation system** based on architectural design rules encoded in room-furniture compatibility matrices
4. **Adaptive placement strategies** with prototype replication to prevent empty rooms and smart room type matching for furniture distribution
5. **Comprehensive evaluation** demonstrating elimination of boundary violations (0% BVR), empty rooms (0% ERR), and 87.6% placement success rate across 100 diverse floor plans

The remainder of this document is organized as follows: Section 2 provides the system architecture overview. Section 3 details the core components including segmentation, LoRA generation, YOLO detection, and rule-based placement. Section 4 documents the critical fixes applied to resolve boundary violations, empty rooms, and ground truth matching issues. Section 5 presents quantitative results including spatial validity metrics, ablation studies, and perceptual quality analysis. Section 6 discusses datasets, implementation details, and experimental methodology. Sections 7-9 cover usage instructions, repository structure, and validation results. Finally, Sections 10-12 address limitations, future work, and conclusions.

---

## 1. Background and Problem Statement

### 1.1 Background

Interior layout design is an essential part of architectural planning, involving the creation of functional and visually appealing arrangements of rooms and furniture within a building layout. Traditionally, this process requires significant manual effort, domain expertise, and iterative design revisions. Architects and interior designers must interpret floor plan images, define room boundaries, and place appropriate furniture based on spatial constraints, functionality, aesthetic preferences, and building codes.

While several computer-aided design (CAD) tools exist, they still depend heavily on human input and lack automation in generating meaningful room layouts and furniture arrangements. Manual floor plan creation is time-consuming, often taking hours or days to produce a single complete design. Furthermore, the process requires specialized knowledge of architectural conventions, furniture dimensions, spatial ergonomics, and design principles that are not easily accessible to non-experts.

Recent advances in deep learning and generative AI have opened possibilities for automating parts of this process. Semantic segmentation models, particularly encoder-decoder architectures like DeepLabV3+, have demonstrated remarkable capability in extracting structured information from images. Diffusion models, especially when combined with parameter-efficient fine-tuning methods like Low-Rank Adaptation (LoRA), can generate highly realistic and contextually appropriate visual content. Object detection systems such as YOLO have achieved real-time performance with high accuracy in identifying and localizing objects within images.

However, most existing approaches focus on individual aspects of the problem in isolation. Pure generative methods can produce visually appealing layouts but often violate basic spatial constraints—furniture may float outside room boundaries, overlap with other objects, or be contextually inappropriate for the room type. Rule-based systems ensure geometric validity but produce deterministic, repetitive designs lacking visual diversity and aesthetic appeal. There is a critical gap in systems that can combine the creative capabilities of generative AI with the spatial reasoning required for functional floor plans.

### 1.2 Problem Statement

The challenge lies in developing an automated system capable of generating complete and realistic interior layouts—including accurate room segmentation and functionally valid furniture placement—directly from floor plan images.

Existing methods for floor plan generation and furniture placement exhibit the following critical limitations:

**Lack of Spatial Validity:** Many generative models produce visually appealing results but fail to maintain spatial consistency. Furniture items frequently extend beyond room boundaries, creating physically impossible layouts. In our baseline experiments, pure LoRA generation resulted in 34.2% boundary violation rate and 28.7% furniture overlap rate—rendering the outputs unusable for practical architectural applications.

**Empty Room Problem:** Generative approaches often fail to furnish all rooms uniformly. Some rooms receive multiple furniture items while others remain completely empty. This inconsistency stems from the stochastic nature of generation and lack of explicit room-aware distribution mechanisms. Our analysis showed 8.1% of rooms were left unfurnished using pure generative methods.

**Hallucination and Contextual Inappropriateness:** Diffusion models can generate contextually inappropriate objects—for example, placing toilets in bedrooms or beds in bathrooms. These "hallucinations" occur because the models lack explicit knowledge of architectural design rules and room-furniture compatibility constraints. Pure generative baselines achieved only 71.2% rule compliance.

**Inconsistent Furniture Dimensions:** Detected furniture from generative outputs often exhibits unrealistic size variations due to differences in image resolution, detection artifacts, and lack of standardization. Without dimension normalization, furniture pieces of the same type may vary dramatically in size within a single floor plan.

**Over-Dependence on Rules:** Traditional rule-based systems offer spatial validity but lack flexibility and aesthetic diversity. They produce deterministic placements that appear repetitive and fail to capture the creative variety seen in human-designed layouts. While achieving 100% rule compliance, pure rule-based methods show poor visual realism (FID score of 68.9) and extremely low diversity (0.089).

**Poor Ground Truth Matching:** Existing systems struggle to leverage layout information from generated images. Limited search strategies and rigid placement constraints result in low utilization of detected furniture positions, forcing excessive reliance on generic rule-based placement.

**Error Propagation:** In multi-stage pipelines, errors from early stages (e.g., room segmentation) cascade through the system, degrading final output quality. Misclassified rooms lead to incorrect furniture selection, and poor detection results force fallback to suboptimal placement strategies.

Hence, there is a critical need for a **hybrid system that combines the strengths of multiple paradigms**—semantic understanding from deep learning, creative generation from diffusion models, and spatial reasoning from rule-based algorithms—to produce floor plans that are simultaneously visually appealing and functionally valid.

### 1.3 Objectives

The main objective of this project is to design and implement a **hybrid deep learning pipeline** that automates the process of converting floor plan images into complete, functionally valid interior layouts with appropriate furniture placement. The system aims to achieve the following specific objectives:

**Objective 1: Accurate Room Segmentation**
- Extract semantic room boundaries from floor plan images using DeepLabV3+ with ResNet-50 backbone
- Classify rooms into six distinct types: background, bedroom, hallway, bathroom, living room, and empty room
- Achieve high segmentation accuracy (target: >85% mean IoU) through:
  - Transfer learning from ImageNet-pretrained ResNet-50
  - Multi-scale feature extraction via atrous spatial pyramid pooling (ASPP)
  - Data augmentation techniques (flips, rotations, scale variations)
  - Post-processing with connected component analysis to remove noise
- Produce clean, pixel-accurate room boundary polygons suitable for downstream furniture placement

**Objective 2: Context-Aware Furniture Generation**
- Generate room-specific furniture layouts using LoRA-enhanced Stable Diffusion models
- Fine-tune separate models for each room type on the ZIMHE Sudo-12K dataset (12,000+ interior images)
- Achieve parameter-efficient adaptation (99% reduction in trainable parameters) through low-rank matrix decomposition
- Produce diverse, aesthetically pleasing furniture arrangements that capture room-type-specific visual patterns
- Maintain consistency with architectural and interior design conventions

**Objective 3: Robust Furniture Detection**
- Extract furniture information from generated images using YOLOv8 object detection
- Detect 20+ furniture categories including beds, sofas, tables, chairs, fixtures, and appliances
- Obtain precise localization (bounding boxes, polygon points, orientation angles)
- Achieve high detection confidence through:
  - Extensive training on annotated floor plan datasets
  - Data augmentation (rotation, scaling, color jittering)
  - Optimal confidence threshold selection (τ=0.3) via validation experiments

**Objective 4: Rule-Based Validation and Filtering**
- Implement architectural design rules to validate detected furniture
- Encode room-furniture compatibility in explicit matrices (e.g., beds belong in bedrooms, not bathrooms)
- Filter generative model hallucinations before placement
- Ensure rule compliance rate >98% while maintaining placement flexibility

**Objective 5: Strict Spatial Validity**
- **Eliminate boundary violations:** Ensure 100% of furniture remains fully within room boundaries through strict polygon containment (not just centroid checking)
- **Prevent empty rooms:** Achieve 0% empty room rate through prototype replication and smart room type matching
- **Minimize overlaps:** Reduce furniture collision rate to <3% through collision detection algorithms
- **Maximize placement success:** Achieve >85% placement success rate through multi-position search and adaptive strategies

**Objective 6: Dimension Standardization**
- Normalize all furniture to standard real-world measurements (in meters)
- Maintain consistent furniture database with prototype dimensions
- Ensure realistic size relationships between different furniture types
- Prevent unrealistic size variations within the same furniture category

**Objective 7: Intelligent Placement Integration**
- Combine detected positions (from generative models) with rule-based wall placement
- Implement three-phase placement algorithm:
  - **Phase 1:** Detected position placement with 7-position search and 4 rotation attempts
  - **Phase 2:** Wall-based placement at 5 positions along sorted wall segments
  - **Phase 3:** Prototype replication to prevent empty rooms
- Achieve optimal balance between ground truth matching and spatial validity

**Objective 8: Comprehensive System Evaluation**
- Measure spatial validity through quantitative metrics: BVR, OR, ERR, PSR, RCR
- Assess visual quality through perceptual metrics: FID score, diversity score
- Conduct comparative evaluation against pure generative and pure rule-based baselines
- Demonstrate superior performance across all metrics

### 1.4 Scope of the Project

The proposed system focuses on **2D floor plan generation** and aims to automate interior layout creation from input floor plan images. The project scope encompasses:

**In-Scope Components:**

1. **Room Segmentation Pipeline**
   - DeepLabV3+ training on custom annotated dataset (500+ floor plans)
   - Six-class semantic segmentation (background, bedroom, hallway, bathroom, living room, empty room)
   - RGB color-coded ground truth masks with unique color per class
   - Connected component post-processing for noise removal
   - Polygon extraction for downstream geometric operations

2. **LoRA-Enhanced Generation**
   - Stable Diffusion v1.5 fine-tuning using Low-Rank Adaptation
   - Room-type-specific models trained on ZIMHE Sudo-12K dataset
   - Separate models for: bedroom, living room, bathroom, hallway, toilet
   - Parameter-efficient training (rank r=16, 1000 steps per room type)
   - Generation of diverse, contextually appropriate furniture layouts

3. **YOLO-Based Detection**
   - YOLOv8-medium training for 100 epochs on floor plan datasets
   - 20+ furniture categories including: bed, sofa, table, chair, desk, toilet, sink, bathtub, cabinet, etc.
   - Extraction of bounding boxes, confidence scores, polygon points, and orientation angles
   - Confidence threshold optimization via validation experiments

4. **Rule-Based Placement System**
   - Furniture prototype database with standard dimensions in meters
   - Room-furniture compatibility matrix encoding architectural rules
   - Three-phase placement algorithm with strict validation
   - Collision detection using Shapely polygon intersection
   - Wall-based placement with inward normal vector calculation
   - Prototype replication mechanism to prevent empty rooms

5. **Integration and Optimization**
   - End-to-end pipeline in `integration (1).ipynb`
   - Single-pass generation function with configurable parameters
   - Auto-optimization function trying multiple confidence thresholds
   - Debug mode with detailed logging and statistics
   - JSON report generation for placement analysis

6. **Evaluation Framework**
   - Spatial validity metrics: BVR, OR, ERR, PSR, RCR
   - Perceptual quality metrics: FID, LPIPS diversity
   - Ablation studies on key components
   - Comparative analysis with baselines (LoRA-only, rules-only)
   - Test set evaluation on 100 floor plans with 830 furniture items

7. **Datasets and Resources**
   - Custom floor plan dataset: 500+ images with pixel-level annotations
   - ZIMHE Sudo-12K: 12,000+ interior layout images for LoRA training
   - RPLAN: 80,000+ annotated floor plans for validation and ground truth
   - Furniture measurements JSON: standard dimensions for 20+ categories

**Out-of-Scope Limitations:**

This work explicitly **does not** cover:

- **3D Rendering:** System generates 2D floor plans only; no volumetric or 3D furniture models
- **Texture and Material Generation:** Focus is on layout and placement, not visual appearance details
- **Real-Time Interactive Editing:** System operates in batch mode; no live editing interface
- **Lighting and Rendering:** No photorealistic rendering or lighting simulation
- **Cost Estimation:** No material cost or budget calculations
- **Structural Engineering:** No load-bearing analysis or building code compliance beyond basic room-furniture rules
- **HVAC and Utilities:** No plumbing, electrical, or ventilation system design
- **Multi-Story Buildings:** Focus is on single-floor layouts
- **Outdoor Spaces:** System handles only interior rooms and furniture
- **Custom Furniture Design:** Uses standard furniture prototypes; no procedural furniture generation
- **User Preference Learning:** No personalization or style transfer based on user history

**Target Use Cases:**

The system is designed for:
- Rapid prototyping of floor plan layouts for architectural visualization
- Automated generation of multiple design alternatives for comparison
- Educational tools for teaching interior design principles
- Real estate visualization and virtual staging
- Research platform for studying hybrid AI architectures in spatial reasoning tasks

**Technical Environment:**

- Platform: Google Colab with T4/V100 GPU (16GB VRAM)
- Runtime: ~2-3 minutes per floor plan (full pipeline)
- Memory: ~8GB peak usage
- Frameworks: PyTorch, OpenCV, Shapely, Albumentations, diffusers, ultralytics

---

## 2. Literature Review and Related Work

### 2.1 Introduction

The automation of floor plan generation and interior layout synthesis is an emerging research domain integrating deep learning, semantic segmentation, generative modeling, and rule-based spatial reasoning. This chapter discusses existing work on semantic segmentation architectures, diffusion-based generative models, object detection systems, and furniture placement strategies, highlighting studies employing encoder-decoder networks (DeepLabV3+), parameter-efficient fine-tuning (LoRA), real-time object detectors (YOLO), and hybrid rule-based systems. Additionally, widely used datasets such as RPLAN, ZIMHE Sudo-12K, and custom annotated floor plan collections are reviewed for their relevance in large-scale training and evaluation.

The literature reveals a fundamental tension in automated floor plan generation: purely generative approaches produce visually appealing but spatially invalid layouts, while purely rule-based systems ensure geometric correctness but lack aesthetic diversity. This review examines how recent advances in multiple AI paradigms can be integrated to address this challenge.

### 2.2 Semantic Segmentation for Floor Plan Analysis

Automatic extraction of semantic and structural information from floor plans forms the foundation of intelligent interior layout generation. Traditional approaches relied on manual digitization or specialized CAD parsing tools, but deep learning has enabled end-to-end extraction directly from raster images.

**Deep Learning for Floor Plan Understanding**

Kim (2021) [1] proposed a deep learning-based automatic floor plan analysis technique capable of extracting vectorized indoor spatial information—room boundaries, walls, and junctions—from raster images. This work demonstrated the potential of AI-driven automation over traditional manual digitization methods, achieving significant time savings and reduced human error. The study employed convolutional architectures to identify structural elements and used post-processing algorithms to vectorize detected regions.

Knechtel et al. (2024) [2] advanced this research by introducing a self-constructing graph network combining CNNs with Graph Convolutional Networks for semantic floor plan segmentation. Their multi-task model predicted walls, doors, and room types, effectively capturing both local features (edges, corners) and global spatial dependencies (room adjacency, connectivity patterns). While graph-based approaches show promise for capturing structural relationships, they require explicit graph construction from images—adding computational overhead and potential error propagation.

**DeepLabV3+ for Architectural Image Segmentation**

Chen et al. (2018) [10] introduced DeepLabV3+, an encoder-decoder architecture with atrous spatial pyramid pooling (ASPP) that has become a state-of-the-art baseline for semantic segmentation tasks. The architecture addresses key challenges in floor plan analysis:

- **Multi-scale feature extraction:** Atrous convolutions with varying dilation rates capture both fine-grained boundaries and large room regions without increasing parameters
- **Encoder-decoder structure:** Low-level spatial details are recovered through skip connections, preserving boundary precision
- **Transfer learning:** Pre-training on ImageNet enables effective feature extraction even with limited domain-specific data

DeepLabV3+ has been successfully applied to medical image segmentation, autonomous driving, and satellite imagery analysis. Its strong performance on tasks requiring precise boundary delineation makes it particularly suitable for floor plan room segmentation, where accurate room boundaries are critical for downstream furniture placement.

**Our Approach: DeepLabV3+ with ResNet-50**

This project employs DeepLabV3+ with a ResNet-50 backbone for semantic room segmentation. Unlike graph-based methods that require explicit connectivity information, DeepLabV3+ operates directly on floor plan images, learning implicit spatial relationships through convolutional layers. The model classifies pixels into six semantic classes (background, bedroom, hallway, bathroom, living room, empty room) and produces clean polygon boundaries suitable for geometric operations. Post-processing with connected component analysis removes noise artifacts smaller than 500 pixels, ensuring robust room extraction.

### 2.3 Generative Models for Interior Design

**Diffusion Models and Latent Representations**

Rombach et al. (2022) [3] introduced Latent Diffusion Models (Stable Diffusion), demonstrating high-quality image synthesis with reduced computational requirements compared to pixel-space diffusion. By operating in a compressed latent space, Stable Diffusion achieves:

- Faster training and inference times
- Lower memory requirements
- Ability to generate high-resolution images (512×512 and beyond)
- Strong conditioning capabilities for text-to-image and image-to-image tasks

Stable Diffusion has been widely adopted for artistic generation, photo editing, and domain-specific synthesis tasks, including architectural visualization.

**AI-Driven Floor Plan Automation**

Nijhawan (2025) [4] demonstrated an AI-driven floor plan design pipeline integrating Stable Diffusion, ControlNet, and LoRA to automate the creation of architectural layouts from textual prompts. This work showed that diffusion models can be effectively adapted to specialized domains like architecture through:

- Text conditioning for specifying room types and styles
- ControlNet for preserving structural constraints during generation
- LoRA for parameter-efficient domain adaptation

However, Nijhawan's approach focused primarily on generating visually coherent layouts from prompts, without explicit validation of spatial feasibility or furniture placement accuracy.

**HouseDiffusion: Vector-Based Generation**

Shabani et al. (2022) [12] proposed HouseDiffusion, a vector floor plan generation pipeline using a diffusion process conditioned on layout graphs. Unlike raster-based systems, HouseDiffusion directly denoises 2D room corner coordinates, producing editable vector floor plans. This method demonstrated that diffusion models can be adapted beyond image generation to structured geometric output, setting a precedent for hybrid approaches combining generative and structural reasoning.

**Limitations of Pure Generative Approaches**

While diffusion models produce aesthetically pleasing layouts, they exhibit critical limitations for practical floor plan generation:

- **Spatial invalidity:** Furniture frequently extends beyond room boundaries or overlaps with other objects
- **Hallucinations:** Models generate contextually inappropriate items (e.g., toilets in bedrooms)
- **Inconsistent dimensions:** Same furniture type appears in varying, unrealistic sizes
- **Empty rooms:** Stochastic generation fails to ensure all rooms are furnished
- **Poor geometric reasoning:** Models lack explicit understanding of containment, collision, and clearance constraints

These limitations motivate the need for post-processing, validation, and rule-based refinement.

### 2.4 Parameter-Efficient Fine-Tuning with LoRA

**Low-Rank Adaptation Principles**

Hu et al. (2022) [5] introduced Low-Rank Adaptation (LoRA), enabling parameter-efficient fine-tuning of large pre-trained models. LoRA injects trainable low-rank matrices into attention layers:

```
W' = W + α · AB^T
```

where W is the frozen pre-trained weight, A and B are small trainable matrices (rank r << d), and α is a scaling factor. This approach:

- Reduces trainable parameters by over 99% compared to full fine-tuning
- Maintains generation quality comparable to full fine-tuning
- Enables multiple task-specific adaptations from a single base model
- Facilitates training on consumer GPUs with limited VRAM

**LoRA in Domain-Specific Generation**

LoRA has been successfully applied to various specialized domains:

- Natural language processing: Task-specific language models
- Character generation: Consistent character appearance across images
- Artistic styles: Style transfer and artistic rendering
- Scientific visualization: Medical imaging and satellite data

For interior design, LoRA enables learning room-type-specific visual patterns (e.g., bedroom furniture styles vs. bathroom fixtures) without requiring massive datasets or extensive computational resources.

**Our Approach: Room-Specific LoRA Models**

This project fine-tunes Stable Diffusion v1.5 using LoRA (rank r=16) on the ZIMHE Sudo-12K dataset, training separate models for each room type. Each LoRA module learns distinctive furniture arrangements, color schemes, and layout patterns appropriate for its target room category. This specialization ensures that generated furniture matches the functional and aesthetic expectations of each room type.

### 2.5 Object Detection in Floor Plans

**YOLO Architecture Evolution**

Redmon et al. (2016) [9] introduced YOLO (You Only Look Once), revolutionizing object detection through a single-stage, real-time architecture. Unlike two-stage detectors (R-CNN family), YOLO:

- Treats detection as a regression problem directly from image pixels to bounding boxes and class probabilities
- Achieves real-time performance (30+ FPS) suitable for interactive applications
- Provides end-to-end training without complex region proposal mechanisms

Subsequent YOLO versions (YOLOv2-v8) have improved accuracy, efficiency, and feature representation, making YOLO the de facto standard for real-time object detection across domains including autonomous vehicles, surveillance, and robotics.

**YOLO in Architectural Applications**

Object detection in architectural drawings and floor plans has evolved from specialized CAD parsing to deep learning-based approaches. YOLO variants have demonstrated strong performance in detecting furniture and architectural elements in floor plan images, providing:

- Bounding boxes for precise localization
- Class labels for furniture categorization (beds, sofas, tables, fixtures)
- Confidence scores for quality filtering
- Real-time inference enabling interactive design tools

**Our Approach: YOLOv8 for Furniture Detection**

This project employs YOLOv8-medium, trained for 100 epochs on annotated floor plan datasets with 20+ furniture categories. YOLOv8's improved architecture (C2f modules, anchor-free detection) provides:

- Higher accuracy compared to earlier YOLO versions
- Better handling of small objects (critical for furniture in floor plans)
- Robust performance across varying image resolutions
- Extraction of polygon boundary points (beyond bounding boxes) for precise placement

Detection confidence threshold τ=0.3 is selected through validation experiments, balancing recall (detecting valid furniture) and precision (avoiding false positives).

### 2.6 Furniture Layout Synthesis and Placement

**GAN-Based Furniture Generation**

Tanasra et al. (2023) [7] explored Conditional GAN architectures such as Pix2Pix and BicycleGAN for interior furnishing, learning mappings between unfurnished and furnished layouts. Their work demonstrated that adversarial training can produce realistic furniture arrangements that respect:

- Room boundaries and wall positions
- Spatial ergonomics and clearance requirements
- Aesthetic coherence and style consistency

Wan et al. (2022) [8] proposed an energy-efficient layout generation network (SD-GAN), employing a dual Pix2Pix model to optimize space allocation while considering building energy consumption. Their approach integrated sustainability metrics into the generation objective, showing that functional constraints can be incorporated into learned models.

**Limitations of Pure Learned Placement**

While GAN-based methods produce visually appealing layouts, they share limitations with diffusion models:

- Spatial infeasibility: Generated furniture frequently violates geometric constraints
- Training data requirements: Require large paired datasets of unfurnished/furnished layouts
- Mode collapse: Limited diversity in generated arrangements
- Black-box reasoning: Difficult to interpret or correct placement decisions

**Rule-Based Spatial Reasoning**

Traditional rule-based systems for furniture placement offer complementary strengths:

- **Guaranteed validity:** Explicit constraint checking ensures spatial feasibility
- **Domain knowledge integration:** Architectural and ergonomic rules encoded directly
- **Interpretability:** Placement decisions are traceable and modifiable
- **Deterministic behavior:** Predictable outcomes for critical applications

However, pure rule-based systems produce repetitive, aesthetically limited layouts lacking the diversity and creativity of human designers.

**Our Hybrid Approach**

This project combines the strengths of both paradigms through a three-phase placement algorithm:

1. **Detected Position Placement:** Uses YOLO-detected furniture positions from LoRA-generated images as placement hints, attempting 7 search positions × 4 rotation angles to find valid placements
2. **Wall-Based Rule Placement:** For furniture without valid detected positions, applies geometric reasoning to place items along walls at 5 positions per wall segment
3. **Prototype Replication:** Creates furniture copies (not consuming prototypes) to ensure all rooms receive appropriate furnishing

Strict validation ensures all placements satisfy:
- Full polygon containment within room boundaries (not just centroid)
- Collision-free arrangement (no overlaps with other furniture)
- Room-furniture compatibility (architectural design rules)

### 2.7 Datasets for Floor Plan Generation

**RPLAN Dataset**

Hu et al. (2020) [6] introduced the RPLAN dataset as part of the Graph2Plan system, containing 80,000+ annotated residential floor plans with:

- Room boundary polygons
- Room type labels (bedroom, bathroom, living room, kitchen, etc.)
- Door and window positions
- Furniture bounding boxes and categories

RPLAN has become a standard benchmark for floor plan generation research, enabling supervised training of segmentation models, layout graph networks, and evaluation of generated layouts against ground truth. Its large scale and diversity across architectural styles make it valuable for:

- Training segmentation models on varied room configurations
- Validating furniture placement against human-designed layouts
- Benchmarking generation quality through comparison with real floor plans

**ZIMHE Sudo-12K Dataset**

The ZIMHE Sudo-12K dataset [11] provides fine-grained interior and furniture layout examples, containing over 12,000 high-quality interior images with:

- Room-specific furniture arrangements
- Diverse furniture styles and configurations
- Varying room sizes and aspect ratios
- Multiple room types (bedrooms, living rooms, bathrooms, kitchens, etc.)

This dataset enables LoRA models to learn room-type-specific visual patterns including:

- Typical furniture groupings (e.g., bed + nightstands in bedrooms)
- Spatial density and arrangement styles
- Color schemes and aesthetic coherence
- Furniture scale relationships

**Custom Floor Plan Annotation**

This project employs a custom dataset of 500+ floor plan images annotated with pixel-level semantic labels across six room types. Each image is manually annotated with RGB color-coded masks:

- Background: (0, 0, 0) Black
- Bedroom: (255, 154, 0) Orange
- Hallway: (50, 99, 155) Purple
- Bathroom: (0, 155, 255) Blue
- Living Room: (155, 255, 0) Yellow
- Empty Room: (100, 80, 71) Brown

The dataset is split 70/20/10 for training/validation/testing, ensuring the segmentation model generalizes across diverse architectural styles, room sizes, and layout configurations.

**Furniture Measurements Database**

A curated JSON database provides standard furniture dimensions for 20+ categories based on ergonomic standards and common manufacturing sizes. This database enables dimension normalization, ensuring consistent furniture proportions across generated floor plans.

### 2.8 Research Gaps and Motivation

Existing literature addresses individual aspects of floor plan generation but exhibits critical gaps:

**Isolated Approaches:** Most work focuses on either structural understanding (segmentation) or visual generation (diffusion models), but not their integration. Systems that combine both paradigms in a unified pipeline are rare.

**Lack of Spatial Validation:** Generative models produce visually appealing but spatially invalid layouts. Few systems implement explicit geometric validation to ensure furniture containment, collision avoidance, and clearance constraints.

**Empty Room Problem:** Stochastic generation fails to guarantee complete furnishing. Research on adaptive strategies to prevent empty rooms (e.g., prototype replication, smart room type matching) is limited.

**Hallucination Filtering:** Generative models produce contextually inappropriate objects without explicit validation against architectural design rules. Integration of rule-based filtering with generative outputs remains underexplored.

**Dimension Inconsistency:** Detected furniture exhibits unrealistic size variations. Dimension normalization to standard measurements is not addressed in existing generative approaches.

**Limited Hybrid Systems:** While some work combines learning and rules, comprehensive systems integrating semantic segmentation, generative models, object detection, and rule-based spatial reasoning in a multi-stage pipeline are novel.

### 2.9 Conclusion

While CNNs excel at semantic understanding of floor plans, and diffusion models generate high-quality visuals, neither alone achieves both spatial validity and aesthetic quality. This motivates the proposed hybrid framework, combining:

- **DeepLabV3+ semantic segmentation** for accurate room boundary extraction
- **LoRA-enhanced Stable Diffusion** for room-specific, visually coherent furniture generation  
- **YOLOv8 object detection** for extracting furniture information from generated layouts
- **Rule-based validation and placement** for ensuring spatial feasibility and design rule compliance

Training DeepLabV3+ on custom annotated floor plans for structural segmentation, fine-tuning LoRA models on ZIMHE Sudo-12K for furniture generation, and validating against RPLAN ground truth bridges the gap between geometric precision and visual synthesis. This multi-paradigm integration advances toward fully automated, coherent interior layout generation that is simultaneously functional and aesthetically pleasing.

The literature review establishes that combining complementary AI approaches—each addressing different aspects of the problem—offers a promising path toward practical floor plan automation systems suitable for real-world architectural applications.

---

## 3. Project Requirements

The successful implementation of the hybrid floor plan generation system requires careful consideration of functional, technical, and operational requirements. This section outlines the comprehensive set of requirements that guided the system design and development, ensuring the final solution meets both research objectives and practical deployment constraints.

### 3.1 Functional Requirements

The system must accept floor plan images in standard raster formats (PNG, JPEG) as input and produce complete interior layouts with semantically labeled rooms and contextually appropriate furniture placements. This core functionality encompasses several critical capabilities that define the system's operational behavior.

**Semantic Room Segmentation:** The system must accurately identify and delineate distinct room regions from input floor plan images, classifying each pixel into one of six semantic categories: background (walls and structural elements), bedroom, hallway, bathroom, living room, and empty room. The segmentation must achieve a minimum mean Intersection over Union (mIoU) of 85% to ensure sufficient boundary precision for downstream furniture placement. Room boundaries must be extracted as polygon coordinates suitable for geometric operations including containment testing, area calculation, and collision detection. Small noise artifacts (regions smaller than 500 pixels) must be automatically filtered through connected component post-processing to produce clean, coherent room representations.

**Room-Specific Furniture Generation:** For each identified room, the system must generate contextually appropriate and visually coherent furniture layouts that align with the functional purpose of the room type. Bedroom layouts must include beds, nightstands, dressers, and storage furniture. Bathroom layouts must include fixtures such as toilets, sinks, bathtubs, and vanities. Living room layouts must include sofas, coffee tables, entertainment units, and seating arrangements. Hallway layouts should include minimal furniture appropriate for circulation spaces. The generated furniture must exhibit style consistency within each room and across the entire floor plan, avoiding abrupt aesthetic discontinuities. Generation must support multiple inference runs to provide layout diversity while maintaining contextual appropriateness.

**Furniture Detection and Localization:** The system must detect and localize individual furniture items within generated layout images, producing bounding box coordinates, class labels, and confidence scores for each detected object. The detection system must support a minimum of 20 distinct furniture categories including beds, sofas, tables, chairs, cabinets, fixtures, and appliances. Detection accuracy must achieve at least 80% average precision at IoU threshold 0.5 to ensure reliable furniture extraction. The system must extract polygon boundary points beyond rectangular bounding boxes to enable precise geometric placement operations. Confidence threshold filtering must be configurable to balance detection recall (capturing valid furniture) against precision (avoiding false positives).

**Rule-Based Furniture Validation:** The system must validate detected furniture against architectural design rules encoded in room-furniture compatibility matrices. Invalid or hallucinated furniture items—such as toilets appearing in bedrooms or beds in bathrooms—must be automatically filtered before placement. The validation system must enforce functional appropriateness, ensuring each room type receives furniture compatible with its intended use. Compatibility rules must be maintainable through external configuration (JSON or Python dictionaries) to allow domain experts to refine design constraints without modifying core algorithms.

**Spatial Validity Enforcement:** All furniture placements must satisfy strict geometric constraints to ensure physically realizable layouts. Every furniture item must be fully contained within its target room boundary, verified through complete polygon containment testing rather than simplified centroid-based checks. The system must detect and prevent furniture overlaps, ensuring collision-free arrangements with no geometric intersections between furniture polygons. Minimum clearance distances must be maintained between furniture items and between furniture and walls to ensure adequate circulation space and ergonomic accessibility. Boundary Violation Rate (BVR) must be reduced to 0%, meaning no furniture extends beyond room boundaries. Overlap Rate (OR) must be minimized to below 3%, allowing only minor acceptable overlaps that do not compromise functionality.

**Empty Room Prevention:** The system must ensure every identified room receives appropriate furniture, achieving an Empty Room Rate (ERR) of 0%. Adaptive placement strategies must be implemented to handle cases where initial furniture generation or rule-based placement fails to furnish all rooms. The system must support prototype furniture replication, creating additional furniture instances (without consuming limited prototypes) to distribute across empty rooms. Smart room type matching must prioritize placing furniture in rooms matching the furniture's design context (e.g., beds in bedrooms) while falling back to alternative compatible rooms when necessary. The placement algorithm must iterate through multiple strategies—detected positions, wall-based placement, and prototype replication—until all rooms are furnished or all strategies are exhausted.

**Dimension Normalization:** Detected furniture must be normalized to standard real-world dimensions based on ergonomic guidelines and common manufacturing sizes. A comprehensive furniture measurement database must define typical dimensions for each furniture category, including length, width, height, and acceptable variance ranges. The normalization process must scale detected furniture polygons proportionally to match standard dimensions while preserving aspect ratios and geometric relationships. Normalized dimensions ensure consistency across multiple floor plans and enable meaningful quantitative comparisons with ground truth layouts.

**Multi-Strategy Placement:** The furniture placement system must employ a hierarchical, multi-phase approach that balances generative hints with geometric reasoning. The first phase attempts placement at detected positions from generated images, searching through multiple rotation angles (0°, 90°, 180°, 270°) and nearby positions to find valid placements. The second phase applies wall-based placement rules for furniture without valid detected positions, positioning items along wall segments at predefined fractions (0.2, 0.4, 0.5, 0.6, 0.8) of wall length. The third phase replicates prototype furniture to ensure room coverage when initial strategies fail. Each phase must strictly validate placements against containment and collision constraints before accepting furniture positions.

### 3.2 Technical Requirements

The technical infrastructure must support the integration of multiple AI frameworks, efficient processing of high-resolution images, and scalable deployment across diverse computational environments.

**Deep Learning Framework Integration:** The system must integrate PyTorch for semantic segmentation and object detection workflows, providing GPU acceleration for model inference. DeepLabV3+ segmentation models require PyTorch 1.9 or higher with torchvision for pre-trained ResNet-50 backbones and model utilities. YOLOv8 detection requires Ultralytics library version 8.0 or higher for model loading, inference, and result processing. The Diffusers library (version 0.21 or higher) must be integrated for Stable Diffusion pipelines, LoRA weight loading, and inference management. All deep learning dependencies must support both CPU and CUDA-enabled GPU execution to accommodate varying hardware configurations.

**Computer Vision and Image Processing:** OpenCV (version 4.5 or higher) must be integrated for image I/O operations, color space conversions, geometric transformations, and visualization utilities. NumPy (version 1.21 or higher) provides the foundation for array operations, polygon representations, and numerical computations. Matplotlib (version 3.4 or higher) enables visualization of segmentation masks, detected furniture, and final floor plan outputs. The PIL/Pillow library must support image format conversions and interfacing between different frameworks' expected input formats.

**Geometric Reasoning Libraries:** Shapely (version 1.8 or higher) must provide robust polygon operations including containment testing, intersection detection, buffer operations, and geometric transformations. The library must support complex polygon geometries including holes and multi-part polygons that may arise from room segmentation. Efficient spatial indexing (R-trees) should be leveraged for accelerating collision detection across many furniture items. Geometric operations must handle edge cases including degenerate polygons, zero-area regions, and numerical precision issues.

**Pre-Trained Model Access:** The system must download and cache pre-trained model weights from established repositories. DeepLabV3+ ResNet-50 weights should be accessible from torchvision model zoo or Hugging Face Hub. Stable Diffusion v1.5 base weights must be downloadable from Hugging Face (runwayml/stable-diffusion-v1-5) or compatible mirrors. Room-specific LoRA weights must be stored locally or retrievable from cloud storage with appropriate version tracking. YOLOv8-medium weights should be automatically downloaded through Ultralytics API or pre-cached for offline inference.

**Data Management and Storage:** Training datasets must be organized with clear directory structures separating images, annotations, and metadata. Segmentation datasets require paired RGB images and corresponding label masks with consistent naming conventions. LoRA fine-tuning datasets must be organized by room type with sufficient examples per category (minimum 1,000 images per room type recommended). Furniture measurement databases must be maintained in JSON format with structured schemas defining dimensions, categories, and compatibility rules. Generated outputs and intermediate results must be stored with timestamped filenames to enable reproducibility and debugging.

**Computational Performance:** Segmentation inference must complete within 2 seconds per floor plan on GPU hardware (NVIDIA RTX 3060 or equivalent) to support interactive workflows. LoRA-enhanced diffusion generation should produce room layouts within 5-7 seconds per room on GPU, scaling linearly with the number of rooms. YOLO detection must process generated images in under 1 second per image to maintain pipeline throughput. End-to-end pipeline execution from input floor plan to final furnished layout must complete within 60 seconds for typical residential floor plans (4-8 rooms) on recommended hardware. CPU-only execution should complete within 5 minutes per floor plan to support deployment on standard workstations without dedicated GPUs.

**Memory Requirements:** GPU memory requirements must not exceed 8 GB VRAM during peak inference to ensure compatibility with mid-range consumer GPUs (RTX 3060, RTX 3070). Segmentation models must operate within 2 GB VRAM with batch size 1 at 512×512 input resolution. Diffusion models must fit within 6 GB VRAM including LoRA adapters for 512×512 generation. System RAM requirements should remain below 16 GB for full pipeline execution to accommodate standard development machines. Memory-efficient implementations must avoid unnecessary data copies and release intermediate tensors promptly after use.

### 3.3 Dataset Requirements

The effectiveness of the hybrid system depends critically on the quality, diversity, and scale of training and evaluation datasets across all pipeline stages.

**Segmentation Training Data:** A minimum of 500 manually annotated floor plan images must be collected with pixel-level semantic labels across six room categories. Annotations must use RGB color-coded masks with consistent color mappings (background: black, bedroom: orange, hallway: purple, bathroom: blue, living room: yellow, empty room: brown). The dataset must exhibit diversity in architectural styles (modern, traditional, apartment, house), room sizes (small, medium, large), layout configurations (open-plan, compartmentalized), and image sources (architectural drawings, real estate listings, CAD exports). Data must be split 70% training, 20% validation, 10% testing with stratified sampling to maintain class balance across splits.

**LoRA Fine-Tuning Data:** Room-specific furniture generation requires access to the ZIMHE Sudo-12K dataset containing over 12,000 high-quality interior images with diverse furniture arrangements. The dataset must include sufficient examples per room type (minimum 1,000 images per category) to learn distinctive furniture patterns, spatial densities, and aesthetic styles. Images should cover multiple furniture styles (modern, traditional, minimalist, luxury), room sizes, and furniture groupings. Image resolution must be at least 512×512 pixels to provide adequate detail for furniture recognition. Captions or metadata describing room types and furniture categories enhance conditioning capabilities during fine-tuning.

**Object Detection Training Data:** YOLOv8 training requires annotated images with bounding boxes for 20+ furniture categories. While pre-trained YOLO models provide strong initialization, domain-specific fine-tuning on floor plan imagery improves accuracy for architectural representations. A minimum of 2,000 annotated floor plan images with furniture bounding boxes should be collected or synthesized. Annotations must include class labels, bounding box coordinates in YOLO format (normalized center x, center y, width, height), and confidence scores for ambiguous instances. Category coverage must be balanced to avoid bias toward common furniture types.

**Validation and Ground Truth Data:** The RPLAN dataset with 80,000+ annotated residential floor plans provides ground truth for evaluating furniture placement against human-designed layouts. Ground truth annotations must include room boundaries, room type labels, furniture bounding boxes with categories, and polygon coordinates. Evaluation subsets should be curated to represent diverse layout complexities (small apartments to large houses), room counts (2-10 rooms), and furniture densities (minimalist to fully furnished). Consistent preprocessing (image normalization, resolution standardization) must be applied to ensure fair comparisons between generated and ground truth layouts.

**Furniture Measurement Standards:** A comprehensive database of standard furniture dimensions must be maintained based on ergonomic research and manufacturing standards. The database must define typical dimensions for 20+ furniture categories including beds (single, double, queen, king), tables (coffee, dining, side), seating (chairs, sofas, benches), storage (dressers, cabinets, shelves), and fixtures (toilets, sinks, bathtubs). Each category must specify length, width, height ranges and acceptable variance tolerances. Dimensional data should reference industry standards (ISO, ANSI) and ergonomic guidelines to ensure realistic and functional furniture sizes.

### 3.4 Evaluation and Quality Assurance Requirements

Rigorous evaluation methodologies must be established to validate system performance across spatial validity, perceptual quality, and functional appropriateness dimensions.

**Spatial Validity Metrics:** Boundary Violation Rate (BVR) must be measured as the percentage of furniture items with any portion extending beyond room boundaries, targeting 0% violation. Overlap Rate (OR) quantifies the percentage of furniture area involved in collisions with other furniture, targeting below 3%. Empty Room Rate (ERR) measures the percentage of rooms receiving no furniture, targeting 0%. Placement Success Rate (PSR) calculates the percentage of furniture items successfully placed satisfying all constraints, targeting above 85%. Room Coverage Rate (RCR) assesses the percentage of rooms receiving at least one furniture item, targeting above 98%. These metrics must be computed across diverse test sets (minimum 100 floor plans) to ensure statistical significance.

**Perceptual Quality Metrics:** Fréchet Inception Distance (FID) must be computed between generated furniture layouts and ground truth distributions to quantify visual realism, targeting scores below 50. Lower FID scores indicate closer alignment with real interior design patterns. Learned Perceptual Image Patch Similarity (LPIPS) should be calculated to assess visual diversity across multiple generated layouts for the same floor plan, with higher diversity scores indicating richer variation. Human evaluation studies must be conducted with a minimum of 25 participants (architects, interior designers, general users) rating generated layouts on realism (1-5 scale), aesthetic quality (1-5 scale), and functional appropriateness (1-5 scale). Mean ratings must exceed 3.5 across all dimensions to demonstrate practical usability.

**Ablation Study Requirements:** Controlled experiments must isolate the contribution of each pipeline component to overall system performance. Ablation conditions include: (1) LoRA generation only without rule-based placement, (2) rule-based placement only without LoRA generation, (3) no dimension normalization, (4) no empty room prevention strategies, (5) simplified centroid-based containment instead of full polygon checking. Each condition must be evaluated on the same test set (minimum 50 floor plans) to enable direct performance comparisons. Statistical significance testing (paired t-tests, p < 0.05) should validate that observed performance differences are not due to random variation.

**Robustness and Edge Case Testing:** The system must be tested on challenging scenarios including floor plans with irregular room shapes (L-shaped, curved boundaries), very small rooms (below 10 square meters), very large rooms (above 50 square meters), narrow hallways (width below 1.5 meters), and complex multi-room layouts (8+ rooms). Performance degradation on edge cases must be quantified and documented. The system should handle corrupted inputs gracefully, producing informative error messages rather than crashes. Boundary conditions such as empty floor plans, single-room layouts, and floor plans with no identifiable rooms must be tested to ensure stable behavior.

### 3.5 Deployment and Operational Requirements

The system must be deployable across various computational environments while maintaining usability for both researchers and end-users.

**Cross-Platform Compatibility:** The implementation must support execution on Linux (Ubuntu 20.04+), macOS (11.0+), and Windows 10/11 operating systems. Python 3.8 or higher must be the primary runtime environment with consistent behavior across platforms. Platform-specific dependencies (file path handling, display backends) must be abstracted to ensure portability. Docker containerization should be supported as an optional deployment method, providing a reproducible execution environment with all dependencies pre-installed.

**Hardware Flexibility:** The system must support execution on both GPU-accelerated systems (NVIDIA GPUs with CUDA 11.0+) and CPU-only environments. GPU execution should be automatic when available, with graceful fallback to CPU when GPUs are not detected. Multi-GPU support is not required for initial implementation but should not be architecturally precluded for future enhancement. Minimum system requirements must be documented: 16 GB RAM, 50 GB storage, and either NVIDIA GPU with 8 GB VRAM or modern CPU with 4+ cores.

**User Interface and Interaction:** For research purposes, Jupyter Notebook interfaces must be provided with clear cell-by-cell explanations, visualization outputs, and interactive parameter tuning. Command-line interfaces should support batch processing of multiple floor plans with configurable parameters (model paths, confidence thresholds, output directories). Output visualizations must clearly distinguish between detected furniture (green polygons) and rule-based furniture (yellow polygons) to facilitate debugging and analysis. Generated floor plans must be saved in standard image formats (PNG, JPEG) with optional JSON metadata containing furniture coordinates, room labels, and placement statistics.

**Documentation and Reproducibility:** Comprehensive documentation must include installation instructions, dependency lists, dataset preparation guidelines, model training procedures, inference scripts, and troubleshooting guides. Code must be modular with clear separation of concerns: segmentation, generation, detection, validation, and placement modules should be independently testable. Version control must track model checkpoints, configuration files, and code revisions to enable reproducibility of reported results. README files must provide quick-start examples enabling users to generate floor plans within 15 minutes of repository cloning.

**Maintenance and Extensibility:** The codebase must follow Python best practices including PEP 8 style guidelines, type hints, and docstring documentation. Module interfaces should be designed for extensibility, allowing researchers to swap segmentation models (U-Net, Mask R-CNN), generative models (DALL-E, Midjourney), or detection models (Faster R-CNN, RetinaNet) without rewriting core logic. Configuration files (JSON, YAML) should externalize hyperparameters, file paths, and model settings to avoid hardcoding values. Unit tests for geometric operations, validation logic, and placement algorithms should achieve at least 70% code coverage to ensure reliability during future modifications.

The comprehensive requirements outlined above guided all architectural decisions, implementation choices, and evaluation protocols throughout the project lifecycle. Meeting these requirements ensures the system achieves its research objectives while remaining practical for real-world deployment in architectural visualization and interior design applications.

---

## 4. Implementation and Pseudocode

This chapter provides detailed algorithmic descriptions and pseudocode for the core components of the hybrid floor plan generation system. The implementation spans multiple modules including semantic segmentation, generative furniture synthesis, object detection, validation, and rule-based placement. Each subsection presents the high-level algorithm structure, key data structures, and critical implementation details that enable the system to achieve zero boundary violations, zero empty rooms, and 87.6% placement success rate.

### 4.1 System Architecture and Data Flow

The implementation follows a seven-stage pipeline architecture where each stage transforms data and passes results to subsequent stages. Understanding the data flow is essential for comprehending the algorithmic interactions.

**Pipeline Data Flow:**

```
Stage 1: Room Segmentation
Input: Floor plan image (H × W × 3 RGB)
Output: Segmentation mask (H × W with class indices 0-5)
        Room metadata {room_name: {type, polygon, area, walls}}

Stage 2: LoRA-Enhanced Generation
Input: Segmentation mask, room metadata
Output: Generated furniture images per room (512 × 512 RGB per room)

Stage 3: YOLO Furniture Detection
Input: Generated furniture images
Output: Detected furniture list [(bbox, class, confidence, polygon)]

Stage 4: Rule-Based Validation
Input: Detected furniture, room types
Output: Validated furniture list (hallucinations filtered)

Stage 5: Dimension Normalization
Input: Validated furniture (pixel coordinates)
Output: Normalized furniture (metric dimensions)

Stage 6: Geometry-Aware Placement
Input: Normalized furniture, room polygons
Output: Placed furniture {room: [furniture with positions]}

Stage 7: Visualization and Export
Input: Placed furniture, segmentation mask
Output: Final floor plan image, JSON placement report
```

**Key Data Structures:**

```python
# Room representation
Room = {
    'type': str,              # 'bedroom', 'bathroom', 'living_room', etc.
    'class_idx': int,         # Segmentation class index (0-5)
    'color': [R, G, B],       # RGB color in mask
    'polygon': Polygon,       # Shapely polygon for geometric operations
    'contour': ndarray,       # OpenCV contour points
    'bounding_box': [(x,y)],  # Corner coordinates
    'area': float,            # Area in square meters
    'centroid': (x, y),       # Center point in pixels
    'walls': [((x1,y1), (x2,y2))],  # Wall segments
    'width': float,           # Width in meters
    'height': float           # Height in meters
}

# Furniture representation
Furniture = {
    'name': str,              # Furniture type ('bed', 'sofa', 'table', etc.)
    'width_m': float,         # Width in meters
    'height_m': float,        # Height in meters
    'width_px': float,        # Width in pixels
    'height_px': float,       # Height in pixels
    'position_px': (x, y),    # Placement position (center)
    'angle': float,           # Rotation angle in degrees
    'polygon': Polygon,       # Shapely polygon after placement
    'original_filename': str, # Source image filename
    'essential': bool         # Whether item is mandatory for room
}

# Detection result
DetectedItem = {
    'bbox': (x, y, w, h),     # Bounding box
    'class': str,             # Furniture class name
    'confidence': float,      # Detection confidence [0, 1]
    'polygon': [(x,y)],       # Boundary points
    'room_match': str         # Matched room name
}
```

### 4.2 Semantic Room Segmentation

The segmentation module employs DeepLabV3+ with ResNet-50 backbone to classify pixels into six semantic room categories. The implementation includes inference, post-processing, and polygon extraction.

**Algorithm 4.1: Room Segmentation and Extraction**

```
ALGORITHM: SegmentAndExtractRooms(image, model, pixel_to_meter_ratio)
INPUT: 
    image: RGB floor plan image (H × W × 3)
    model: Trained DeepLabV3+ model
    pixel_to_meter_ratio: Scale factor (default 0.1)
OUTPUT:
    rooms_info: Dictionary mapping room names to room properties
    segmented_mask: Color-coded segmentation mask

1. PREPROCESSING:
   image_normalized ← ResizeAndNormalize(image, target_size=512×512)
   // Apply ImageNet normalization: mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
   
2. MODEL INFERENCE:
   logits ← model.forward(image_normalized)  // Shape: (1, 6, H, W)
   predictions ← argmax(logits, dim=1)       // Shape: (1, H, W)
   
3. COLOR MAPPING:
   color_map ← {
       0: (0, 0, 0),           // Background - Black
       1: (255, 154, 0),       // Bedroom - Orange
       2: (50, 99, 155),       // Hallway - Purple
       3: (0, 155, 255),       // Bathroom - Blue
       4: (155, 255, 0),       // Living Room - Yellow
       5: (100, 80, 71)        // Empty Room - Brown
   }
   segmented_mask ← ApplyColorMap(predictions, color_map)
   
4. ROOM EXTRACTION:
   rooms_info ← {}
   FOR each class_idx in [1, 2, 3, 4, 5]:  // Skip background (0)
       color ← color_map[class_idx]
       mask ← (segmented_mask == color)
       
       // Connected component analysis
       num_components, labels ← ConnectedComponents(mask)
       
       FOR room_id in [1, 2, ..., num_components]:
           room_mask ← (labels == room_id)
           
           // Filter small noise artifacts
           IF area(room_mask) < 500 pixels:
               CONTINUE
           
           // Extract room properties
           room_props ← AnalyzeRoom(room_mask, pixel_to_meter_ratio)
           room_name ← f"{room_type[class_idx]}_{room_id}"
           rooms_info[room_name] ← room_props
   
   RETURN rooms_info, segmented_mask
```

**Algorithm 4.2: Room Property Analysis**

```
ALGORITHM: AnalyzeRoom(room_mask, pixel_to_meter_ratio)
INPUT:
    room_mask: Binary mask for single room (H × W)
    pixel_to_meter_ratio: Scale conversion factor
OUTPUT:
    room_properties: Dictionary with geometric properties

1. CONTOUR EXTRACTION:
   contours ← FindContours(room_mask, mode=EXTERNAL)
   main_contour ← contour with maximum area
   
2. AREA CALCULATION:
   area_pixels ← ContourArea(main_contour)
   area_meters ← area_pixels × (pixel_to_meter_ratio)²
   
3. BOUNDING BOX:
   rotated_rect ← MinAreaRect(main_contour)
   (cx, cy), (w, h), angle ← rotated_rect
   width_meters ← w × pixel_to_meter_ratio
   height_meters ← h × pixel_to_meter_ratio
   
4. POLYGON EXTRACTION:
   epsilon ← 0.02 × ArcLength(main_contour)
   polygon_approx ← ApproxPolyDP(main_contour, epsilon)
   bounding_box ← ExtractCorners(polygon_approx)
   
5. WALL SEGMENTATION:
   walls ← []
   FOR i ← 0 TO length(bounding_box) - 1:
       p1 ← bounding_box[i]
       p2 ← bounding_box[(i + 1) mod length(bounding_box)]
       walls.append((p1, p2))
   
   // Sort walls by length (longest first)
   walls ← SortByLength(walls, descending=True)
   
6. CENTROID:
   moments ← CalculateMoments(room_mask)
   centroid ← (moments['m10']/moments['m00'], moments['m01']/moments['m00'])
   
7. SHAPE CLASSIFICATION:
   aspect_ratio ← max(w, h) / min(w, h)
   num_corners ← length(polygon_approx)
   IF num_corners ≤ 4:
       shape ← "rectangular"
   ELSE IF num_corners ≤ 8:
       shape ← "polygonal"
   ELSE:
       shape ← "complex"
   
8. CONSTRUCT PROPERTIES:
   room_properties ← {
       'polygon': CreateShapelyPolygon(bounding_box),
       'contour': main_contour,
       'bounding_box': bounding_box,
       'area': area_meters,
       'width': width_meters,
       'height': height_meters,
       'centroid': centroid,
       'walls': walls,
       'aspect_ratio': aspect_ratio,
       'shape': shape
   }
   
   RETURN room_properties
```

### 4.3 LoRA-Enhanced Furniture Generation

The generative module employs Stable Diffusion v1.5 fine-tuned with LoRA adapters for room-specific furniture synthesis. Each room type has a dedicated LoRA model trained on the ZIMHE Sudo-12K dataset.

**Algorithm 4.3: Room-Specific Furniture Generation**

```
ALGORITHM: GenerateRoomFurniture(room_mask, room_type, lora_models)
INPUT:
    room_mask: Binary mask for target room (H × W)
    room_type: Room category ('bedroom', 'bathroom', 'living_room', etc.)
    lora_models: Dictionary mapping room types to LoRA weights
OUTPUT:
    generated_image: Furniture layout image (512 × 512 × 3)

1. LORA MODEL SELECTION:
   IF room_type in lora_models:
       lora_weights ← lora_models[room_type]
   ELSE:
       // Fallback to generic interior model
       lora_weights ← lora_models['default']
   
2. BASE MODEL LOADING:
   base_model ← Load("stable-diffusion-v1-5")
   pipeline ← StableDiffusionPipeline(base_model)
   pipeline ← pipeline.to("cuda" if GPU_available else "cpu")
   
3. LORA ADAPTER INJECTION:
   pipeline.load_lora_weights(lora_weights)
   // LoRA modifies attention layers: W' = W + α·AB^T
   // Rank r=16, scaling factor α tuned during training
   
4. PROMPT CONSTRUCTION:
   base_prompt ← GetRoomPrompt(room_type)
   // Examples:
   //   bedroom: "modern bedroom with bed, nightstands, dresser, warm lighting"
   //   bathroom: "contemporary bathroom with sink, bathtub, toilet, clean tiles"
   //   living_room: "cozy living room with sofa, coffee table, TV unit, plants"
   
5. MASK PREPROCESSING:
   room_mask_rgb ← ConvertToRGB(room_mask)
   room_mask_resized ← Resize(room_mask_rgb, (512, 512))
   
6. CONDITIONAL GENERATION:
   generation_params ← {
       'prompt': base_prompt,
       'negative_prompt': "blurry, distorted, overlapping furniture, text, watermark",
       'num_inference_steps': 50,
       'guidance_scale': 7.5,
       'width': 512,
       'height': 512,
       'seed': random_seed()
   }
   
   generated_image ← pipeline(**generation_params).images[0]
   
7. POST-PROCESSING:
   // Optional: Apply mask to constrain generation to room region
   IF use_masking:
       generated_image ← generated_image × room_mask_resized
   
   RETURN generated_image
```

**Algorithm 4.4: Batch Generation for Multi-Room Floor Plans**

```
ALGORITHM: GenerateAllRooms(rooms_info, lora_models)
INPUT:
    rooms_info: Dictionary of room metadata
    lora_models: LoRA weight paths per room type
OUTPUT:
    generated_rooms: Dictionary mapping room names to generated images

1. INITIALIZATION:
   generated_rooms ← {}
   
2. ROOM TYPE GROUPING:
   rooms_by_type ← GroupByType(rooms_info)
   // Batch rooms of same type for efficient GPU usage
   
3. FOR EACH room_type, room_list IN rooms_by_type:
       // Load LoRA model once per room type
       pipeline ← LoadPipelineWithLoRA(room_type, lora_models)
       
       FOR EACH room_name IN room_list:
           room_data ← rooms_info[room_name]
           
           // Generate furniture layout
           generated_image ← GenerateRoomFurniture(
               room_mask=room_data['polygon'],
               room_type=room_type,
               pipeline=pipeline
           )
           
           // Store result
           generated_rooms[room_name] ← generated_image
           
           // Save intermediate output for debugging
           IF debug_mode:
               SaveImage(generated_image, f"output/{room_name}_generated.png")
       
       // Release GPU memory
       UnloadPipeline(pipeline)
   
4. RETURN generated_rooms
```

### 4.4 YOLO-Based Furniture Detection

The detection module employs YOLOv8-medium to extract furniture items from generated images, producing bounding boxes, class labels, confidence scores, and polygon boundaries.

**Algorithm 4.5: Furniture Detection and Extraction**

```
ALGORITHM: DetectFurniture(generated_image, yolo_model, confidence_threshold)
INPUT:
    generated_image: Generated furniture layout (512 × 512 × 3)
    yolo_model: Trained YOLOv8-medium model
    confidence_threshold: Detection threshold τ (default 0.3)
OUTPUT:
    detected_furniture: List of detected furniture items

1. MODEL INFERENCE:
   results ← yolo_model.predict(
       source=generated_image,
       conf=confidence_threshold,
       iou=0.45,
       imgsz=512,
       verbose=False
   )
   
2. DETECTION EXTRACTION:
   detected_furniture ← []
   
   FOR EACH detection IN results[0].boxes:
       // Extract bounding box
       x1, y1, x2, y2 ← detection.xyxy[0]
       bbox_width ← x2 - x1
       bbox_height ← y2 - y1
       center_x ← (x1 + x2) / 2
       center_y ← (y1 + y2) / 2
       
       // Extract class and confidence
       class_id ← detection.cls[0]
       class_name ← yolo_model.names[class_id]
       confidence ← detection.conf[0]
       
       // Extract polygon points (if available)
       IF detection.masks is not None:
           mask ← detection.masks[0]
           contours ← FindContours(mask)
           polygon_points ← ApproxPolyDP(contours[0], epsilon=2.0)
       ELSE:
           // Fallback to rectangle
           polygon_points ← [
               (x1, y1), (x2, y1), (x2, y2), (x1, y2)
           ]
       
       // Create furniture detection object
       detected_item ← {
           'bbox': (center_x, center_y, bbox_width, bbox_height),
           'class': class_name,
           'confidence': confidence,
           'polygon': polygon_points,
           'original_detection': detection
       }
       
       detected_furniture.append(detected_item)
   
3. CONFIDENCE FILTERING:
   // Remove low-confidence detections
   detected_furniture ← [d for d in detected_furniture if d['confidence'] >= confidence_threshold]
   
4. NON-MAXIMUM SUPPRESSION:
   // Remove duplicate detections of same object
   detected_furniture ← NMS(detected_furniture, iou_threshold=0.45)
   
5. SIZE FILTERING:
   // Remove unreasonably small/large detections
   detected_furniture ← [d for d in detected_furniture 
                         if MIN_FURNITURE_SIZE < area(d['bbox']) < MAX_FURNITURE_SIZE]
   
   RETURN detected_furniture
```

**Algorithm 4.6: Room-Furniture Matching**

```
ALGORITHM: MatchFurnitureToRooms(detected_furniture, rooms_info, generated_rooms)
INPUT:
    detected_furniture: List of detected items per generated image
    rooms_info: Dictionary of room metadata
    generated_rooms: Mapping of room names to generated images
OUTPUT:
    matched_furniture: Dictionary mapping room names to furniture lists

1. INITIALIZATION:
   matched_furniture ← {room_name: [] for room_name in rooms_info.keys()}
   
2. FOR EACH room_name, generated_image IN generated_rooms:
       // Get furniture detected in this room's generated image
       furniture_in_image ← detected_furniture[room_name]
       
       // Smart room type matching
       room_type ← rooms_info[room_name]['type']
       room_base_type ← room_type.split('_')[0]  // "bedroom_1" → "bedroom"
       
       FOR EACH detected_item IN furniture_in_image:
           // Add room context to furniture item
           detected_item['source_room'] ← room_name
           detected_item['source_room_type'] ← room_base_type
           
           // Append to matched list
           matched_furniture[room_name].append(detected_item)
   
3. LOGGING:
   FOR EACH room_name, furniture_list IN matched_furniture:
       IF length(furniture_list) == 0:
           LogWarning(f"No furniture detected in {room_name}")
       ELSE:
           furniture_counts ← CountByClass(furniture_list)
           LogInfo(f"{room_name}: {furniture_counts}")
   
   RETURN matched_furniture
```

### 4.5 Rule-Based Validation and Filtering

The validation module applies architectural design rules to filter hallucinated or contextually inappropriate furniture before placement.

**Algorithm 4.7: Furniture Validation Against Design Rules**

```
ALGORITHM: ValidateFurniture(matched_furniture, compatibility_matrix)
INPUT:
    matched_furniture: Dictionary mapping rooms to furniture lists
    compatibility_matrix: Room-furniture compatibility rules
OUTPUT:
    validated_furniture: Filtered furniture passing validation

1. LOAD COMPATIBILITY RULES:
   // Example compatibility matrix:
   rules ← {
       'bedroom': ['bed', 'nightstand', 'dresser', 'desk', 'chair', 'wardrobe'],
       'bathroom': ['toilet', 'sink', 'bathtub', 'shower', 'vanity', 'cabinet'],
       'living_room': ['sofa', 'couch', 'table', 'tv', 'chair', 'shelf'],
       'hallway': ['table', 'shelf', 'chair', 'plant'],
       'empty_room': ['table', 'chair', 'shelf', 'storage']
   }
   
2. VALIDATION:
   validated_furniture ← {}
   validation_stats ← {'passed': 0, 'failed': 0, 'hallucinations': []}
   
   FOR EACH room_name, furniture_list IN matched_furniture:
       room_type ← GetRoomBaseType(room_name)  // "bedroom_1" → "bedroom"
       allowed_furniture ← rules.get(room_type, [])
       
       validated_list ← []
       
       FOR EACH furniture_item IN furniture_list:
           furniture_class ← furniture_item['class'].lower()
           
           // Fuzzy matching for furniture names
           is_compatible ← FALSE
           FOR EACH allowed_type IN allowed_furniture:
               IF allowed_type IN furniture_class OR furniture_class IN allowed_type:
                   is_compatible ← TRUE
                   BREAK
           
           IF is_compatible:
               validated_list.append(furniture_item)
               validation_stats['passed'] += 1
           ELSE:
               // Record hallucination
               validation_stats['failed'] += 1
               validation_stats['hallucinations'].append({
                   'room': room_name,
                   'furniture': furniture_class,
                   'reason': f"{furniture_class} not allowed in {room_type}"
               })
               
               IF debug_mode:
                   LogWarning(f"Filtered {furniture_class} from {room_name} (incompatible)")
       
       validated_furniture[room_name] ← validated_list
   
3. REPORT VALIDATION STATISTICS:
   success_rate ← validation_stats['passed'] / (validation_stats['passed'] + validation_stats['failed'])
   LogInfo(f"Validation: {validation_stats['passed']} passed, {validation_stats['failed']} filtered ({success_rate:.1%})")
   
   IF length(validation_stats['hallucinations']) > 0:
       LogInfo(f"Hallucinations detected: {validation_stats['hallucinations']}")
   
   RETURN validated_furniture, validation_stats
```

### 4.6 Dimension Normalization

The normalization module scales detected furniture to standard real-world dimensions based on an ergonomic measurement database.

**Algorithm 4.8: Furniture Dimension Normalization**

```
ALGORITHM: NormalizeDimensions(validated_furniture, measurement_database, pixel_to_meter_ratio)
INPUT:
    validated_furniture: Furniture items with pixel dimensions
    measurement_database: JSON with standard dimensions per category
    pixel_to_meter_ratio: Conversion factor (default 0.1)
OUTPUT:
    normalized_furniture: Furniture with metric dimensions

1. LOAD MEASUREMENT DATABASE:
   // Example database structure:
   standard_dims ← {
       'bed_queen': {'width_m': 1.52, 'height_m': 2.03},
       'bed_king': {'width_m': 1.93, 'height_m': 2.03},
       'bed_single': {'width_m': 0.91, 'height_m': 1.91},
       'sofa_3seat': {'width_m': 2.13, 'height_m': 0.91},
       'toilet': {'width_m': 0.46, 'height_m': 0.71},
       'sink': {'width_m': 0.51, 'height_m': 0.43},
       // ... 20+ categories
   }
   
2. NORMALIZATION:
   normalized_furniture ← {}
   
   FOR EACH room_name, furniture_list IN validated_furniture:
       normalized_list ← []
       
       FOR EACH furniture_item IN furniture_list:
           furniture_class ← furniture_item['class'].lower()
           
           // Find matching standard dimensions
           standard_key ← FindBestMatch(furniture_class, standard_dims.keys())
           
           IF standard_key is not None:
               standard_width ← standard_dims[standard_key]['width_m']
               standard_height ← standard_dims[standard_key]['height_m']
           ELSE:
               // Fallback: Use detected dimensions with conversion
               detected_width_px ← furniture_item['bbox'][2]
               detected_height_px ← furniture_item['bbox'][3]
               standard_width ← detected_width_px × pixel_to_meter_ratio
               standard_height ← detected_height_px × pixel_to_meter_ratio
               
               LogWarning(f"No standard dimensions for {furniture_class}, using detected size")
           
           // Create normalized furniture object
           normalized_item ← Furniture(
               name=furniture_class,
               width_m=standard_width,
               height_m=standard_height,
               original_filename=furniture_item.get('original_filename', 'generated')
           )
           
           // Convert to pixels for placement operations
           normalized_item.width_px ← standard_width / pixel_to_meter_ratio
           normalized_item.height_px ← standard_height / pixel_to_meter_ratio
           
           // Preserve detection metadata
           normalized_item.detected_position ← furniture_item['bbox'][:2]
           normalized_item.confidence ← furniture_item['confidence']
           normalized_item.source_room ← room_name
           
           normalized_list.append(normalized_item)
       
       normalized_furniture[room_name] ← normalized_list
   
3. LOGGING:
   FOR EACH room_name, furniture_list IN normalized_furniture:
       total_items ← length(furniture_list)
       normalized_count ← count items with standard dimensions
       LogInfo(f"{room_name}: {normalized_count}/{total_items} items normalized to standard sizes")
   
   RETURN normalized_furniture
```

### 4.7 Three-Phase Furniture Placement

The placement module implements a hierarchical strategy combining detected positions, wall-based rules, and prototype replication to achieve zero empty rooms and maximum placement success.

**Algorithm 4.9: Main Placement Orchestration**

```
ALGORITHM: PlaceAllFurniture(normalized_furniture, rooms_info, pixel_to_meter_ratio)
INPUT:
    normalized_furniture: Dictionary mapping rooms to furniture lists
    rooms_info: Room geometric properties
    pixel_to_meter_ratio: Scale conversion factor
OUTPUT:
    placed_furniture: Dictionary mapping rooms to placed furniture with positions

1. INITIALIZATION:
   placed_furniture ← {room_name: [] for room_name in rooms_info.keys()}
   placement_stats ← {
       'phase1_success': 0, 'phase1_fail': 0,
       'phase2_success': 0, 'phase2_fail': 0,
       'phase3_success': 0, 'phase3_fail': 0,
       'total_attempted': 0, 'total_placed': 0
   }
   
2. PHASE 1: DETECTED POSITION PLACEMENT
   FOR EACH room_name, furniture_list IN normalized_furniture:
       room_data ← rooms_info[room_name]
       room_polygon ← room_data['polygon']
       placed_in_room ← []
       placed_polygons ← []
       
       FOR EACH furniture_item IN furniture_list:
           placement_stats['total_attempted'] += 1
           
           // Try placement at detected position with search
           success, furniture_poly ← PlaceAtDetectedPosition(
               furniture=furniture_item,
               detected_pos=furniture_item.detected_position,
               room_polygon=room_polygon,
               placed_polygons=placed_polygons,
               search_radius=50,  // pixels
               rotation_angles=[0, 90, -90, 180]
           )
           
           IF success:
               placed_in_room.append(furniture_item)
               placed_polygons.append(furniture_poly)
               placement_stats['phase1_success'] += 1
               placement_stats['total_placed'] += 1
           ELSE:
               // Mark for Phase 2 processing
               furniture_item.phase1_failed ← TRUE
               placement_stats['phase1_fail'] += 1
       
       placed_furniture[room_name] ← placed_in_room
   
3. PHASE 2: WALL-BASED RULE PLACEMENT
   FOR EACH room_name, furniture_list IN normalized_furniture:
       room_data ← rooms_info[room_name]
       room_polygon ← room_data['polygon']
       walls ← room_data['walls']
       placed_in_room ← placed_furniture[room_name]
       placed_polygons ← [f.polygon for f in placed_in_room]
       
       // Get furniture that failed Phase 1
       unplaced_furniture ← [f for f in furniture_list if f.phase1_failed]
       
       FOR EACH furniture_item IN unplaced_furniture:
           // Try placement along walls
           success, furniture_poly ← PlaceAlongWalls(
               furniture=furniture_item,
               walls=walls,
               room_polygon=room_polygon,
               placed_polygons=placed_polygons,
               wall_positions=[0.2, 0.4, 0.5, 0.6, 0.8],  // Fractions of wall length
               rotation_angles=[0, 90, -90, 180]
           )
           
           IF success:
               placed_in_room.append(furniture_item)
               placed_polygons.append(furniture_poly)
               placement_stats['phase2_success'] += 1
               placement_stats['total_placed'] += 1
           ELSE:
               furniture_item.phase2_failed ← TRUE
               placement_stats['phase2_fail'] += 1
       
       placed_furniture[room_name] ← placed_in_room
   
4. PHASE 3: PROTOTYPE REPLICATION FOR EMPTY ROOMS
   empty_rooms ← [room for room, furn in placed_furniture.items() if length(furn) == 0]
   
   IF length(empty_rooms) > 0:
       LogWarning(f"Empty rooms detected: {empty_rooms}")
       
       FOR EACH empty_room IN empty_rooms:
           room_type ← rooms_info[empty_room]['type'].split('_')[0]
           
           // Get prototype furniture for this room type
           prototypes ← LoadPrototypes(room_type)
           
           // Try to replicate prototypes (not consuming originals)
           FOR EACH prototype IN prototypes:
               furniture_copy ← Furniture(
                   name=prototype.name,
                   width_m=prototype.width_m,
                   height_m=prototype.height_m,
                   original_filename=prototype.original_filename
               )
               furniture_copy.width_px ← prototype.width_px
               furniture_copy.height_px ← prototype.height_px
               
               // Try placement
               success, furniture_poly ← PlaceAlongWalls(
                   furniture=furniture_copy,
                   walls=rooms_info[empty_room]['walls'],
                   room_polygon=rooms_info[empty_room]['polygon'],
                   placed_polygons=[],
                   wall_positions=[0.2, 0.4, 0.5, 0.6, 0.8],
                   rotation_angles=[0, 90, -90, 180]
               )
               
               IF success:
                   placed_furniture[empty_room].append(furniture_copy)
                   placement_stats['phase3_success'] += 1
                   placement_stats['total_placed'] += 1
                   BREAK  // At least one item placed
               ELSE:
                   placement_stats['phase3_fail'] += 1
   
5. FINAL VALIDATION:
   // Verify no empty rooms remain
   final_empty_rooms ← [room for room, furn in placed_furniture.items() if length(furn) == 0]
   empty_room_rate ← length(final_empty_rooms) / length(rooms_info)
   
   // Calculate overall success rate
   psr ← placement_stats['total_placed'] / placement_stats['total_attempted']
   
   LogInfo(f"Placement Statistics:")
   LogInfo(f"  Phase 1 (Detected): {placement_stats['phase1_success']} placed")
   LogInfo(f"  Phase 2 (Wall-based): {placement_stats['phase2_success']} placed")
   LogInfo(f"  Phase 3 (Replication): {placement_stats['phase3_success']} placed")
   LogInfo(f"  Total PSR: {psr:.1%}")
   LogInfo(f"  Empty Room Rate: {empty_room_rate:.1%}")
   
   RETURN placed_furniture, placement_stats
```

**Algorithm 4.10: Detected Position Placement with Search**

```
ALGORITHM: PlaceAtDetectedPosition(furniture, detected_pos, room_polygon, placed_polygons, search_radius, rotation_angles)
INPUT:
    furniture: Furniture object to place
    detected_pos: (x, y) position from YOLO detection
    room_polygon: Shapely polygon for containment checking
    placed_polygons: List of already-placed furniture polygons
    search_radius: Search distance in pixels (default 50)
    rotation_angles: List of angles to try (default [0, 90, -90, 180])
OUTPUT:
    success: Boolean indicating placement success
    furniture_polygon: Shapely polygon of placed furniture (if successful)

1. DEFINE SEARCH POSITIONS:
   base_x, base_y ← detected_pos
   search_positions ← [
       (base_x, base_y),                          // Center
       (base_x - search_radius, base_y),          // Left
       (base_x + search_radius, base_y),          // Right
       (base_x, base_y - search_radius),          // Top
       (base_x, base_y + search_radius),          // Bottom
       (base_x - search_radius, base_y - search_radius),  // Top-left
       (base_x + search_radius, base_y + search_radius)   // Bottom-right
   ]
   
2. TRY ALL POSITION-ROTATION COMBINATIONS:
   FOR EACH position IN search_positions:
       FOR EACH angle IN rotation_angles:
           // Create furniture polygon at this position and rotation
           furniture_rect ← CreateRectangle(
               center=position,
               width=furniture.width_px,
               height=furniture.height_px
           )
           rotated_furniture ← Rotate(furniture_rect, angle, origin=position)
           
           // STRICT VALIDATION:
           // 1. Full polygon containment (not just centroid)
           IF NOT room_polygon.contains(rotated_furniture):
               CONTINUE
           
           // 2. Collision detection with existing furniture
           has_collision ← FALSE
           FOR EACH placed_poly IN placed_polygons:
               IF rotated_furniture.intersects(placed_poly):
                   overlap_area ← rotated_furniture.intersection(placed_poly).area
                   overlap_percentage ← overlap_area / rotated_furniture.area
                   
                   // Allow small overlaps (<3%)
                   IF overlap_percentage > 0.03:
                       has_collision ← TRUE
                       BREAK
           
           IF has_collision:
               CONTINUE
           
           // PLACEMENT SUCCESS
           furniture.position_px ← position
           furniture.angle ← angle
           furniture.polygon ← rotated_furniture
           
           RETURN TRUE, rotated_furniture
   
3. ALL ATTEMPTS FAILED:
   RETURN FALSE, None
```

**Algorithm 4.11: Wall-Based Rule Placement**

```
ALGORITHM: PlaceAlongWalls(furniture, walls, room_polygon, placed_polygons, wall_positions, rotation_angles)
INPUT:
    furniture: Furniture object to place
    walls: List of wall segments [(p1, p2), ...]
    room_polygon: Room boundary polygon
    placed_polygons: Existing furniture polygons
    wall_positions: Fractions of wall length to try [0.2, 0.4, 0.5, 0.6, 0.8]
    rotation_angles: Rotation angles to attempt
OUTPUT:
    success: Boolean indicating placement success
    furniture_polygon: Placed furniture polygon (if successful)

1. SORT WALLS BY LENGTH:
   walls ← SortByLength(walls, descending=True)
   // Prefer placing on longer walls
   
2. FOR EACH wall IN walls:
       wall_vector ← wall[1] - wall[0]
       wall_length ← ||wall_vector||
       wall_angle ← atan2(wall_vector.y, wall_vector.x) × 180 / π
       
       // Skip very short walls
       IF wall_length < furniture.width_px × 1.2:
           CONTINUE
       
       FOR EACH fraction IN wall_positions:
           // Calculate position along wall
           position ← wall[0] + fraction × wall_vector
           
           // Offset inward from wall to avoid boundary violation
           wall_normal ← Perpendicular(wall_vector)
           wall_normal ← Normalize(wall_normal)
           inward_offset ← max(furniture.width_px, furniture.height_px) / 2 + 10  // 10px buffer
           position ← position + inward_offset × wall_normal
           
           FOR EACH angle IN rotation_angles:
               // Create furniture polygon
               furniture_rect ← CreateRectangle(
                   center=position,
                   width=furniture.width_px,
                   height=furniture.height_px
               )
               
               // Align with wall angle
               total_angle ← wall_angle + angle
               rotated_furniture ← Rotate(furniture_rect, total_angle, origin=position)
               
               // STRICT VALIDATION:
               IF NOT room_polygon.contains(rotated_furniture):
                   CONTINUE
               
               has_collision ← FALSE
               FOR EACH placed_poly IN placed_polygons:
                   IF rotated_furniture.intersects(placed_poly):
                       overlap_area ← rotated_furniture.intersection(placed_poly).area
                       IF overlap_area / rotated_furniture.area > 0.03:
                           has_collision ← TRUE
                           BREAK
               
               IF has_collision:
                   CONTINUE
               
               // PLACEMENT SUCCESS
               furniture.position_px ← position
               furniture.angle ← total_angle
               furniture.polygon ← rotated_furniture
               
               RETURN TRUE, rotated_furniture
   
3. ALL WALLS EXHAUSTED:
   RETURN FALSE, None
```

### 4.8 Spatial Validity Metrics Computation

The evaluation module computes five key metrics to assess placement quality: Boundary Violation Rate (BVR), Overlap Rate (OR), Empty Room Rate (ERR), Placement Success Rate (PSR), and Room Coverage Rate (RCR).

**Algorithm 4.12: Spatial Validity Metrics**

```
ALGORITHM: ComputeSpatialMetrics(placed_furniture, rooms_info)
INPUT:
    placed_furniture: Dictionary mapping rooms to placed furniture
    rooms_info: Room geometric properties
OUTPUT:
    metrics: Dictionary with BVR, OR, ERR, PSR, RCR values

1. INITIALIZATION:
   total_furniture ← 0
   boundary_violations ← 0
   overlap_violations ← 0
   empty_rooms ← 0
   rooms_with_furniture ← 0
   total_rooms ← length(rooms_info)
   
2. BOUNDARY VIOLATION RATE (BVR):
   FOR EACH room_name, furniture_list IN placed_furniture:
       room_polygon ← rooms_info[room_name]['polygon']
       
       FOR EACH furniture IN furniture_list:
           total_furniture += 1
           
           // Check full polygon containment
           IF NOT room_polygon.contains(furniture.polygon):
               boundary_violations += 1
   
   BVR ← boundary_violations / total_furniture IF total_furniture > 0 ELSE 0
   
3. OVERLAP RATE (OR):
   total_overlap_area ← 0
   total_furniture_area ← 0
   
   FOR EACH room_name, furniture_list IN placed_furniture:
       FOR i ← 0 TO length(furniture_list) - 1:
           furniture_i ← furniture_list[i]
           total_furniture_area += furniture_i.polygon.area
           
           FOR j ← i+1 TO length(furniture_list) - 1:
               furniture_j ← furniture_list[j]
               
               IF furniture_i.polygon.intersects(furniture_j.polygon):
                   overlap_area ← furniture_i.polygon.intersection(furniture_j.polygon).area
                   total_overlap_area += overlap_area
   
   OR ← total_overlap_area / total_furniture_area IF total_furniture_area > 0 ELSE 0
   
4. EMPTY ROOM RATE (ERR):
   FOR EACH room_name, furniture_list IN placed_furniture:
       IF length(furniture_list) == 0:
           empty_rooms += 1
       ELSE:
           rooms_with_furniture += 1
   
   ERR ← empty_rooms / total_rooms
   
5. PLACEMENT SUCCESS RATE (PSR):
   // PSR is computed during placement as:
   // PSR = total_placed / total_attempted
   // Already available from placement_stats
   
6. ROOM COVERAGE RATE (RCR):
   RCR ← rooms_with_furniture / total_rooms
   
7. CONSTRUCT METRICS DICTIONARY:
   metrics ← {
       'BVR': BVR × 100,  // Convert to percentage
       'OR': OR × 100,
       'ERR': ERR × 100,
       'PSR': PSR × 100,
       'RCR': RCR × 100,
       'total_furniture': total_furniture,
       'boundary_violations': boundary_violations,
       'overlap_violations': overlap_violations,
       'empty_rooms': empty_rooms,
       'total_rooms': total_rooms
   }
   
8. LOGGING:
   LogInfo("Spatial Validity Metrics:")
   LogInfo(f"  BVR: {metrics['BVR']:.2f}% (target: 0%)")
   LogInfo(f"  OR: {metrics['OR']:.2f}% (target: <3%)")
   LogInfo(f"  ERR: {metrics['ERR']:.2f}% (target: 0%)")
   LogInfo(f"  PSR: {metrics['PSR']:.2f}% (target: >85%)")
   LogInfo(f"  RCR: {metrics['RCR']:.2f}% (target: >98%)")
   
   RETURN metrics
```

### 4.9 End-to-End Pipeline Integration

The integration module orchestrates all components into a unified pipeline with error handling, logging, and result export.

**Algorithm 4.13: Complete Floor Plan Generation Pipeline**

```
ALGORITHM: GenerateFloorPlanComplete(input_image_path, output_folder, config)
INPUT:
    input_image_path: Path to input floor plan image
    output_folder: Directory for output files
    config: Configuration dictionary with hyperparameters
OUTPUT:
    final_layout: Dictionary with all placement results
    result_image: Visualized floor plan with furniture
    metrics: Performance metrics dictionary

1. INITIALIZATION:
   CreateDirectory(output_folder)
   LogInfo(f"Starting floor plan generation: {input_image_path}")
   
2. STAGE 1: SEMANTIC SEGMENTATION
   LogInfo("Stage 1: Room Segmentation")
   input_image ← LoadImage(input_image_path)
   segmentation_model ← LoadDeepLabV3Plus(config['segmentation_model_path'])
   
   rooms_info, segmented_mask ← SegmentAndExtractRooms(
       image=input_image,
       model=segmentation_model,
       pixel_to_meter_ratio=config['pixel_to_meter_ratio']
   )
   
   SaveImage(segmented_mask, f"{output_folder}/segmented_mask.png")
   LogInfo(f"Detected {length(rooms_info)} rooms")
   
3. STAGE 2: LORA-ENHANCED GENERATION
   LogInfo("Stage 2: LoRA Furniture Generation")
   lora_models ← LoadLoRAModels(config['lora_weights_dir'])
   
   generated_rooms ← GenerateAllRooms(
       rooms_info=rooms_info,
       lora_models=lora_models
   )
   
   FOR EACH room_name, generated_image IN generated_rooms:
       SaveImage(generated_image, f"{output_folder}/{room_name}_generated.png")
   
   LogInfo(f"Generated furniture for {length(generated_rooms)} rooms")
   
4. STAGE 3: YOLO FURNITURE DETECTION
   LogInfo("Stage 3: Furniture Detection")
   yolo_model ← LoadYOLOv8(config['yolo_model_path'])
   
   detected_furniture ← {}
   FOR EACH room_name, generated_image IN generated_rooms:
       detected_furniture[room_name] ← DetectFurniture(
           generated_image=generated_image,
           yolo_model=yolo_model,
           confidence_threshold=config['confidence_threshold']
       )
   
   matched_furniture ← MatchFurnitureToRooms(
       detected_furniture=detected_furniture,
       rooms_info=rooms_info,
       generated_rooms=generated_rooms
   )
   
   total_detected ← sum(length(furn) for furn in matched_furniture.values())
   LogInfo(f"Detected {total_detected} furniture items")
   
5. STAGE 4: RULE-BASED VALIDATION
   LogInfo("Stage 4: Furniture Validation")
   compatibility_matrix ← LoadCompatibilityRules(config['rules_path'])
   
   validated_furniture, validation_stats ← ValidateFurniture(
       matched_furniture=matched_furniture,
       compatibility_matrix=compatibility_matrix
   )
   
   LogInfo(f"Validation: {validation_stats['passed']} passed, {validation_stats['failed']} filtered")
   
6. STAGE 5: DIMENSION NORMALIZATION
   LogInfo("Stage 5: Dimension Normalization")
   measurement_db ← LoadMeasurementDatabase(config['measurements_json'])
   
   normalized_furniture ← NormalizeDimensions(
       validated_furniture=validated_furniture,
       measurement_database=measurement_db,
       pixel_to_meter_ratio=config['pixel_to_meter_ratio']
   )
   
7. STAGE 6: THREE-PHASE PLACEMENT
   LogInfo("Stage 6: Furniture Placement")
   placed_furniture, placement_stats ← PlaceAllFurniture(
       normalized_furniture=normalized_furniture,
       rooms_info=rooms_info,
       pixel_to_meter_ratio=config['pixel_to_meter_ratio']
   )
   
   LogInfo(f"Placement: {placement_stats['total_placed']}/{placement_stats['total_attempted']} items")
   
8. STAGE 7: METRICS COMPUTATION
   LogInfo("Stage 7: Computing Metrics")
   metrics ← ComputeSpatialMetrics(
       placed_furniture=placed_furniture,
       rooms_info=rooms_info
   )
   
9. VISUALIZATION AND EXPORT:
   LogInfo("Generating visualization")
   result_image ← VisualizeFloorPlan(
       segmented_mask=segmented_mask,
       placed_furniture=placed_furniture,
       rooms_info=rooms_info,
       color_code={'detected': (0, 255, 0), 'rule_based': (255, 255, 0)}
   )
   
   SaveImage(result_image, f"{output_folder}/result_floor_plan.png")
   
   // Export placement report
   placement_report ← {
       'input_image': input_image_path,
       'rooms': rooms_info,
       'placed_furniture': placed_furniture,
       'placement_stats': placement_stats,
       'metrics': metrics,
       'config': config
   }
   
   SaveJSON(placement_report, f"{output_folder}/placement_report.json")
   
10. COMPLETION:
    LogInfo("Floor plan generation complete")
    LogInfo(f"Results saved to: {output_folder}")
    
    RETURN {
        'rooms_info': rooms_info,
        'placed_furniture': placed_furniture,
        'metrics': metrics,
        'result_image': result_image
    }
```

### 4.10 Complexity Analysis

The computational complexity of each pipeline stage affects overall system performance and scalability.

**Time Complexity:**

1. **Semantic Segmentation:** O(H × W × D)
   - H, W: Image dimensions (typically 512 × 512)
   - D: Network depth (ResNet-50 layers)
   - GPU inference: ~2 seconds per image

2. **LoRA Generation:** O(R × S × T)
   - R: Number of rooms (typically 4-8)
   - S: Inference steps (50 steps)
   - T: Time per denoising step (~0.1s)
   - Total: ~5-7 seconds per room

3. **YOLO Detection:** O(R × I)
   - R: Number of rooms
   - I: YOLO inference time per image (~0.5s)
   - Total: ~2-4 seconds for 4-8 rooms

4. **Validation:** O(F × C)
   - F: Total furniture items (typically 30-50)
   - C: Compatibility check cost (O(1))
   - Negligible: <0.1 seconds

5. **Placement:** O(F × P × A × V)
   - F: Furniture items
   - P: Search positions (7)
   - A: Rotation angles (4)
   - V: Validation cost (containment + collision)
   - Worst case: 5-10 seconds for 30-50 items

6. **Total Pipeline:** O(H × W × D + R × S × T + F × P × A × V)
   - Dominated by LoRA generation: ~30-60 seconds for typical floor plans

**Space Complexity:**

1. **Segmentation Model:** O(M) ≈ 100 MB (DeepLabV3+ weights)
2. **LoRA Models:** O(R × L) ≈ R × 5 MB per room type
3. **YOLO Model:** O(Y) ≈ 50 MB (YOLOv8-medium)
4. **Intermediate Data:** O(F × P) for furniture polygons
5. **Peak GPU Memory:** 6-8 GB VRAM during LoRA generation

**Scalability Considerations:**

- Linear scaling with number of rooms: O(R)
- Quadratic collision detection can be optimized with spatial indexing (R-trees)
- Batch processing of same room types reduces LoRA model loading overhead
- Potential parallelization of independent rooms for multi-GPU systems

This completes the implementation and pseudocode chapter, providing comprehensive algorithmic descriptions of all system components with concrete complexity analysis.

---

## 5. Project Architecture Overview

### Multi-Stage Pipeline

```
Input Floor Plan Image
    ↓
[1] DeepLabV3+ Segmentation → Room boundaries (86.9% mIoU)
    ↓
[2] LoRA Fine-tuned Stable Diffusion → Room-specific furniture layouts
    ↓
[3] YOLOv8 Detection → Extract furniture bounding boxes (τ=0.3)
    ↓
[4] Rule-Based Validation → Filter invalid/hallucinated furniture
    ↓
[5] Dimension Normalization → Apply standard furniture measurements
    ↓
[6] Geometry-Aware Placement → Strict containment + collision avoidance
    ↓
[7] Room Type Matching → Ensure contextually appropriate furniture
    ↓
Final Floor Plan (Green=Detected, Yellow=Rule-based)
```

---

## 2. Core Components Implemented

### 2.1 Room Segmentation (`roomClassifyCNN (1).ipynb`)

**Model:** DeepLabV3+ with ResNet-50 backbone  
**Classes:** 6 room types (Background, Bedroom, Hallway, Bathroom, Living Room, Empty Room)  
**Training:** 500+ annotated floor plans, 70/20/10 split, 20 epochs

**Color Mapping:**
- Background: `(0, 0, 0)` Black
- Bedroom: `(255, 154, 0)` Orange  
- Hallway: `(50, 99, 155)` Purple
- Bathroom: `(0, 155, 255)` Blue
- Living Room: `(155, 255, 0)` Yellow
- Empty Room: `(100, 80, 71)` Brown

**Post-Processing:** Connected component analysis removes regions <500px

**Performance:**
- Test Pixel Accuracy: **93.8%**
- Test Mean IoU: **86.9%**
- Best per-class: Background (95.8%), Bedroom (88.4%)

### 2.2 LoRA-Enhanced Generation

**Base Model:** Stable Diffusion v1.5  
**Dataset:** ZIMHE Sudo-12K (12,000+ interior layout images)  
**Configuration:** Rank r=16, learning rate 10⁻⁴, 1000 steps/room type

**Room-Specific Models:**
- `bedroom_inference.ipynb`: Bedroom furniture generation
- `living_room.ipynb`: Living room layouts
- `bathroom_inference.ipynb`: Bathroom fixtures
- `hallway_inference.ipynb`: Hallway furnishings
- `toilet_inference.ipynb`: Toilet room layouts

**Benefits:**
- 99% reduction in trainable parameters vs. full fine-tuning
- Room-specific visual patterns and furniture styles
- Diverse, aesthetically pleasing layouts

### 2.3 YOLO Furniture Detection

**Model:** YOLOv8-medium trained for 100 epochs  
**Categories:** 20+ furniture types (bed, sofa, table, chair, toilet, sink, etc.)  
**Confidence Threshold:** τ = 0.3 (optimized via validation)

**Extraction:**
- Bounding boxes: `(x, y, w, h)`
- Class labels and confidence scores
- Polygon boundary points
- Orientation angles

### 2.4 Rule-Based Furniture Placement (`floor_planrules/`)

**Key Modules:**

**`furniture_definitions.py`**
- Furniture prototype database with standard dimensions
- Room-furniture compatibility matrix
- Essential furniture rules (e.g., beds in bedrooms, toilets in bathrooms)

**`room_analyzer.py`**
- Extracts room polygons from segmentation masks
- Computes room properties (area, perimeter, wall segments)
- Identifies room types from color coding

**`furniture_placer.py`**
- **Phase 1:** Detected position placement with search
- **Phase 2:** Wall-based rule placement (5 positions per wall)
- **Phase 3:** Prototype replication to prevent empty rooms
- **Validation:** Strict polygon containment + collision detection

**`door_detector.py`**
- Identifies door locations for furniture clearance
- Prevents blocking entrances/exits

---

## 3. Critical Fixes Applied (Phase 3)

### Fix #1: Boundary Violations Eliminated ✅

**Problem:** Green furniture escaping through walls (34.2% BVR in LoRA-only baseline)

**Root Cause:** Only checking centroid containment
```python
# BAD: room_polygon.contains(f_poly.centroid)
```

**Solution:** Strict full-polygon containment in `_place_item_at_pos_strict()`
```python
# GOOD: room_polygon.contains(f_poly)
```

**Result:** **0.0% BVR** - All furniture guaranteed inside room boundaries

### Fix #2: Empty Rooms Eliminated ✅

**Problem:** Some rooms had no furniture (8.1% ERR in LoRA-only baseline)

**Root Causes:**
1. Strict room name matching: "bedroom_1" didn't match "bedroom"
2. Furniture prototypes consumed after first use: `prototypes.pop(0)`

**Solutions:**
1. **Smart room type matching:**
```python
room_base = room_name.split('_')[0]  # "bedroom_1" → "bedroom"
if room_base == room_type or room_type in room_name:
    detected_items.extend(furniture_list)
```

2. **Prototype copying instead of consuming:**
```python
# Create fresh copy for each room
furniture_copy = Furniture(
    name=prototype.name,
    width_m=prototype.width_m,
    height_m=prototype.height_m
)
```

**Result:** **0.0% ERR** - All rooms receive contextually appropriate furniture

### Fix #3: Enhanced Ground Truth Matching ✅

**Improvements:**
- 7 search positions (including diagonals) vs. original 5
- 4 rotation attempts per position (0°, 90°, -90°, 180°)
- Detailed debug logging with placement statistics
- JSON report generation (`placement_report.json`)
- Auto-optimization function tries multiple confidence thresholds

**Result:** **87.6% PSR** (vs 45.3% LoRA-only, 82.4% rules-only)

---

## 4. Integration Pipeline (`integration (1).ipynb`)

### Main Functions

**`generate_floor_plan_with_neat_furniture()`**
- Single-pass floor plan generation
- Configurable confidence threshold, pixel-to-meter ratio
- Debug mode with detailed logging
- Outputs: Final layout dict, visualized image, placement report

**`generate_best_floor_plan()` [RECOMMENDED]**
- Tries multiple YOLO confidence thresholds: [0.2, 0.25, 0.3, 0.35, 0.4]
- Selects configuration with highest detected furniture placement
- Auto-saves best result with parameters
- Useful for maximizing ground truth matching

### Visualization

**Color Coding:**
- 🟢 **Green furniture:** Detected by YOLO (positioned from LoRA, sized from JSON)
- 🟡 **Yellow furniture:** Rule-based placement (positioned algorithmically, sized from JSON)

**Output Files:**
- `{output_folder}/result_floor_plan.png`: Final visualization
- `{output_folder}/placement_report.json`: Detailed statistics
- `{output_folder}/best_floor_plan.png`: Best from auto-optimization

---

## 5. Quantitative Results

### Spatial Validity Comparison (100 Floor Plans)

| Metric | LoRA Only | Rules Only | Hybrid (Ours) |
|--------|-----------|------------|---------------|
| **Boundary Violation Rate (BVR)** ↓ | 34.2% | 0.0% | **0.0%** ✅ |
| **Overlap Rate (OR)** ↓ | 28.7% | 3.2% | **2.1%** ✅ |
| **Empty Room Rate (ERR)** ↓ | 8.1% | 0.0% | **0.0%** ✅ |
| **Placement Success Rate (PSR)** ↑ | 45.3% | 82.4% | **87.6%** ✅ |
| **Rule Compliance Rate (RCR)** ↑ | 71.2% | 100.0% | **98.9%** ✅ |

**Average:** 8.3 furniture items per floor plan (830 total placement attempts)

### Ablation Study (50 Floor Plans)

| Configuration | PSR | BVR |
|---------------|-----|-----|
| **Full system** | **87.6%** | **0.0%** |
| - Strict containment | 89.2% | 31.5% |
| - Prototype copying | 68.4% | 0.0% |
| - Dimension normalization | 84.1% | 0.0% |
| - Position search | 82.7% | 0.0% |

**Key Insight:** Strict containment is critical (eliminates 31.5% violations), prototype copying prevents empty rooms (+19.2% PSR)

---

## 6. Key Achievements

### Technical Accomplishments
✅ Zero boundary violations through strict polygon containment  
✅ Zero empty rooms via prototype copying and smart room matching  
✅ 87.6% placement success rate (highest among all methods)  
✅ Rule-based validation filters generative model hallucinations  
✅ Dimension normalization ensures consistent furniture sizing  
✅ Multi-position search improves ground truth alignment  

### System Capabilities
✅ Handles diverse room types (6 classes)  
✅ Supports 20+ furniture categories  
✅ Processes multiple room instances per floor plan  
✅ Auto-optimization for best results  
✅ Comprehensive debug reporting  
✅ Flexible pixel-to-meter scaling  

---

## 7. Datasets Used

| Dataset | Purpose | Size | Usage |
|---------|---------|------|-------|
| **Custom Floor Plans** | Segmentation training | 500+ images | 70/20/10 split, DeepLabV3+ training |
| **ZIMHE Sudo-12K** | LoRA fine-tuning | 12,000+ interiors | Room-specific furniture generation |
| **RPLAN** | Validation/evaluation | 80,000+ floor plans | Ground truth comparison, test set |
| **Furniture Measurements JSON** | Dimension normalization | 20+ categories | Standard measurements in meters |

---

## 8. Implementation Details

### Environment
- **Platform:** Google Colab (GPU: T4/V100)
- **Frameworks:** PyTorch, OpenCV, Shapely, Albumentations
- **Models:** DeepLabV3+ (torchvision), Stable Diffusion (diffusers), YOLOv8 (ultralytics)

### Hyperparameters
- **Segmentation:** 20 epochs, Adam (lr=10⁻⁴), input 512×512px
- **LoRA:** Rank 16, 1000 steps, lr=10⁻⁴
- **YOLO:** Confidence τ=0.3, trained 100 epochs
- **Placement:** Pixel-to-meter ratio ρ=0.1, position tolerance 50px

---

## 9. Limitations and Future Work

### Current Limitations
- Segmentation errors propagate downstream
- Dependent on YOLO detection quality
- No semantic furniture relationships (e.g., nightstands near beds)
- Separate models for each stage (not end-to-end)
- Limited handling of built-in/custom furniture
- Computational cost of iterative placement search

### Proposed Future Work
1. **End-to-end learning:** Unified trainable architecture
2. **Transformer-based segmentation:** Better boundary understanding
3. **Semantic relationship modeling:** Functional furniture adjacencies
4. **Multi-room style coordination:** Consistent aesthetics across floor plan
5. **3D extension:** Volumetric room models with furniture
6. **User interaction:** Designer-guided constraints and preferences
7. **Dataset expansion:** More diverse architectural styles and layouts

---

## 10. Repository Structure

```
/Users/sanjanapatel/lora/
├── floor_planrules/                    # Core rule-based system
│   ├── main.py                         # Pipeline orchestration
│   ├── room_analyzer.py                # Room extraction & analysis
│   ├── furniture_definitions.py        # Prototypes & compatibility rules
│   ├── furniture_placer.py             # Placement algorithms (3 phases)
│   ├── door_detector.py                # Door/entrance detection
│   ├── requirements.txt                # Python dependencies
│   └── furniture_crops/
│       └── furniture_measurements.json # Standard dimensions database
│
├── integration (1).ipynb               # Main integration pipeline ⭐
├── roomClassifyCNN (1).ipynb           # DeepLabV3+ segmentation training
├── bedroom_inference.ipynb             # LoRA bedroom generation
├── living_room.ipynb                   # LoRA living room generation
├── bathroom_inference.ipynb            # LoRA bathroom generation
├── hallway_inference.ipynb             # LoRA hallway generation
├── toilet_inference.ipynb              # LoRA toilet room generation
│
├── FIXES_APPLIED.md                    # Technical documentation of fixes
├── QUICK_START.md                      # Usage guide
└── research_paper.tex                  # IEEE conference paper (LaTeX)
```

---

## 11. How to Use

### Quick Start (Single Run)
```python
final_layout, result_image = generate_floor_plan_with_neat_furniture(
    lora_room_images=[
        'path/to/bedroom_0.png',
        'path/to/living_room_0.png',
        'path/to/bathroom_0.png'
    ],
    segmented_mask_path='path/to/segmented_rooms.png',
    furniture_json_path='floor_planrules/furniture_crops/furniture_measurements.json',
    output_folder='output/',
    pixel_to_meter_ratio=0.1,
    debug=True  # Enable detailed logging
)
```

### Recommended (Auto-Optimization)
```python
final_layout, best_image, best_params = generate_best_floor_plan(
    lora_room_images=lora_images,
    segmented_mask_path=mask_path,
    furniture_json_path=json_path,
    output_folder='output_best/',
    pixel_to_meter_ratio=0.1
)

print(f"Best confidence threshold: {best_params['confidence']}")
print(f"Detected furniture placed: {best_params['detected_count']}")
```

### Debug Outputs
- `placement_report.json`: Per-room statistics, placement attempts, success/failure reasons
- Console logs: Detailed placement process with coordinates, angles, validation results
- Visual output: Color-coded furniture overlay on segmented floor plan

---

## 12. Validation and Testing

### Test Environment
- **Hardware:** Colab T4 GPU (16GB VRAM)
- **Runtime:** ~2-3 minutes per floor plan (full pipeline)
- **Memory:** ~8GB peak usage

### Test Cases Validated
✅ Single-room floor plans (bedroom, bathroom, living room)  
✅ Multi-room floor plans (3-5 rooms)  
✅ Complex layouts with hallways and empty rooms  
✅ Various room sizes (small bathrooms to large living rooms)  
✅ Different architectural styles (RPLAN dataset diversity)  
✅ Edge cases: narrow hallways, irregular room shapes  

### Quality Assurance
- All furniture verified inside room boundaries (manual inspection)
- No room left empty across 100 test floor plans
- Rule compliance confirmed (no toilets in bedrooms, etc.)
- Collision detection validated (2.1% overlap rate from intentional tight spaces)

---

## 13. Conclusion

Phase 3 successfully delivered a production-ready hybrid floor plan generation system that:

1. **Eliminates critical failures:** 0% boundary violations, 0% empty rooms
2. **Maximizes placement success:** 87.6% PSR, highest among all methods
3. **Maintains visual quality:** Preserves LoRA aesthetic appeal
4. **Ensures functional validity:** 98.9% rule compliance rate
5. **Provides comprehensive tooling:** Auto-optimization, debug reports, visualization

The hybrid approach demonstrates that **combining generative AI with algorithmic reasoning** produces superior results compared to either approach alone. The system is ready for research publication (IEEE conference paper completed) and further development toward end-to-end learning architectures.

---

## Acknowledgments

**Datasets:**
- ZIMHE Sudo-12K Dataset (GitHub: zimhe/sudo-floor-plan-12k)
- RPLAN Dataset (Graph2Plan paper, Hu et al. 2020)

**Frameworks & Tools:**
- DeepLabV3+ (Chen et al. 2018)
- Stable Diffusion (Rombach et al. 2022)
- LoRA (Hu et al. 2022)
- YOLOv8 (Ultralytics)
- OpenCV, Shapely, PyTorch

---

**Phase 3 Status: ✅ COMPLETE**  
**Next Steps: Research paper submission, user study preparation, end-to-end architecture exploration**
