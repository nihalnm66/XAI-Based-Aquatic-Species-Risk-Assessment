# 🌊 An XAI-Based Conservation Framework for Identifying Aquatic Species under Risk in Natural Ecosystems

An end-to-end intelligent system for detecting aquatic species and marine debris in underwater imagery, then estimating species/debris interaction risk. The production runtime combines a Java Spring Boot API with a Python preprocessing and **INT8 ONNX Runtime** inference pipeline.

---

## 📑 Table of Contents
1. [Theoretical Background & Motivation](#-theoretical-background--motivation)
2. [Phase 1: Preprocessing & Enhancement Pipeline](#-phase-1-preprocessing--enhancement-pipeline)
3. [Phase 2: Model Training & Architecture](#-phase-2-model-training--architecture)
4. [Phase 3: Model Evaluation & Performance Metrics](#-phase-3-model-evaluation--performance-metrics)
5. [Phase 4: Production Runtime & Backend Orchestration](#-phase-4-production-runtime--backend-orchestration)
6. [Repository Structure](#-repository-structure)
7. [Installation & Quick Start](#-installation--quick-start)
8. [Deploy on Render](#-deploy-on-render)

---

## 🔬 Theoretical Background & Motivation

Underwater photography and videography suffer from severe optical degradation caused by light absorption and scattering:
* **Wavelength-Dependent Absorption:** Red light is absorbed within the first few meters of water, followed by green and blue, resulting in heavy blue/green color casts.
* **Optical Scattering:** Suspended particles cause forward and backward scattering, generating dense optical haze and lowering contrast.

Without targeted enhancement, standard object detection models experience massive performance drops due to obscured edges and distorted textures. This project solves this challenge by decoupling **image enhancement** from **object detection**, passing optimized visual data into exported YOLO11 models.

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

The training pipeline uses **YOLO11m (Medium)** for debris detection and a YOLO11 species detector. Production inference uses their exported, quantized **INT8 ONNX** versions so the service can run efficiently on Render's CPU-based container.

* **Training Specifications:**
  * **Framework:** Ultralytics YOLOv11 during training; ONNX Runtime during production inference
  * **Base Weights:** `yolo11m.pt` (Transfer Learning)
  * **Epochs:** 50
  * **Image Size:** $640 \times 640$
  * **Batch Size:** 16
  * **Dataset Configuration:** `/content/preprocessed_dataset/data.yaml` (15 specialized marine debris classes)

---

## 📊 Phase 3: Model Evaluation & Performance Metrics

Following 50 epochs of training, the model weights checkpoint (`best.pt`) was validated against 1,001 validation images (1,891 total instances):

The metrics below describe the original PyTorch training/evaluation checkpoint; production inference uses the corresponding INT8 ONNX exports.

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

## 💻 Phase 4: Production Runtime & Backend Orchestration

The production service is a **Java Spring Boot** API backed by a Python/OpenCV/ONNX Runtime inference process:

* **RESTful API (`/api/analyze` and `/api/analyze-upload`)**: Accepts a multipart image upload, runs `py_scripts/predict.py`, and returns `HIGH`, `MEDIUM`, or `LOW` risk classifications.
* **INT8 ONNX inference**: `predict.py` loads `Species_Detection_Model/yolo11_species.int8.onnx` and `Debris_Detection_Model/yolo11m_aquatic_debris.int8.onnx` with `CPUExecutionProvider`.
* **Preprocessing and XAI output**: Gray-world white balance, LAB/CLAHE enhancement, bounding-box annotations, and confidence-weighted activation heatmaps are generated for each analysis.
* **Persistence and authentication**: PostgreSQL/Hibernate persistence and JWT authentication are provided by the Spring Boot backend. Render supplies database connection values and generates `JWT_SECRET`.

---

## 📂 Repository Structure

```text
XAI-Based-Aquatic-Species-Risk-Assessment/
│
├── Backend_Service/                  # Java Spring Boot REST API & database orchestration
├── Debris_Detection_Model/           # YOLO11m aquatic debris model
│   ├── Debris_Train.ipynb            # Complete Google Colab training & validation notebook
│   ├── yolo11m_aquatic_debris.pt     # Training checkpoint
│   └── yolo11m_aquatic_debris.int8.onnx # Production CPU inference model
├── Species_Detection_Model/          # YOLO11 aquatic species model
│   ├── yolo11_species.pt             # Training checkpoint
│   └── yolo11_species.int8.onnx      # Production CPU inference model
├── Dockerfile                        # Combined Java + Python deployment image
├── render.yaml                       # Render web service and PostgreSQL blueprint
├── requirements.txt                  # Python inference dependencies
├── py_scripts/                       # Python preprocessing and inference wrappers
│   └── predict.py                    # Local inference script called by the Spring Boot backend
└── README.md                         # Project documentations

---

## ⚙️ Installation & Quick Start

### 1. Clone the Repository

```bash
git clone [https://github.com/nihalnm66/XAI-Based-Aquatic-Species-Risk-Assessment.git](https://github.com/nihalnm66/XAI-Based-Aquatic-Species-Risk-Assessment.git)
cd XAI-Based-Aquatic-Species-Risk-Assessment

```

### 2. Run Local Python Inference

Install the production inference dependencies, then test an image locally:

```bash
python3 -m pip install -r requirements.txt
python py_scripts/predict.py /path/to/input.jpg /tmp/annotated.jpg

```

### 3. Start the Spring Boot Backend

Navigate to the backend service directory and run the application via Maven:

```bash
cd Backend_Service
mvn spring-boot:run

```

### 4. Test the API Endpoint via cURL

```bash
curl -X POST "http://localhost:8080/api/analyze-upload" \
  -F "file=@/path/to/image.jpg"

```

## ☁️ Deploy on Render

The repository includes a Docker deployment that packages the Spring Boot API,
Python/OpenCV/NumPy/ONNX Runtime, frontend, and both INT8 ONNX models into one
CPU-based web service. Render PostgreSQL supplies the database connection
through environment variables, so local database credentials are not used in
production.

1. Push the repository to GitHub.
2. Create a Render account and choose **New → Blueprint**.
3. Select this GitHub repository and branch `main`.
4. Render reads `render.yaml`, builds the Docker image, and creates the web service and database.
5. Open the generated `https://...onrender.com` URL from any device. The
   frontend is served at `/`, and image analysis is available at
   `/api/analyze-upload` (also `/api/analyze`).

The free web service may sleep after inactivity, so the first request after a
period of inactivity can take a few minutes. CPU-only inference is also slower
than local GPU inference. Do not commit database passwords or other secrets;
configure them in Render environment variables.

```json
{
  "analysisSummary": "CRITICAL: 1 hazardous interaction(s) detected.",
  "detailedExplanation": "Detected species: ...",
  "recommendations": [
    "Continue routine monitoring and rescan if the debris moves closer."
  ],
  "speciesDetections": [],
  "debrisDetections": [],
  "interactions": [],
  "annotatedImageUrl": "data:image/jpeg;base64,...",
  "xaiHeatmapUrl": "data:image/jpeg;base64,...",
  "overallRiskScore": "HIGH",
  "sessionId": "fb216712-2c76-404a-9b56-709e4082b494"
}

```
