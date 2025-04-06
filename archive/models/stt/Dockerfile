# Start with the specified base image
FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-devel
RUN apt-get update -y && apt-get install -y libcudnn9-cuda-12
# Set the working directory
WORKDIR /workspace

# Copy requirements.txt to the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

EXPOSE 3348