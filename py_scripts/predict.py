import base64
import json
import math
import os
import sys
from pathlib import Path
from typing import Iterable, Sequence

import cv2
import numpy as np
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parent.parent
SPECIES_MODEL = ROOT / "Species_Detection_Model" / "yolo11_species.pt"
DEBRIS_MODEL = ROOT / "Debris_Detection_Model" / "yolo11m_aquatic_debris.pt"
JSON_START = "---JSON_START---"
JSON_END = "---JSON_END---"


def preprocess_underwater(image: np.ndarray) -> np.ndarray:
    if image is None or image.size == 0:
        raise ValueError("Input image could not be decoded")

    channels = image.astype(np.float32)
    means = channels.reshape(-1, 3).mean(axis=0)
    balanced = np.clip(channels * (means.mean() / (means + 1e-5)), 0, 255).astype(
        np.uint8
    )
    lab = cv2.cvtColor(balanced, cv2.COLOR_BGR2LAB)
    lightness, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = cv2.merge([clahe.apply(lightness), a_channel, b_channel])
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)


def _label(model: YOLO, class_id: int) -> str:
    names = model.names
    if isinstance(names, dict):
        return str(names.get(class_id, f"class_{class_id}"))
    return str(names[class_id])


def detect(model: YOLO, image: np.ndarray, kind: str, confidence: float) -> list[dict]:
    result = model.predict(image, conf=confidence, verbose=False)[0]
    detections = []
    for box in result.boxes:
        detections.append(
            {
                "type": kind,
                "label": _label(model, int(box.cls[0].item())),
                "confidence": round(float(box.conf[0].item()), 4),
                "bbox": [round(float(value), 1) for value in box.xyxy[0].tolist()],
            }
        )
    return detections


def iou_and_distance(
    first: Sequence[float], second: Sequence[float]
) -> tuple[float, float]:
    x1, y1 = max(first[0], second[0]), max(first[1], second[1])
    x2, y2 = min(first[2], second[2]), min(first[3], second[3])
    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    area_first = max(0, first[2] - first[0]) * max(0, first[3] - first[1])
    area_second = max(0, second[2] - second[0]) * max(0, second[3] - second[1])
    iou = intersection / (area_first + area_second - intersection + 1e-6)
    center_first = ((first[0] + first[2]) / 2, (first[1] + first[3]) / 2)
    center_second = ((second[0] + second[2]) / 2, (second[1] + second[3]) / 2)
    distance = math.hypot(
        center_first[0] - center_second[0], center_first[1] - center_second[1]
    )
    return float(iou), float(distance)


def assess_risk(
    species: Sequence[dict], debris: Sequence[dict], shape: tuple[int, int]
) -> tuple[str, str, str, list[str], list[dict]]:
    if not debris:
        return (
            "LOW",
            "No debris detected. Ecosystem appears clear.",
            "The debris detector found no objects above the configured confidence threshold, so no species/debris exposure could be established.",
            ["Continue routine monitoring of the habitat."],
            [],
        )
    if not species:
        return (
            "LOW",
            f"Detected {len(debris)} debris item(s), but no aquatic species were detected.",
            f"The system detected {len(debris)} debris item(s), but no aquatic species above the configured confidence threshold. A species interaction cannot be confirmed from this image.",
            ["Review the image manually and repeat monitoring with additional frames if species may be occluded."],
            [],
        )

    height, width = shape
    diagonal = math.hypot(width, height)
    hazardous = ("net", "pbag", "plastic", "rope", "hook")
    interactions = []
    for debris_item in debris:
        is_hazardous = any(
            token in debris_item["label"].lower() for token in hazardous
        )
        for species_item in species:
            iou, distance = iou_and_distance(
                debris_item["bbox"], species_item["bbox"]
            )
            normalized_distance = distance / diagonal if diagonal else 1.0
            if iou > 0.02 or normalized_distance < 0.15:
                relation = (
                    f"overlapping bounding boxes (IoU {iou:.1%})"
                    if iou > 0.02
                    else f"close center distance ({normalized_distance:.1%} of image diagonal)"
                )
                interactions.append(
                    {
                        "species": species_item["label"],
                        "debris": debris_item["label"],
                        "speciesConfidence": species_item["confidence"],
                        "debrisConfidence": debris_item["confidence"],
                        "iou": round(iou, 4),
                        "normalizedDistance": round(normalized_distance, 4),
                        "hazardous": is_hazardous,
                        "relationship": relation,
                    }
                )

    hazardous_count = sum(item["hazardous"] for item in interactions)
    detected_species = ", ".join(
        f'{item["label"]} ({item["confidence"]:.0%})' for item in species
    )
    detected_debris = ", ".join(
        f'{item["label"]} ({item["confidence"]:.0%})' for item in debris
    )
    detail_lines = [
        f"Detected species: {detected_species}.",
        f"Detected debris: {detected_debris}.",
    ]
    recommendations = []
    for index, interaction in enumerate(interactions, start=1):
        hazard_text = "This is classified as a hazardous debris type." if interaction["hazardous"] else "This debris type is not classified as a primary entanglement hazard."
        detail_lines.append(
            f"Interaction {index}: {interaction['species']} is near {interaction['debris']} "
            f"({interaction['relationship']}). {hazard_text}"
        )

    if hazardous_count:
        recommendations = [
            "Prioritize removal or isolation of the hazardous debris.",
            "Inspect the surrounding area for additional entanglement or ingestion hazards.",
            "Continue observation of the affected species after debris removal.",
        ]
        return (
            "HIGH",
            f"CRITICAL: {hazardous_count} hazardous interaction(s) detected involving {len(species)} species and {len(debris)} debris item(s).",
            " ".join(detail_lines),
            recommendations,
            interactions,
        )
    if interactions:
        recommendations = [
            "Monitor the species/debris pair for changing proximity.",
            "Remove the debris if it drifts closer or begins overlapping the species.",
        ]
        return (
            "MEDIUM",
            f"CAUTION: {len(interactions)} species/debris interaction(s) detected involving {len(species)} species and {len(debris)} debris item(s).",
            " ".join(detail_lines),
            recommendations,
            interactions,
        )
    return (
        "LOW",
        f"Monitored {len(species)} species and {len(debris)} debris items with a safe distance buffer.",
        " ".join(detail_lines) + " No species/debris pair crossed the configured IoU or proximity thresholds.",
        ["Continue routine monitoring and rescan if the debris moves closer."],
        interactions,
    )


