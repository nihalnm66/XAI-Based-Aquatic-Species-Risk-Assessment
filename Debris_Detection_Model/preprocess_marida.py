import os
import rasterio
import numpy as np
import cv2

def apply_gamma(image, gamma=1.5):
    """Adjusts brightness non-linearly to reveal ocean detail."""
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)

def process_and_augment(tif_path, mask_path, output_dir, base_name):
    with rasterio.open(tif_path) as src:
        # Extract RGB
        blue, green, red = src.read(2), src.read(3), src.read(4)
    
    img = np.dstack((blue, green, red))
    img = np.nan_to_num(img, nan=0.0)

    # 1. Advanced Scaling (Reflectance to 8-bit)
    img = np.clip(img, 0, 0.4) # Slightly wider range for more color depth
    img = (img / 0.4 * 255).astype(np.uint8)
    img = apply_gamma(img, gamma=1.8) # Enhance dark ocean features

    # 2. Process Labels
    with rasterio.open(mask_path) as m_src:
        mask = m_src.read(1)
        h, w = mask.shape

    yolo_lines = []
    for class_id in np.unique(mask):
        if class_id == 0: continue
        binary_mask = np.uint8(mask == class_id)
        contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            if bw < 2 or bh < 2: continue
            yolo_lines.append(f"{class_id-1} {(x+bw/2)/w:.6f} {(y+bh/2)/h:.6f} {bw/w:.6f} {bh/h:.6f}")

    # 3. Save Original + Augmentations (Horizontal Flip)
    label_txt = "\n".join(yolo_lines)
    
    # Save Original
    cv2.imwrite(os.path.join(output_dir, 'images', f"{base_name}.png"), img)
    with open(os.path.join(output_dir, 'labels', f"{base_name}.txt"), 'w') as f: f.write(label_txt)

    # Save Flipped (Doubles the data!)
    img_flipped = cv2.flip(img, 1)
    cv2.imwrite(os.path.join(output_dir, 'images', f"{base_name}_flip.png"), img_flipped)
    
    # Flip YOLO coordinates
    flipped_lines = []
    for line in yolo_lines:
        c, x, y, w_val, h_val = map(float, line.split())
        flipped_lines.append(f"{int(c)} {1.0-x:.6f} {y:.6f} {w_val:.6f} {h_val:.6f}")
    
    with open(os.path.join(output_dir, 'labels', f"{base_name}_flip.txt"), 'w') as f: 
        f.write("\n".join(flipped_lines))

def preprocess_marida(raw_dir, out_dir):
    os.makedirs(os.path.join(out_dir, 'images'), exist_ok=True)
    os.makedirs(os.path.join(out_dir, 'labels'), exist_ok=True)
    
    found_count = 0
    for root, _, files in os.walk(raw_dir):
        for file in files:
            if file.endswith('.tif') and not any(x in file for x in ['_cl', '_conf', '_re']):
                img_path = os.path.join(root, file)
                base = os.path.splitext(file)[0]
                mask_path = os.path.join(root, f"{base}_cl.tif")
                
                if os.path.exists(mask_path):
                    process_and_augment(img_path, mask_path, out_dir, base)
                    found_count += 1
                    if found_count % 100 == 0: print(f"Processed {found_count} original patches...")

    print(f"✅ Preprocessed Dataset Ready! Created {found_count * 2} files (Original + Flipped).")

# Target folders
RAW_FOLDER = 'data_raw/MARIDA'
PREPROCESSED_FOLDER = 'data_preprocessed'

preprocess_marida(RAW_FOLDER, PREPROCESSED_FOLDER)
