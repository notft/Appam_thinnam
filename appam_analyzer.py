# appam_analyzer.py
import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

def create_appam_mask(image):
    
    _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("No appam detected in image")
    
    main_contour = max(contours, key=cv2.contourArea)
    
    
    mask = np.zeros_like(image)
    cv2.drawContours(mask, [main_contour], -1, (255), -1)
    return mask

def enhance_image(image):
    
    denoised = cv2.bilateralFilter(image, 9, 75, 75)
    
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)
    return enhanced

def detect_holes(binary, min_area=15, max_area=1200):
    
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2,2))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    
    valid_holes = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if min_area < area < max_area:
            perimeter = cv2.arcLength(contour, True)
            if perimeter > 0:
                circularity = 4 * np.pi * area / (perimeter ** 2)
                if 0.3 < circularity < 1.2:
                    valid_holes.append(contour)
    
    return valid_holes

def visualize_results(original, masked, enhanced, binary, final_contours, output_dir):
    
    visualization = cv2.cvtColor(original, cv2.COLOR_GRAY2BGR)
    
    
    for contour in final_contours:
        area = cv2.contourArea(contour)
        color = (0, 255, 0) if area < 50 else (255, 0, 0) if area < 200 else (0, 0, 255)
        
       
        cv2.drawContours(visualization, [contour], -1, color, 2)
        
      
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            cv2.circle(visualization, (cX, cY), 2, color, -1)
    
    
    plt.figure(figsize=(15, 5))
    
    plt.subplot(141)
    plt.imshow(masked, cmap='gray')
    plt.title('Masked')
    plt.axis('off')
    
    plt.subplot(142)
    plt.imshow(enhanced, cmap='gray')
    plt.title('Enhanced')
    plt.axis('off')
    
    plt.subplot(143)
    plt.imshow(binary, cmap='gray')
    plt.title('Binary')
    plt.axis('off')
    
    plt.subplot(144)
    plt.imshow(cv2.cvtColor(visualization, cv2.COLOR_BGR2RGB))
    plt.title('Final Detection')
    plt.axis('off')
    
    plt.tight_layout()
    
   
    timestamp = cv2.getTickCount()
    steps_path = os.path.join(output_dir, f'processing_steps_{timestamp}.png')
    final_path = os.path.join(output_dir, f'final_detection_{timestamp}.jpg')
    
    plt.savefig(steps_path)
    cv2.imwrite(final_path, visualization)
    plt.close()  
    
    return visualization, steps_path, final_path

def count_holes(image_path):
    
    original = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if original is None:
        raise ValueError("Could not read image")
    
   
    mask = create_appam_mask(original)
    masked_image = cv2.bitwise_and(original, mask)
    
  
    enhanced = enhance_image(masked_image)
    
    
    binary = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        15,
        3
    )
    binary = cv2.bitwise_and(binary, mask)
    
    valid_holes = detect_holes(binary)
    
    
    output_dir = 'static/uploads'  
    os.makedirs(output_dir, exist_ok=True)
    
    visualization, steps_path, final_path = visualize_results(
        original, masked_image, enhanced, binary, valid_holes, output_dir
    )
    
    return len(valid_holes), steps_path, final_path

if __name__ == "__main__":
    image_path = "path/to/your/test/image.png"
    try:
        num_holes, steps_image, final_image = count_holes(image_path)
        print(f"Number of holes detected: {num_holes}")
        print(f"Processing steps saved to: {steps_image}")
        print(f"Final detection saved to: {final_image}")
    except Exception as e:
        print(f"Error processing image: {str(e)}")