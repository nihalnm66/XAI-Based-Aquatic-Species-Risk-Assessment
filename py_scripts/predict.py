# py_scripts/predict.py
import sys
import json
import os
from ultralytics import YOLO

def main():
    # Java will pass these arguments
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Missing arguments"}))
        sys.exit(1)

    input_image_path = sys.argv[1]
    output_image_path = sys.argv[2]
    
    # Path to your custom weights (relative to where Java runs the script)
    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Debris_Detection_Model/yolo11m_aquatic_debris.pt"))
    #model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Debris_Detection_Model/best.pt"))

    try:
        # Load the custom model
        model = YOLO(model_path)
        
        # Run inference
        results = model(input_image_path)
        
        # Save the image with bounding boxes drawn
        results[0].save(output_image_path)
        
        # Analyze detections for Risk Score
        detections = results[0].boxes.cls.tolist()
        confidences = results[0].boxes.conf.tolist()
        names = model.names
        
        if len(detections) == 0:
            risk = "LOW"
            summary = "No debris detected. Ecosystem appears clear."
        else:
            # Simple risk logic based on quantity (you can customize this)
            risk = "HIGH" if len(detections) >= 5 else "MEDIUM"
            
            # Format a nice summary string
            detected_classes = [names[int(c)] for c in detections]
            unique_classes = set(detected_classes)
            avg_conf = sum(confidences) / len(confidences) * 100 if confidences else 0
            summary = f"Detected {len(detections)} objects ({', '.join(unique_classes)}) | Avg Confidence: {avg_conf:.1f}%"
            
        # Create output JSON for Java
        output = {
            "overallRiskScore": risk,
            "analysisSummary": summary
        }
        
        # Print ONLY the JSON at the very end so Java can parse it
        print(f"---JSON_START---{json.dumps(output)}---JSON_END---")
        
    except Exception as e:
        print(f"---JSON_START---{json.dumps({'error': str(e)})}---JSON_END---")

if __name__ == "__main__":
    main()