def activation_heatmap(
    image: np.ndarray, detections: Iterable[dict]
) -> np.ndarray:
    """Create a confidence-weighted detection-region activation heatmap."""
    height, width = image.shape[:2]
    heat = np.zeros((height, width), dtype=np.float32)
    y_grid, x_grid = np.ogrid[:height, :width]
    for detection in detections:
        x1, y1, x2, y2 = map(int, detection["bbox"])
        x1, x2 = max(0, x1), min(width, x2)
        y1, y2 = max(0, y1), min(height, y2)
        if x2 <= x1 or y2 <= y1:
            continue
        sigma = max(x2 - x1, y2 - y1) / 2.0
        center_x, center_y = (x1 + x2) / 2, (y1 + y2) / 2
        activation = np.exp(
            -((x_grid - center_x) ** 2 + (y_grid - center_y) ** 2)
            / (2 * sigma * sigma)
        )
        heat = np.maximum(heat, activation * detection["confidence"])

    if not heat.any():
        return image.copy()
    normalized = cv2.normalize(heat, None, 0, 255, cv2.NORM_MINMAX).astype(
        np.uint8
    )
    return cv2.addWeighted(
        image, 0.6, cv2.applyColorMap(normalized, cv2.COLORMAP_JET), 0.4, 0
    )


def data_url(image: np.ndarray) -> str:
    success, encoded = cv2.imencode(".jpg", image)
    if not success:
        raise IOError("Could not encode output image")
    return "data:image/jpeg;base64," + base64.b64encode(encoded.tobytes()).decode(
        "ascii"
    )


def main() -> None:
    if len(sys.argv) < 2:
        print(
            f"{JSON_START}{json.dumps({'error': 'Usage: predict.py <input_image> [output_image]'})}{JSON_END}"
        )
        sys.exit(1)

    try:
        input_path = Path(sys.argv[1]).expanduser().resolve()
        output_path = (
            Path(sys.argv[2]).expanduser().resolve() if len(sys.argv) > 2 else None
        )
        confidence = float(os.environ.get("DETECTION_CONFIDENCE", "0.25"))
        image = cv2.imread(str(input_path))
        enhanced = preprocess_underwater(image)

        species_model = YOLO(str(SPECIES_MODEL))
        debris_model = YOLO(str(DEBRIS_MODEL))
        species = detect(species_model, enhanced, "species", confidence)
        debris = detect(debris_model, enhanced, "debris", confidence)
        all_detections = [*species, *debris]

        annotated = enhanced.copy()
        for detection in all_detections:
            x1, y1, x2, y2 = map(int, detection["bbox"])
            color = (
                (255, 80, 80)
                if detection["type"] == "species"
                else (80, 220, 120)
            )
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                annotated,
                f'{detection["label"]} {detection["confidence"]:.2f}',
                (x1, max(20, y1 - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2,
            )
        heatmap = activation_heatmap(enhanced, all_detections)
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if not cv2.imwrite(str(output_path), annotated):
                raise IOError(f"Could not write annotated output: {output_path}")

        risk, summary, explanation, recommendations, interactions = assess_risk(
            species, debris, enhanced.shape[:2]
        )
        payload = {
            "overallRiskScore": risk,
            "analysisSummary": summary,
            "detailedExplanation": explanation,
            "recommendations": recommendations,
            "speciesDetections": species,
            "debrisDetections": debris,
            "interactions": interactions,
            "annotatedImageUrl": data_url(annotated),
            "xaiHeatmapUrl": data_url(heatmap),
        }
        print(f"{JSON_START}{json.dumps(payload)}{JSON_END}")
    except Exception as error:
        print(f"{JSON_START}{json.dumps({'error': str(error)})}{JSON_END}")
        sys.exit(1)


if __name__ == "__main__":
    main()
