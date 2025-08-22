import cv2
import numpy as np


class ImageEnhancement:
    @staticmethod
    def gaussian_blur(image, kernel_size=15):
        """高斯模糊"""
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)

    @staticmethod
    def median_blur(image, kernel_size=5):
        """中值滤波"""
        return cv2.medianBlur(image, kernel_size)

    @staticmethod
    def bilateral_filter(image, d=9, sigma_color=75, sigma_space=75):
        """双边滤波"""
        return cv2.bilateralFilter(image, d, sigma_color, sigma_space)

    @staticmethod
    def sharpen(image):
        """锐化"""
        kernel = np.array([[-1, -1, -1],
                           [-1, 9, -1],
                           [-1, -1, -1]])
        return cv2.filter2D(image, -1, kernel)

    @staticmethod
    def unsharp_mask(image, kernel_size=(5, 5), sigma=1.0, amount=1.0, threshold=0):
        """USM锐化"""
        blurred = cv2.GaussianBlur(image, kernel_size, sigma)
        sharpened = float(amount + 1) * image - float(amount) * blurred
        sharpened = np.maximum(sharpened, np.zeros(sharpened.shape))
        sharpened = np.minimum(sharpened, 255 * np.ones(sharpened.shape))
        sharpened = sharpened.round().astype(np.uint8)
        if threshold > 0:
            low_contrast_mask = np.absolute(image - blurred) < threshold
            np.copyto(sharpened, image, where=low_contrast_mask)
        return sharpened
