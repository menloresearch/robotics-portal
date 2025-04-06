from io import BytesIO
import numpy as np
import base64
from PIL import Image


def encode_numpy_array(arr):
    """
    Encode a NumPy uint8 array to a gzipped base64 string.

    Args:
        arr (numpy.ndarray): Input NumPy uint8 array

    Returns:
        str: Gzipped base64 encoded string representation of the array
    """

    # Ensure the array is uint8 type
    if arr.dtype != np.uint8:
        arr = arr.astype(np.uint8)

    img_pil = Image.fromarray(arr)

    buffer = BytesIO()
    img_pil.save(buffer, format="WebP", quality=80, method=0)
    webp_bytes = buffer.getvalue()
    buffer.close()

    return base64.b64encode(webp_bytes).decode("utf-8")
