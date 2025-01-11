import cv2
import numpy as np
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image

class ModelSingleton:
    _processor = None
    _model = None

    @classmethod
    def get_processor(cls):
        if cls._processor is None:
            cls._processor = TrOCRProcessor.from_pretrained("microsoft/trocr-large-printed")
        return cls._processor

    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-large-printed")
        return cls._model


class CaptchaSolver:
    def __init__(self, image_path):
        ModelSingleton()
        self.image = cv2.imread(image_path)
        self.kernel = np.ones((2, 2), np.uint8)
        self.processor = ModelSingleton.get_processor()
        self.model = ModelSingleton.get_model()

    def enhance_legibility(self, cropped_image):
        gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        return cv2.erode(cv2.blur(mask, (2, 2)), self.kernel, iterations=1)

    def process_image(self, image_data):
        # Turn ndarray into an image object and preprocess
        image = Image.fromarray(image_data).convert("RGB")
        pixel_values = self.processor(images=image, return_tensors="pt").pixel_values

        # Generate text
        output = self.model.generate(pixel_values)
        decoded = self.processor.batch_decode(output, skip_special_tokens=True)[0].strip() 
        try:
            result = int("".join(ch for ch in decoded if ch.isdigit()))
        except ValueError:
            # print(decoded)
            result = -1
        finally:
            return result

    def resolve(self, left_image, right_image):
        left_number = self.process_image(left_image)
        right_number = self.process_image(right_image)
        return {"left": left_number, "right": right_number, "sum": ((left_number + right_number) if (left_number > 0 and right_number > 0) else "Error")}

    def solve_captcha(self):
        positions = {'left': 5, 'right': 45}
        dimensions = {'width': 25}
        
        left_image = self.image[7:27, positions['left']:positions['left']+dimensions['width']]
        right_image = self.image[7:27, positions['right']:positions['right']+dimensions['width']]
        
        left_enhanced = self.enhance_legibility(left_image)
        right_enhanced = self.enhance_legibility(right_image)

        return self.resolve(left_enhanced, right_enhanced)

if __name__ == "__main__":
    solver = CaptchaSolver("ocr/testimages/captcha4.png")
    result = solver.solve_captcha()
    print(result)