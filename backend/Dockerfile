# Use the specified base image
FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-devel

# Set the working directory in the container
WORKDIR /app
RUN apt-get update && apt-get install -y \
    git ffmpeg libsm6 libxext6 libglew2.2 libgl1-mesa-glx libosmesa6 \
    && rm -rf /var/lib/apt/lists/*
# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire current directory contents into the container at /app
RUN apt-get update -y && apt-get install -y libglfw3-dev libgles2-mesa-dev
RUN apt-cache search mesa | grep -i egl
RUN pip install --no-cache-dir genesis-world @ git+https://github.com/Genesis-Embodied-AI/Genesis.git@main
COPY . .


# RUN python cache_build_kernel.py
# Specify the default command to run your application
# Change the following line to run your actual application script
EXPOSE 8000


# Set environment variables for CUDA
ENV PATH=/usr/local/cuda/bin/:$PATH
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/cuda/lib64
ENTRYPOINT [ "gunicorn" ]
# Specify the command to run your application using Gunicorn and Uvicorn workers
CMD [ "app:app", "-k", "uvicorn.workers.UvicornWorker", "-w", "16", "-b", "0.0.0.0:8000", "-t", "1000"]