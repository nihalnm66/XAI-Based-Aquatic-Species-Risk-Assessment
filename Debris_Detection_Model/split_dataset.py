import os
import shutil

def organize_splits(preprocessed_dir, splits_dir):
    categories = ['train', 'val', 'test']
    
    for cat in categories:
        os.makedirs(os.path.join(preprocessed_dir, 'images', cat), exist_ok=True)
        os.makedirs(os.path.join(preprocessed_dir, 'labels', cat), exist_ok=True)

    # Dictionary of what is actually on your Mac
    available_images = {os.path.splitext(f)[0]: f for f in os.listdir(os.path.join(preprocessed_dir, 'images')) if f.endswith('.png')}
    available_labels = {os.path.splitext(f)[0]: f for f in os.listdir(os.path.join(preprocessed_dir, 'labels')) if f.endswith('.txt')}

    for cat in categories:
        split_files = [f for f in os.listdir(splits_dir) if cat in f.lower() and f.endswith('.txt')]
        
        move_count = 0
        for split_file in split_files:
            with open(os.path.join(splits_dir, split_file), 'r') as file:
                patch_names = [line.strip().split('.')[0] for line in file.readlines() if line.strip()]
                
                for name in patch_names:
                    # Handle the S2_ prefix mismatch
                    match = None
                    if name in available_images:
                        match = name
                    elif f"S2_{name}" in available_images:
                        match = f"S2_{name}"
                    
                    if match:
                        # 1. Move the Original Image and Label
                        shutil.move(os.path.join(preprocessed_dir, 'images', available_images[match]),
                                    os.path.join(preprocessed_dir, 'images', cat, available_images[match]))
                        if match in available_labels:
                            shutil.move(os.path.join(preprocessed_dir, 'labels', available_labels[match]),
                                        os.path.join(preprocessed_dir, 'labels', cat, available_labels[match]))
                        move_count += 1

                        # 2. Handle the Flipped Image (Only use for Training!)
                        flip_match = f"{match}_flip"
                        if flip_match in available_images:
                            if cat == 'train':
                                # Move flip to train folder
                                shutil.move(os.path.join(preprocessed_dir, 'images', available_images[flip_match]),
                                            os.path.join(preprocessed_dir, 'images', cat, available_images[flip_match]))
                                if flip_match in available_labels:
                                    shutil.move(os.path.join(preprocessed_dir, 'labels', available_labels[flip_match]),
                                                os.path.join(preprocessed_dir, 'labels', cat, available_labels[flip_match]))
                                move_count += 1
                            else:
                                # Discard flip for val/test to prevent "Data Leakage"
                                os.remove(os.path.join(preprocessed_dir, 'images', available_images[flip_match]))
                                if flip_match in available_labels:
                                    os.remove(os.path.join(preprocessed_dir, 'labels', available_labels[flip_match]))
        
        print(f"✅ Successfully prepared {move_count} files for {cat}")

# Target preprocessed folder
PREPROCESSED_FOLDER = 'data_preprocessed'
SPLITS_FOLDER = 'data_raw/MARIDA/splits'

organize_splits(PREPROCESSED_FOLDER, SPLITS_FOLDER)
