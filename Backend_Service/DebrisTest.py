import cv2
from ultralytics import YOLO

# Load the trained model using its absolute path
model_path = "/Users/nihal/Desktop/MAC/project/XAI-Based-Aquatic-Species-Risk-Assessment/Debris_Detection_Model/debris_v2_medium_best.pt"
model = YOLO(model_path)

# Define the image source
image_source = "image.jpg" 

print(f"Running inference on {image_source}...")

# Run prediction (turned off built-in show, but keeping save=True)
results = model.predict(source=image_source, save=True, show=False)

# Extract and print the detection results
for result in results:
    print(f"\nFound {len(result.boxes)} object(s).")
    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        class_name = model.names[class_id]
        print(f" - Detected: {class_name} (Confidence: {confidence:.2f})")

    # --- Manually display the image using OpenCV ---
    annotated_img = result.plot() # Generates the image array with bounding boxes
    
    cv2.imshow("YOLOv8 Debris Detection", annotated_img)
    
print("\n✅ Inference complete!")
print("Press any key while the image window is selected to close it...")

# Keep window open until a key is pressed
cv2.waitKey(0)
cv2.destroyAllWindows()