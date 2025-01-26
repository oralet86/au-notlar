import cv2
import numpy as np
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image
import os
from datetime import datetime
from global_variables import logger, PROCESSOR_NAME, MODEL_NAME, TRAIN_DATA_FOLDER


class ModelSingleton:
    """
    A singleton pair of a model and a processor.
    Use get_processor() to get the instantiated processor,
    Use get_model() to get the instantiated model.
    """

    _processor = None
    _model = None
    _processor_loaded = False
    _model_loaded = False

    @classmethod
    def get_processor(cls):
        logger.info("Processor requested!")
        if cls._processor is None:
            cls._processor = TrOCRProcessor.from_pretrained(PROCESSOR_NAME)
            cls._processor_loaded = True
        return cls._processor

    @classmethod
    def get_model(cls):
        logger.info("Model requested!")
        if cls._model is None:
            cls._model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)
            cls._model_loaded = True
        return cls._model

    @classmethod
    def is_loaded(cls):
        return cls._processor_loaded and cls._model_loaded


class CaptchaSolver:
    """
    A class to solve equation Captchas.
    Create an object of this class with either the equation image path as input or the image data as an np.ndarray.
    use object.solve_captcha() to get the result.
    """

    def __init__(self, image: str | np.ndarray):
        logger.info("Initializing a CaptchaSolver object.")
        if isinstance(image, str):
            self.image = cv2.imread(image)
        elif isinstance(image, np.ndarray):
            self.image = image
        else:
            raise TypeError("Argument image must either be str or np.ndarray")
        self.kernel = np.ones((2, 2), np.uint8)
        self.processor = ModelSingleton.get_processor()
        self.model = ModelSingleton.get_model()

    def enhance_legibility(self, cropped_image: np.ndarray) -> np.ndarray:
        """
        Enhances the legibility of a given cropped image by converting it to grayscale,
        applying thresholding to create a binary mask, and refining the mask with blurring
        and erosion.

        Args:
            cropped_image (np.ndarray): The input image.

        Returns:
            np.ndarray: Enhanced version of the input image.
        """
        gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        return cv2.erode(cv2.blur(mask, (2, 2)), self.kernel, iterations=1)

    def process_image(self, image_data: np.ndarray) -> int:
        """
        Processes the image to extract the number it contains.

        Args:
            image_data (np.ndarray): The image to be processed.

        Returns:
            int: The extracted number. Returns -1 if the number couldn't be extracted.
        """
        # Turn ndarray into an image object and preprocess
        image = Image.fromarray(image_data).convert("RGB")
        pixel_values = self.processor(images=image, return_tensors="pt").pixel_values

        # Generate text
        output = self.model.generate(pixel_values)
        decoded = self.processor.batch_decode(output, skip_special_tokens=True)[
            0
        ].strip()
        try:
            result = int("".join(ch for ch in decoded if ch.isdigit()))
            return result
        except ValueError:
            logger.info(
                f'Failure while extracting number from CAPTCHA! Expected an integer, got "{decoded}"'
            )
            raise ValueError

    def resolve(self, left_image: np.ndarray, right_image: np.ndarray) -> dict:
        """
        Takes a left_image and a right_image in the forms of ndarrays.
        Returns a dictionary containing the left number, the right number and their sums.

        Args:
            left_image (np.ndarray): Image of the left number.
            right_image (np.ndarray): Image of the right number.

        Returns:
            dict: A dictionary with the following keys:
              - "left" (int): The number extracted from the left side of the equation. -1 if the number couldn't be extracted.
              - "right" (int): The number extracted from the right side of the equation. -1 if the number couldn't be extracted.
              - "sum" (int): The result of the equation based on the extracted numbers. "Error" if any of the extracted numbers are -1.
        """
        left_number = self.process_image(left_image)
        right_number = self.process_image(right_image)
        return {
            "left": left_number,
            "right": right_number,
            "sum": (
                (left_number + right_number)
                if (left_number > 0 and right_number > 0)
                else "Error"
            ),
        }

    def save_training_data(self, image: np.ndarray, label: int) -> None:
        """
        Saves a given image and the label in the folder specified in "TRAIN_DATA_FOLDER"
        with the following name convention: "label_year-month-day_hour-minute-second.png"

        Args:
            image (np.ndarray): The image to be saved.
            label (int): The label extracted from the image.
        """
        os.makedirs(TRAIN_DATA_FOLDER, exist_ok=True)
        name = f"{label}_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.png"
        data_path = f"{TRAIN_DATA_FOLDER}/{name}"
        logger.info(f'Saving training data to "{data_path}"')
        cv2.imwrite(data_path, image)

    def solve_captcha(self, save: bool = False) -> int | None:
        """
        Solves the CAPTCHA and returns a dictionary containing the numbers on the left
        and right side of the equation, along with the calculated result.

        Args:
            save (bool, optional): If True, saves the enhanced images of the left and
            right numbers for use as training data. Defaults to False.

        Returns:
            int | None: The result of the equation, if found, will be returned. If not, None will be returned.
        """
        logger.info("Attempting to solve CAPTCHA..")
        positions = {"left": 5, "right": 45}
        dimensions = {"width": 25}

        left_image = self.image[
            7:27, positions["left"] : positions["left"] + dimensions["width"]
        ]
        right_image = self.image[
            7:27, positions["right"] : positions["right"] + dimensions["width"]
        ]

        left_enhanced = self.enhance_legibility(left_image)
        right_enhanced = self.enhance_legibility(right_image)

        try:
            result = self.resolve(left_enhanced, right_enhanced)
        except ValueError:
            logger.info("Error while resolving CAPTCHA.")
            return 0

        # Save the singular images as training data
        if save:
            self.save_training_data(left_enhanced, result["left"])
            self.save_training_data(right_enhanced, result["right"])

        return result["sum"]


if __name__ == "__main__":
    for i in range(10):
        try:
            solver = CaptchaSolver(f"{TRAIN_DATA_FOLDER}/captcha{i+1}.png")
            result = solver.solve_captcha()
            print(f"{i+1} result: {result}")
        except Exception as e:
            print(f"Error: {e}")
            continue
