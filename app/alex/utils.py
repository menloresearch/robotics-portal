import numpy as np
import base64

# Function to encode a NumPy uint8 array to base64
def encode_numpy_array(arr):
    """
    Encode a NumPy uint8 array to a base64 string.
    
    Args:
        arr (numpy.ndarray): Input NumPy uint8 array
    
    Returns:
        str: Base64 encoded string representation of the array
    """
    # Ensure the array is uint8 type
    if arr.dtype != np.uint8:
        arr = arr.astype(np.uint8)
    
    # Convert the array to bytes
    arr_bytes = arr.tobytes()
    
    # Encode to base64
    base64_encoded = base64.b64encode(arr_bytes)
    
    # Convert to string for easier handling
    return base64_encoded.decode('utf-8')

# Function to decode a base64 string back to a NumPy uint8 array
def decode_numpy_array(base64_str, original_shape):
    """
    Decode a base64 string back to a NumPy uint8 array.
    
    Args:
        base64_str (str): Base64 encoded string
        original_shape (tuple): Original shape of the array
    
    Returns:
        numpy.ndarray: Reconstructed NumPy uint8 array
    """
    # Encode back to bytes if it's a string
    if isinstance(base64_str, str):
        base64_bytes = base64_str.encode('utf-8')
    else:
        base64_bytes = base64_str
    
    # Decode base64
    decoded_bytes = base64.b64decode(base64_bytes)
    
    # Reconstruct the NumPy array
    reconstructed_arr = np.frombuffer(decoded_bytes, dtype=np.uint8)
    
    # Reshape to original dimensions
    return reconstructed_arr.reshape(original_shape)

# Example usage
def main():
    # Create a sample uint8 NumPy array
    original_array = np.array([
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
    ], dtype=np.uint8)
    
    print("Original Array:")
    print(original_array)
    print("Original Shape:", original_array.shape)
    
    # Encode the array
    encoded_str = encode_numpy_array(original_array)
    print("\nBase64 Encoded String:")
    print(encoded_str)
    
    # Decode the array back
    decoded_array = decode_numpy_array(encoded_str, original_array.shape)
    print("\nDecoded Array:")
    print(decoded_array)
    
    # Verify the reconstruction
    print("\nArrays are identical:", np.array_equal(original_array, decoded_array))

# Run the example
if __name__ == "__main__":
    main()