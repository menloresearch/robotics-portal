import {
  socket,
  connectionStatus,
  statusColor,
  isConnected,
  isLoading,
  receivedFirstFrame,
  reasoningMessages,
  selectedEnvironment,
  selectedResolution,
  mainCtx,
  mainCanvas,
  secondaryCtx,
  secondaryCanvas,
  frameSize,
  frameBuffer,
  bufferSize,
  isBuffering,
} from "./store";
import { get } from "svelte/store";
import { renderView } from "./renderView";

let frameProcessorInterval: number | null = null;

// Process frames from the buffer at regular intervals
function initFrameBufferProcessor() {
  // Clear any existing interval
  if (frameProcessorInterval) {
    window.clearInterval(frameProcessorInterval);
  }

  // Start a new interval to process frames
  frameProcessorInterval = window.setInterval(() => {
    processFrameBuffer();
  }, 16); // ~60fps processing rate
}

// Process frames from the buffer
function processFrameBuffer() {
  const buffer = get(frameBuffer);
  const bufferSizeInSeconds = get(bufferSize);

  if (buffer.length === 0) {
    return; // No frames to process
  }

  // Calculate current buffer duration
  const oldestFrameTime = buffer[0].timestamp;
  const newestFrameTime = buffer[buffer.length - 1].timestamp;
  const bufferDuration = (newestFrameTime - oldestFrameTime) / 1000; // in seconds

  // If still in initial buffering phase
  if (get(isBuffering)) {
    // Check if we've accumulated enough frames (bufferSizeInSeconds worth)
    if (bufferDuration >= bufferSizeInSeconds) {
      console.log(
        `Buffer filled with ${buffer.length} frames (${bufferDuration.toFixed(1)}s). Starting playback.`,
      );
      isBuffering.set(false);
    } else {
      // Still filling initial buffer, don't render yet
      return;
    }
  }

  // We want to maintain the buffer at our target size
  // Only display a frame if we have more than our target buffer
  // This ensures we keep ~bufferSizeInSeconds of frames in the buffer at all times
  if (bufferDuration > bufferSizeInSeconds) {
    // Get the oldest frame from the buffer
    const oldestFrame = buffer[0];

    // Render the oldest frame
    renderView(oldestFrame.mainView, oldestFrame.secondaryView);

    // Remove only the rendered frame from the buffer
    frameBuffer.update((currentBuffer) => {
      currentBuffer.shift();
      return currentBuffer;
    });
  }

  // If buffer gets critically low (less than half of target size), start buffering again
  // This might happen during network interruptions
  if (bufferDuration < bufferSizeInSeconds / 2 && buffer.length > 1) {
    console.log(
      `Buffer too small: ${bufferDuration.toFixed(1)}s < ${bufferSizeInSeconds / 2}s. Rebuffering...`,
    );
    isBuffering.set(true);
  }
}

