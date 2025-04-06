import {
  socket,
  connectionStatus,
  statusColor,
  isConnected,
  isLoading,
  receivedFirstFrame,
  reasoningMessages,
  selectedScene,
  scenes,
  selectedResolution,
  mainCtx,
  mainCanvas,
  secondaryCtx,
  secondaryCanvas,
  frameSize,
  frameBuffer,
  isBuffering,
  isRunning,
} from "./store";
import { get } from "svelte/store";
import { renderView } from "./renderView";

let frameProcessorInterval: number | null = null;

// Process frames in real-time without buffering
function initFrameBufferProcessor() {
  // Clear any existing interval
  if (frameProcessorInterval) {
    window.clearInterval(frameProcessorInterval);
    frameProcessorInterval = null;
  }
  
  // We no longer need a frame processor interval as frames are rendered immediately
  // This function is kept for compatibility but doesn't set up any interval
  console.log("Real-time rendering enabled - no frame buffer");
}

// This function is no longer used but kept for compatibility
function processFrameBuffer() {
  // No-op: We're rendering frames immediately as they arrive
}

export function connect(objectPositions?: any) {
  isLoading.set(true);
  receivedFirstFrame.set(false);
  reasoningMessages.set("");

  // Get WebSocket host from environment variable (set in package.json scripts)
  const wsHost = import.meta.env.VITE_WS_HOST || "localhost:8000";

  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";

  // Create WebSocket connection with appropriate protocol
  const webSocket = new WebSocket(`${protocol}//${wsHost}/ws`);
  socket.set(webSocket);

  // Connection opened
  webSocket.addEventListener("open", () => {
    console.log("WebSocket connection opened");
    // Don't send environment message here anymore
    // It will be sent when the Run button is clicked
  });

  // Listen for messages
  webSocket.addEventListener("message", async (event) => {
    try {
      // Parse the message as JSON
      const message = JSON.parse(event.data);

      // Calculate message size (approximate for text data)
      frameSize.set((event.data.length / 1024).toFixed(2));

      if (message.type === "connection_established") {
        let content = JSON.parse(message.content);
        console.info("Content: ", content);
        scenes.set(content.scenes);
        selectedScene.set(content.scenes[0].id);

        // Set connection status when we receive the connection_established message
        console.log("Connected to server successfully");
        connectionStatus.set("Connected");
        statusColor.set("text-green-500");
        isConnected.set(true);
        isLoading.set(false);
      }

      if (message.type === "resolution" && message.resolution) {
        selectedResolution.set(message.resolution);
      }

      // Handle different message types
      if (message.type === "streaming_view") {
        // If this is the first frame we're receiving
        if (!get(receivedFirstFrame)) {
          receivedFirstFrame.set(true);
          isLoading.set(false); // Stop loading indicator once frames start arriving
          isBuffering.set(false); // Make sure buffering is disabled
          
          // Call init once to ensure any previous intervals are cleared
          initFrameBufferProcessor();
        }

        // Render the frame immediately when it arrives
        renderView(message.main_view, message.god_view);
        
        // We no longer buffer frames, but keep timestamp for telemetry
        const frameData = {
          mainView: message.main_view,
          secondaryView: message.god_view,
          timestamp: performance.now(),
        };
        
        // For telemetry purposes, we still update the buffer with the latest frame
        // but we only keep the most recent frame
        frameBuffer.set([frameData]);
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
    isRunning.set(false);
  });

  // Connection error
  webSocket.addEventListener("error", (event) => {
    console.error("WebSocket error:", event);
    connectionStatus.set("Error");
    statusColor.set("text-red-500");
    isConnected.set(false);
    isLoading.set(false);
    isRunning.set(false);
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

export function toggleRunning(objectPositions?: any) {
  const currentValue = get(isRunning);
  const newValue = !currentValue;

  const currentSocket = get(socket);
  if (currentSocket && currentSocket.readyState === WebSocket.OPEN) {
    // If starting the simulation
    if (newValue) {
      isLoading.set(true); // Show loading indicator until frames arrive
      receivedFirstFrame.set(false); // Reset first frame status

      // First send environment selection message (previously sent on connection)
      const envMessage: any = {
        type: "scene",
        scene: get(selectedScene),
        resolution: get(selectedResolution),
      };

      // Add positions data if provided
      if (objectPositions) {
        // Convert object positions to array format with values divided by 100
        envMessage.positions = {};
        for (const color in objectPositions) {
          const obj = objectPositions[color];
          envMessage.positions[color] = [obj.x / 100, obj.y / 100, obj.z / 100];
        }
      }

      // Send environment configuration first
      currentSocket.send(JSON.stringify(envMessage));
      console.log("Sent environment configuration:", envMessage);

      // Then send the run command
      currentSocket.send(
        JSON.stringify({
          type: "run_state",
          running: true,
        }),
      );
    } else {
      // If stopping the simulation
      // Clear the loading state immediately
      isLoading.set(false);

      // Clear the frame buffer
      frameBuffer.set([]);
      isBuffering.set(true);

      // Clear MainView's loading overlay as well by setting receivedFirstFrame to true
      receivedFirstFrame.set(true);

      // Send stop command
      currentSocket.send(
        JSON.stringify({
          type: "run_state",
          running: false,
        }),
      );
    }

    // Update running state
    isRunning.set(newValue);

    console.log(`Robot ${newValue ? "started" : "stopped"}`);
    return true;
  }
  return false;
}
