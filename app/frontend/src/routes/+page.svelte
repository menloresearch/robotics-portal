<!-- App.svelte -->
<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { handleZoom } from "$lib/interacts.ts";

  // State variables
  let socket: WebSocket | null = null;
  let connectionStatus = "Disconnected";
  let statusColor = "text-red-500";
  let frameCount = 0;
  let isDragging = false;
  let lastMouseX = 0;
  let lastMouseY = 0;
  let fps = "0";
  let latency = "0";
  let frameSize = "0";
  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;
  let isConnected = false;

  // Performance tracking
  let lastFrameTime = 0;
  let fpsArray: number[] = [];
  let latencyArray: number[] = [];

  // Initialize canvas on mount
  onMount(() => {
    canvas = document.getElementById("imageDisplay") as HTMLCanvasElement;
    ctx = canvas.getContext("2d") as CanvasRenderingContext2D;

    // Clear canvas with gray background
    ctx.fillStyle = "#f3f4f6";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Add zoom event listener
    canvas.addEventListener(
      "wheel",
      (e) => handleZoom(socket as WebSocket, e),
      {
        passive: false,
      },
    );

    // Add drag event listeners
    // canvas.addEventListener("mousedown", handleMouseDown);
    // canvas.addEventListener("mousemove", handleMouseMove);
    // canvas.addEventListener("mouseup", handleMouseUp);
    // canvas.addEventListener("mouseleave", handleMouseUp);
  });

  // Clean up event listener on destroy
  onDestroy(() => {
    if (socket) {
      socket.close();
    }
    if (canvas) {
      canvas.removeEventListener("wheel", (e) =>
        handleZoom(socket as WebSocket, e),
      );
      // canvas.removeEventListener("mousedown", handleMouseDown);
      // canvas.removeEventListener("mousemove", handleMouseMove);
      // canvas.removeEventListener("mouseup", handleMouseUp);
      // canvas.removeEventListener("mouseleave", handleMouseUp);
    }
  });

  onDestroy(() => {
    if (socket) {
      socket.close();
    }
  });

  // Connect to WebSocket server
  function connect() {
    socket = new WebSocket("ws://localhost:8000/ws");

    // Connection opened
    socket.addEventListener("open", (event) => {
      console.log("Connected to WebSocket server");
      connectionStatus = "Connected";
      statusColor = "text-green-500";
      isConnected = true;
    });

    // Listen for messages
    socket.addEventListener("message", async (event) => {
      const now = performance.now();

      // Calculate message size
      frameSize = (event.data.size / 1024).toFixed(2);

      try {
        // If the message is a Blob (binary data)
        if (event.data instanceof Blob) {
          // Create object URL from blob
          const objectUrl = URL.createObjectURL(event.data);

          // Load and display the image
          const img = new Image();
          img.onload = () => {
            // Draw image on canvas
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

            // Clean up object URL after image loads
            URL.revokeObjectURL(objectUrl);

            // Update metrics
            frameCount++;

            // Calculate FPS
            const elapsed = now - lastFrameTime;
            if (lastFrameTime !== 0) {
              const currentFps = 1000 / elapsed;
              fpsArray.push(currentFps);
              if (fpsArray.length > 30) fpsArray.shift();
              fps = (
                fpsArray.reduce((a, b) => a + b, 0) / fpsArray.length
              ).toFixed(1);
            }
            lastFrameTime = now;

            // Estimate latency using client-side timestamps
            const currentLatency = performance.now() - now;
            latencyArray.push(currentLatency);
            if (latencyArray.length > 30) latencyArray.shift();
            latency = (
              latencyArray.reduce((a, b) => a + b, 0) / latencyArray.length
            ).toFixed(1);
          };
          img.src = objectUrl;
        } else {
          // If it's not a blob, try to parse it as JSON
          const message = JSON.parse(event.data);
          // Handle any JSON control messages here if needed
          console.log("Received JSON message:", message);
        }
      } catch (error) {
        console.error("Error processing message:", error);
      }
    });

    // Connection closed
    socket.addEventListener("close", (event) => {
      console.log("Disconnected from WebSocket server");
      connectionStatus = "Disconnected";
      statusColor = "text-red-500";
      isConnected = false;
    });

    // Connection error
    socket.addEventListener("error", (event) => {
      console.error("WebSocket error:", event);
      connectionStatus = "Error";
      statusColor = "text-red-500";
      isConnected = false;
    });
  }

  // Disconnect from WebSocket server
  function disconnect() {
    if (socket) {
      socket.close();
      socket = null;
    }
  }

  // Function to switch between cameras
  function switchCamera(cameraIndex: number) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(
        JSON.stringify({
          type: "camera_change",
          camera: cameraIndex,
        }),
      );
    }
  }

  // Send control message back to server (example of bidirectional communication)
  function setFrameRate() {
    if (socket && socket.readyState === WebSocket.OPEN) {
      const fpsValue = (document.getElementById("fpsInput") as HTMLInputElement)
        .value;
      socket.send(
        JSON.stringify({
          type: "fps_change",
          fps: parseInt(fpsValue),
        }),
      );
    }
  }
</script>

<div class="container mx-auto max-w-3xl px-4 py-6">
  <h1 class="text-2xl font-bold mb-4">WebSocket Image Stream</h1>

  <div class="flex items-center space-x-3 mb-4">
    <button
      on:click={connect}
      disabled={isConnected}
      class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-300 disabled:bg-gray-300 disabled:cursor-not-allowed"
    >
      Connect
    </button>

    <button
      on:click={disconnect}
      disabled={!isConnected}
      class="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-300 disabled:bg-gray-300 disabled:cursor-not-allowed"
    >
      Disconnect
    </button>

    <div class="flex items-center space-x-2 ml-4">
      <input
        id="fpsInput"
        type="number"
        min="1"
        max="60"
        value="30"
        class="w-16 px-2 py-1 border border-gray-300 rounded-md"
      />
      <button
        on:click={setFrameRate}
        disabled={!isConnected}
        class="px-2 py-1 bg-gray-200 rounded-md hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
      >
        Set FPS
      </button>
    </div>

    <div class="flex items-center space-x-2 ml-4">
      {#each Array(3) as _, i}
        <button
          on:click={() => switchCamera(i)}
          disabled={!isConnected}
          class="px-3 py-1 bg-purple-500 text-white rounded-md hover:bg-purple-600 focus:outline-none focus:ring-2 focus:ring-purple-300 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          Camera {i + 1}
        </button>
      {/each}
    </div>
  </div>

  <div class="border border-gray-300 rounded-md overflow-hidden shadow-sm">
    <canvas
      id="imageDisplay"
      width="640"
      height="480"
      class="w-full h-auto cursor-grab active:cursor-grabbing"
    ></canvas>
  </div>

  <div
    class="mt-4 bg-gray-100 p-4 rounded-md font-mono text-sm grid grid-cols-2 gap-x-4 gap-y-2"
  >
    <div>Connection: <span class={statusColor}>{connectionStatus}</span></div>
    <div>Frames Received: <span class="font-semibold">{frameCount}</span></div>
    <div>FPS: <span class="font-semibold">{fps}</span></div>
    <div>Latency: <span class="font-semibold">{latency}</span> ms</div>
    <div>
      Last Frame Size: <span class="font-semibold">{frameSize}</span> KB
    </div>
  </div>
</div>
