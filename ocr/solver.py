import cv2
import numpy as np
import os
from datetime import datetime
from global_variables import logger
from ocr.ocr import predict
from global_variables import TRAIN_DATA_FOLDER


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

        left_number = predict(left_enhanced)
        right_number = predict(right_enhanced)

        result = left_number + right_number

        # Save the singular images as training data
        if save:
            self.save_training_data(left_enhanced, left_number)
            self.save_training_data(right_enhanced, right_number)

        return result


if __name__ == "__main__":
    ...
