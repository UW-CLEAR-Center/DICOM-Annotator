import numpy as np

def my_image_normalize(image, bit_depth=16, low=0, high=1, sub_area_ratio=4):
    max_pixel_value = 2 ** bit_depth - 1
    image = np.array(image, dtype=float)
    h, l = image.shape
    hm = h // 2
    lm = l // 2
    dh = np.ceil(h / sub_area_ratio / 2)
    dl = np.ceil(l / sub_area_ratio / 2)
    hs = max(0, int(hm - dh))
    he = min(h, int(hm + dh))
    ls = max(0, int(lm - dl))
    le = min(l, int(lm + dl))
    sorted_pixels = np.sort(image[hs:he, ls:le], axis=None)
    num_pixels = sorted_pixels.shape[0]
    min_condition_pixel = sorted_pixels[int(num_pixels * low)]
    max_condition_pixel = sorted_pixels[int(num_pixels * high) - 1]

    image = max_pixel_value * (image - min_condition_pixel) / (max_condition_pixel - min_condition_pixel)
    image = np.minimum(max_pixel_value, image)
    image = np.maximum(0, image)

    return image

