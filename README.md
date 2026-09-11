# 🌊 XAI-Based Aquatic Species Risk Assessment & Marine Debris Detection

An advanced, end-to-end intelligent system engineered to detect, classify, and evaluate the environmental risk of marine debris and aquatic waste from underwater imagery. This project integrates rigorous computer vision theory, custom-trained deep learning object detection, and a production-grade Java Spring Boot backend persistence layer.

---

## 📑 Table of Contents
1. [Theoretical Background & Motivation](#-theoretical-background--motivation)
2. [Phase 1: Preprocessing & Enhancement Pipeline](#-phase-1-preprocessing--enhancement-pipeline)
3. [Phase 2: Model Training & Architecture](#-phase-2-model-training--architecture)
4. [Phase 3: Model Evaluation & Performance Metrics](#-phase-3-model-evaluation--performance-metrics)
5. [Phase 4: Backend Orchestration & Development](#-phase-4-backend-orchestration--development)
6. [Repository Structure](#-repository-structure)
7. [Installation & Quick Start](#-installation--quick-start)

---

## 🔬 Theoretical Background & Motivation

Underwater photography and videography suffer from severe optical degradation caused by light absorption and scattering:
* **Wavelength-Dependent Absorption:** Red light is absorbed within the first few meters of water, followed by green and blue, resulting in heavy blue/green color casts.
* **Optical Scattering:** Suspended particles cause forward and backward scattering, generating dense optical haze and lowering contrast.

Without targeted enhancement, standard object detection models experience massive performance drops due to obscured edges and distorted textures. This project solves this challenge by decoupling **image enhancement** from **object detection**, passing optimized visual data into a state-of-the-art YOLOv11 model.

---

## 🛠️ Phase 1: Preprocessing & Enhancement Pipeline

Implemented via Python, OpenCV, and NumPy inside Google Colab (`Debris_Train.ipynb`), the custom pre-processing pipeline executes the following steps:

1. **Dataset Ingestion**: Automatically mounts Google Drive, extracts the compressed archive, and loads the `underwater_plastics` dataset.
2. **Gray World White-Balance & Color Correction**: 
   * Calculates the arithmetic mean intensity of the Blue, Green, and Red channels across the image.
   * Derives an average gray scalar to dynamically scale color channels, neutralizing dominant aquatic tints.
3. **LAB Color Space Conversion**: 
   * Splits the image into **L** (Lightness/Luminance), **A** (Green-Red components), and **B** (Blue-Yellow components) channels to process lighting adjustments independently of true color information.
4. **CLAHE (Contrast Limited Adaptive Histogram Equalization)**: 
   * Applied directly to the $L$-channel using a defined tile grid size ($8 \times 8$) and clip limit to cut through optical scattering and amplify localized visibility of hidden debris.

* **Total Processed Volume:** **5,130 raw underwater images** successfully enhanced across training, validation, and test splits.

---

## 🚀 Phase 2: Model Training & Architecture

The object detection engine utilizes **YOLO11m (Medium)**, chosen for its optimal balance between inference speed and parameter capacity (~20.04 million parameters) to support downstream explainability modules.

* **Training Specifications:**
  * **Framework:** Ultralytics YOLOv11 (PyTorch / CUDA backend)
  * **Base Weights:** `yolo11m.pt` (Transfer Learning)
  * **Epochs:** 50
  * **Image Size:** $640 \times 640$
  * **Batch Size:** 16
  * **Dataset Configuration:** `/content/preprocessed_dataset/data.yaml` (15 specialized marine debris classes)

---

## 📊 Phase 3: Model Evaluation & Performance Metrics

Following 50 epochs of training, the model weights checkpoint (`best.pt`) was validated against 1,001 validation images (1,891 total instances):

### **Core Accuracy Metrics**
* **mAP50 (Overall Accuracy):** **73.5%** ($0.7346$)
* **mAP50-95 (Strict Accuracy):** **48.7%** ($0.4867$)
* **Precision (P):** **78.7%** ($0.7872$)
* **Recall (R):** **68.4%** ($0.6844$)

### **Class-Specific Performance (mAP50)**
* 🕶️ **Sunglasses:** 99.5%
* 📱 **Cellphone:** 97.5%
* 🛍️ **Plastic Bag (`pbag`):** 96.4%
* 🥅 **Net (`net`):** 93.5%
* 🍾 **Glass Bottle (`gbottle`):** 82.8%
* 🧤 **Glove:** 82.6%
* 🧃 **Plastic Bottle (`pbottle`):** 83.3%
* 🛞 **Tire:** 78.7%

---

## 💻 Phase 4: Backend Orchestration & Development

The custom weights file (`yolo11m_aquatic_debris.pt`) is integrated into a robust **Java Spring Boot** backend architecture:

* **RESTful API (`/api/analyze`)**: Accepts image pathways, triggers Python-based preprocessing and YOLO inference pipelines (`predict.py`), and evaluates environmental risk classifications (`HIGH`, `MEDIUM`, `LOW`).
* **Database Persistence (PostgreSQL & Hibernate)**: Automatically records session UUIDs, creation timestamps, original image paths, explanation heatmap paths, and detection summaries into the `aquaculture_db` relational database (`detection_results` table).
* **Explainability Support**: High parameter capacity ensures downstream Grad-CAM modules generate clear, precise attribution heatmaps for end users.

---

## 📂 Repository Structure

```text
XAI-Based-Aquatic-Species-Risk-Assessment/
│
├── Backend_Service/                  # Java Spring Boot REST API & database orchestration
├── Debris_Detection_Model/           # Model weights and training assets
│   ├── Debris_Train.ipynb            # Complete Google Colab training & validation notebook
│   └── yolo11m_aquatic_debris.pt     # Custom-trained YOLO11m production weights (~40.5MB)
├── py_scripts/                       # Python preprocessing and inference wrappers
│   └── predict.py                    # Local inference script called by the Spring Boot backend
└── README.md                         # Project documentation

---

## ⚙️ Installation & Quick Start

### 1. Clone the Repository

```bash
git clone [https://github.com/nihalnm66/XAI-Based-Aquatic-Species-Risk-Assessment.git](https://github.com/nihalnm66/XAI-Based-Aquatic-Species-Risk-Assessment.git)
cd XAI-Based-Aquatic-Species-Risk-Assessment

```

### 2. Run Local Python Inference

Ensure dependencies (`ultralytics`, `opencv-python`, `numpy`) are installed, then test an image locally:

```bash
python py_scripts/predict.py

```

### 3. Start the Spring Boot Backend

Navigate to the backend service directory and run the application via Maven:

```bash
cd Backend_Service
mvn spring-boot:run

```

### 4. Test the API Endpoint via cURL

```bash
curl -X POST "http://localhost:8080/api/analyze?path=/path/to/image.jpg"

```

```json
{
  "analysisSummary": "Summary: Detected: pbag (92.7%) | Risk: HIGH",
  "createdAt": "2026-08-15T17:52:00.641671",
  "heatmapPath": "outputs/heatmap_/path/to/image.jpg",
  "id": 6,
  "originalImagePath": "/path/to/image.jpg",
  "overallRiskScore": "HIGH",
  "sessionId": "fb216712-2c76-404a-9b56-709e4082b494"
}

```