export function connect(objectPositions?: any) {
  isLoading.set(true);
  receivedFirstFrame.set(false);
  reasoningMessages.set("");

  // Get WebSocket host from environment variable (set in package.json scripts)
  const wsHost = import.meta.env.VITE_WS_HOST || "localhost:8000";

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";

  // Create WebSocket connection with appropriate protocol
  // const webSocket = new WebSocket(`${protocol}//${wsHost}/ws`);
  const webSocket = new WebSocket(`${protocol}//${wsHost}/ws`);
  socket.set(webSocket);

  // Connection opened
  webSocket.addEventListener("open", () => {
    console.log("Connected to WebSocket server");
    connectionStatus.set("Connected");
    statusColor.set("text-green-500");
    isConnected.set(true);

    // Send environment selection message with object positions if provided
    const message: any = {
      type: "env",
      env: get(selectedEnvironment),
      resolution: get(selectedResolution),
    };

    // Add positions data if provided
    if (objectPositions) {
      // Convert object positions to array format with values divided by 100
      message.positions = {};
      for (const color in objectPositions) {
        const obj = objectPositions[color];
        message.positions[color] = [obj.x / 100, obj.y / 100, obj.z / 100];
      }
    }

    webSocket.send(JSON.stringify(message));
  });

  // Listen for messages
  webSocket.addEventListener("message", async (event) => {
    try {
      // Parse the message as JSON
      const message = JSON.parse(event.data);

      // Calculate message size (approximate for text data)
      frameSize.set((event.data.length / 1024).toFixed(2));

      if (message.type === "connection_established" && message.content) {
        console.info(`Connection status: ${message.content}`);
      }

      if (message.type === "resolution" && message.resolution) {
        selectedResolution.set(message.resolution);
      }

      // Handle different message types
      if (message.type === "streaming_view") {
        // If this is the first frame, stop the loading state
        if (!get(receivedFirstFrame)) {
          receivedFirstFrame.set(true);
          isLoading.set(false);

          // Initialize the frame buffer processor when first connected
          initFrameBufferProcessor();
        }

        // Add the frame to the buffer instead of rendering immediately
        const frameData = {
          mainView: message.main_view,
          secondaryView: message.god_view,
          timestamp: performance.now(),
        };

        // Update the frame buffer with the new frame
        frameBuffer.update((buffer) => {
          buffer.push(frameData);
          return buffer;
        });
      } else if (message.type === "reasoning" && message.message) {
        // Handle reasoning messages
        reasoningMessages.update((current) => current + message.message);

        setTimeout(() => {
          const reasoningBox = document.getElementById("reasoning-box");
          if (reasoningBox) {
            reasoningBox.scrollTop = reasoningBox.scrollHeight;
          }
        }, 0);
      } else if (message.type === "output") {
        reasoningMessages.update(
          (current) =>
            current +
            "\n\n ACTION OUTPUT: \n\n" +
            JSON.stringify(message.message),
        );

        setTimeout(() => {
          const reasoningBox = document.getElementById("reasoning-box");
          if (reasoningBox) {
            reasoningBox.scrollTop = reasoningBox.scrollHeight;
          }
        }, 0);
      }
    } catch (error) {
      console.error("Error processing message:", error);
    }
  });

  // Connection closed
  webSocket.addEventListener("close", () => {
    console.log("Disconnected from WebSocket server");
    connectionStatus.set("Disconnected");
    statusColor.set("text-red-500");
    isConnected.set(false);
    isLoading.set(false);
  });

  // Connection error
  webSocket.addEventListener("error", (event) => {
    console.error("WebSocket error:", event);
    connectionStatus.set("Error");
    statusColor.set("text-red-500");
    isConnected.set(false);
    isLoading.set(false);
  });
}

export function disconnect() {
  const currentSocket = get(socket);
  if (currentSocket) {
    currentSocket.close();
    socket.set(null);
  }

  // Clear the frame processor interval
  if (frameProcessorInterval) {
    window.clearInterval(frameProcessorInterval);
    frameProcessorInterval = null;
  }

  // Reset the frame buffer
  frameBuffer.set([]);
  isBuffering.set(true);

  isLoading.set(false);
  receivedFirstFrame.set(false);
  reasoningMessages.set("");

  // Clear main canvas with dark background
  const ctx = get(mainCtx);
  const canvas = get(mainCanvas);
  if (ctx && canvas) {
    ctx.fillStyle = "#1f2937";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }

  // Clear secondary canvas with dark background
  const secCtx = get(secondaryCtx);
  const secCanvas = get(secondaryCanvas);
  if (secCtx && secCanvas) {
    secCtx.fillStyle = "#1f2937";
    secCtx.fillRect(0, 0, secCanvas.width, secCanvas.height);
  }
}

export function switchCamera(
  cameraIndex: number,
  view: "main" | "secondary" = "main",
) {
  const currentSocket = get(socket);
  if (currentSocket && currentSocket.readyState === WebSocket.OPEN) {
    currentSocket.send(
      JSON.stringify({
        type: "camera_change",
        camera: cameraIndex,
        view: view,
      }),
    );
  }
}

export function setResolution(resolution: number) {
  const currentSocket = get(socket);
  if (currentSocket && currentSocket.readyState === WebSocket.OPEN) {
    currentSocket.send(
      JSON.stringify({
        type: "resolution_change",
        resolution: resolution,
      }),
    );
  }
}

export function sendCommand(commandText: string) {
  const currentSocket = get(socket);
  if (
    currentSocket &&
    currentSocket.readyState === WebSocket.OPEN &&
    commandText.trim()
  ) {
    currentSocket.send(
      JSON.stringify({
        type: "command",
        content: commandText.trim(),
      }),
    );
    reasoningMessages.set("");
    return true;
  }
  return false;
}
