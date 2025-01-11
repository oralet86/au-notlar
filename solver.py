import cv2
import numpy as np
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image

class ModelSingleton:
    _instance = None

    def __init__(self):
        if ModelSingleton._instance is None:
            ModelSingleton._instance = dict()
            ModelSingleton._instance["processor"] = TrOCRProcessor.from_pretrained("microsoft/trocr-large-printed")
            ModelSingleton._instance["model"] = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-large-printed")

class CaptchaSolver:
    def __init__(self, image_path):
        ModelSingleton()
        self.image = cv2.imread(image_path)
        self.kernel = np.ones((2, 2), np.uint8)
        self.processor = ModelSingleton._instance["processor"]
        self.model = ModelSingleton._instance["model"]

    def enhance_legibility(self, cropped_image):
        gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        return cv2.erode(cv2.blur(mask, (2, 2)), self.kernel, iterations=1)

    def process_image(self, image_path):
        # Open image and preprocess
        image = Image.open(image_path).convert("RGB")
        pixel_values = self.processor(images=image, return_tensors="pt").pixel_values

        # Generate text
        output = self.model.generate(pixel_values)
        return int("".join(ch for ch in self.processor.batch_decode(output, skip_special_tokens=True)[0].strip() if ch.isdigit()))

    def resolve(self, left_image, right_image):
        left_number = self.process_image(left_image)
        right_number = self.process_image(right_image)
        return {"left": left_number, "right": right_number, "sum": left_number+right_number}

    def solve_captcha(self):
        positions = {'left': 5, 'right': 45}
        dimensions = {'width': 25}
        
        left_image = self.image[7:27, positions['left']:positions['left']+dimensions['width']]
        right_image = self.image[7:27, positions['right']:positions['right']+dimensions['width']]
        
        left_enhanced = self.enhance_legibility(left_image)
        right_enhanced = self.enhance_legibility(right_image)

        cv2.imwrite('left_number.png', left_enhanced)
        cv2.imwrite('right_number.png', right_enhanced)

        return self.resolve('left_number.png', 'right_number.png')

if __name__ == "__main__":
    solver = CaptchaSolver("ocr/testimages/captcha10.png")
    result = solver.solve_captcha()
    print(result)