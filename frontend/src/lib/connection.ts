import {
  socket,
  connectionStatus,
  statusColor,
  isConnected,
  isLoading,
  receivedFirstFrame,
  reasoningMessages,
  selectedEnvironment,
  mainCtx,
  mainCanvas,
  secondaryCtx,
  secondaryCanvas,
  frameSize,
} from "./store";
import { get } from "svelte/store";
import { renderView } from "./renderView";

export function connect(objectPositions?: any) {
  isLoading.set(true);
  receivedFirstFrame.set(false);
  reasoningMessages.set("");

  // Get WebSocket host from environment variable (set in package.json scripts)
  const wsHost = import.meta.env.VITE_WS_HOST || "localhost:8000";

  // Create WebSocket connection
  const webSocket = new WebSocket(`ws://${wsHost}/ws`);
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

      if (message.type === "connection_established" && message.client_id) {
        console.info(`Connection with id ${message.client_id}`);
      }

      // Handle different message types
      if (message.type === "streaming_view") {
        // If this is the first frame, stop the loading state
        if (!get(receivedFirstFrame)) {
          receivedFirstFrame.set(true);
          isLoading.set(false);
        }

        await renderView(message.main_view, message.god_view);
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

export function setFrameRate(fpsValue: string) {
  const currentSocket = get(socket);
  if (currentSocket && currentSocket.readyState === WebSocket.OPEN) {
    currentSocket.send(
      JSON.stringify({
        type: "fps_change",
        fps: parseInt(fpsValue),
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
