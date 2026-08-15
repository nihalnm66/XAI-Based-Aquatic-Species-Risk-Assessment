
import argparse
import sys
from ultralytics import YOLO

def main():
    parser = argparse.ArgumentParser(description="Aquatic Debris Detection Inference")
    parser.add_argument("--image", type=str, required=True, help="Path to input image")
    args = parser.parse_args()

    try:
        # Load the model weights
        model_path = "../Debris_Detection_Model/yolo11m_aquatic_debris.pt"
        model = YOLO(model_path)

        # Run inference (verbose=False hides the messy YOLO speed logs)
        results = model(args.image, verbose=False)
        # Run inference (verbose=False hides the messy YOLO speed logs)
        results = model(args.image, verbose=False)

        # NEW: Save the image with the bounding boxes drawn on it!
        annotated_image_path = args.image.replace(".jpg", "_result.jpg")
        results[0].save(filename=annotated_image_path)
        detections = []
        for r in results:
            # zip() lets us loop through class IDs and confidence scores at the same time
            for c, conf in zip(r.boxes.cls, r.boxes.conf):
                class_name = model.names[int(c)]
                confidence_percentage = float(conf) * 100
                
                # Format exactly how it will appear in the database
                detections.append(f"{class_name} ({confidence_percentage:.1f}%)")

        if detections:
            summary = f"Detected: {', '.join(detections)}"
            risk = "HIGH"
        else:
            summary = "No debris detected. Environment clear."
            risk = "LOW"

        # Print final clean output to Spring Boot
        print(f"Summary: {summary} | Risk: {risk}")

    except Exception as e:
        print(f"Error during execution: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()