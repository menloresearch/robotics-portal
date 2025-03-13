<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { handleZoom } from "$lib/interacts";
  import { viewRender } from "$lib/msgHandler";

  // State variables
  let socket: WebSocket | null = null;
  let connectionStatus = "Disconnected";
  let statusColor = "text-red-500";
  let frameCount = 0;
  let fps = "0";
  let latency = "0";
  let frameSize = "0";
  let canvas: HTMLCanvasElement;
  let ctx: CanvasRenderingContext2D;
  let secondaryCanvas: HTMLCanvasElement;
  let secondaryCtx: CanvasRenderingContext2D;
  let isConnected = false;
  let instruction = "";
  let reasoningMessages: string = "";
  let selectedEnvironment = "go2";
  let environments = [
    { id: "go2", name: "Go2" },
    { id: "g1", name: "G1" },
  ];

  // Performance tracking
  let lastFrameTime = 0;
  let fpsArray: number[] = [];
  let latencyArray: number[] = [];

  // Initialize canvas on mount
  onMount(() => {
    canvas = document.getElementById("imageDisplay") as HTMLCanvasElement;
    ctx = canvas.getContext("2d") as CanvasRenderingContext2D;
    secondaryCanvas = document.getElementById(
      "secondaryDisplay",
    ) as HTMLCanvasElement;
    secondaryCtx = secondaryCanvas.getContext("2d") as CanvasRenderingContext2D;

    // Clear main canvas with dark background
    ctx.fillStyle = "#1f2937";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Clear secondary canvas with dark background
    secondaryCtx.fillStyle = "#1f2937";
    secondaryCtx.fillRect(0, 0, secondaryCanvas.width, secondaryCanvas.height);

    // Add zoom event listener
    secondaryCanvas.addEventListener(
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
    if (secondaryCanvas) {
      secondaryCanvas.removeEventListener("wheel", (e) =>
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
    // socket = new WebSocket("ws:/localhost:8000/ws");
    socket = new WebSocket("ws://192.168.0.20:8000/ws");

    // Connection opened
    socket.addEventListener("open", (event) => {
      console.log("Connected to WebSocket server");
      connectionStatus = "Connected";
      statusColor = "text-green-500";
      isConnected = true;

      // Send environment selection message
      socket.send(
        JSON.stringify({
          type: "env",
          env: selectedEnvironment,
        }),
      );
    });

    // Listen for messages
    socket.addEventListener("message", async (event) => {
      try {
        // Parse the message as JSON
        const message = JSON.parse(event.data);

        // Calculate message size (approximate for text data)
        frameSize = (event.data.length / 1024).toFixed(2);

        if (message.type === "connection_established" && message.client_id) {
          console.info(`Connection with id ${message.client_id}`);
        }

        // Handle different message types
        if (message.type === "streaming_view") {
          [frameCount, lastFrameTime, fps, latency] = await viewRender(
            message.main_view,
            ctx,
            canvas,
            frameCount,
            lastFrameTime,
            fpsArray,
            fps,
            latencyArray,
            latency,
          );

          await viewRender(
            message.god_view,
            secondaryCtx,
            secondaryCanvas,
            frameCount,
            lastFrameTime,
            fpsArray,
            fps,
            latencyArray,
            latency,
          );
        } else if (message.type === "reasoning" && message.message) {
          // Handle reasoning messages
          reasoningMessages += message.message;

          setTimeout(() => {
            const reasoningBox = document.getElementById("reasoning-box");
            if (reasoningBox) {
              reasoningBox.scrollTop = reasoningBox.scrollHeight;
            }
          }, 0);
        } else if (message.type === "output") {
          reasoningMessages +=
            "\n\n ACTION OUTPUT: \n\n" + JSON.stringify(message.message);
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

  // Send command instruction to the backend
  function sendCommand() {
    if (socket && socket.readyState === WebSocket.OPEN && instruction.trim()) {
      socket.send(
        JSON.stringify({
          type: "command",
          content: instruction.trim(),
        }),
      );
      // Clear the input after sending
      instruction = "";
      reasoningMessages = "";
    }
  }
</script>

<div class="flex justify-between items-center mb-4">
  <div class="min-h-screen min-w-screen bg-gray-900 text-white p-4">
    <h1 class="text-2xl font-bold mb-8">
      Portal Dashboard / Uranus Notebook (Dan's idea :3)
    </h1>
    <div class="grid grid-cols-12 gap-4">
      <!-- Left Side Panels - Control Panel and Telemetry -->
      <div class="col-span-2 space-y-4">
        <!-- Control Panel -->
        <div class="bg-gray-800 rounded-lg p-4">
          <h2 class="text-xl font-semibold mb-4">Control Panel</h2>

          <div class="space-y-4">
            <div class="space-y-2">
              <h3 class="text-sm font-medium text-gray-400">Environment</h3>
              <div class="flex flex-col space-y-2">
                <select
                  bind:value={selectedEnvironment}
                  disabled={isConnected}
                  class="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white"
                >
                  {#each environments as env}
                    <option value={env.id}>{env.name}</option>
                  {/each}
                </select>
              </div>
            </div>

            <div class="space-y-2">
              <h3 class="text-sm font-medium text-gray-400">Connection</h3>
              <div class="flex flex-col space-y-2">
                <button
                  on:click={connect}
                  disabled={isConnected}
                  class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed"
                >
                  Connect
                </button>
                <button
                  on:click={disconnect}
                  disabled={!isConnected}
                  class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed"
                >
                  Disconnect
                </button>
              </div>
            </div>

            <div class="space-y-2">
              <h3 class="text-sm font-medium text-gray-400">
                Frame Rate Control
              </h3>
              <div class="flex flex-col space-y-2">
                <input
                  id="fpsInput"
                  type="number"
                  min="1"
                  max="60"
                  value="30"
                  class="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white"
                />
                <button
                  on:click={setFrameRate}
                  disabled={!isConnected}
                  class="px-2 py-1 bg-gray-700 rounded-md hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  Set FPS
                </button>
              </div>
            </div>

            <div class="space-y-2">
              <h3 class="text-sm font-medium text-gray-400">
                Camera Selection
              </h3>
              <div class="grid grid-cols-1 gap-2">
                <button
                  on:click={() => switchCamera(0)}
                  disabled={!isConnected}
                  class="px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed"
                >
                  First person view
                </button>
                <button
                  on:click={() => switchCamera(1)}
                  disabled={!isConnected}
                  class="px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed"
                >
                  Third person view
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Telemetry Data -->
        <div class="bg-gray-800 rounded-lg p-4">
          <h2 class="text-xl font-semibold mb-4">Telemetry</h2>
          <div class="space-y-2 font-mono text-sm">
            <div class="flex justify-between">
              <span>Connection:</span>
              <span class={statusColor}>{connectionStatus}</span>
            </div>
            <div class="flex justify-between">
              <span>Frames:</span>
              <span class="font-semibold">{frameCount}</span>
            </div>
            <div class="flex justify-between">
              <span>FPS:</span>
              <span class="font-semibold">{fps}</span>
            </div>
            <div class="flex justify-between">
              <span>Latency:</span>
              <span class="font-semibold">{latency} ms</span>
            </div>
            <div class="flex justify-between">
              <span>Frame Size:</span>
              <span class="font-semibold">{frameSize} KB</span>
            </div>
            <div class="flex justify-between">
              <span>Environment:</span>
              <span class="font-semibold"
                >{environments.find((env) => env.id === selectedEnvironment)
                  ?.name || selectedEnvironment}</span
              >
            </div>
          </div>
        </div>
      </div>

      <!-- Main Content Area -->
      <div class="col-span-7 space-y-4">
        <!-- Main Render View -->
        <div class="bg-gray-800 rounded-lg overflow-hidden">
          <div class="p-2 bg-gray-700">
            <h2 class="text-sm font-medium">Main Camera View</h2>
          </div>
          <canvas
            id="imageDisplay"
            width="640"
            height="480"
            class="w-full h-auto cursor-grab active:cursor-grabbing"
          ></canvas>
        </div>
      </div>

      <!-- Right Side Panels -->
      <div class="col-span-3 space-y-4">
        <!-- Secondary Camera View -->
        <div class="bg-gray-800 rounded-lg overflow-hidden">
          <div class="p-2 bg-gray-700">
            <h2 class="text-sm font-medium">Secondary View</h2>
          </div>
          <canvas
            id="secondaryDisplay"
            width="640"
            height="480"
            class="w-full h-auto"
          ></canvas>
        </div>

        <!-- Frontal Cortex Panel (Reasoning) -->
        <div class="bg-gray-800 rounded-lg p-4 flex flex-col">
          <h2 class="text-xl font-semibold mb-4">Frontal cortex</h2>
          <div class="space-y-4 flex-grow flex flex-col">
            <div
              id="reasoning-box"
              class="h-96 bg-gray-700 rounded-md p-3 overflow-y-auto flex-grow"
            >
              {#if reasoningMessages.length === 0}
                <div class="text-gray-400 italic">Reasoning...</div>
              {:else}
                <div class="mb-2 text-sm whitespace-pre-wrap">
                  {reasoningMessages}
                </div>
              {/if}
            </div>
            <div class="flex space-x-2 mt-auto">
              <input
                type="text"
                bind:value={instruction}
                placeholder="Instruction..."
                class="flex-1 px-3 py-2 bg-gray-700 rounded-md border border-gray-600 focus:outline-none focus:border-blue-500"
                on:keydown={(e) => e.key === "Enter" && sendCommand()}
              />
              <button
                on:click={sendCommand}
                disabled={!isConnected}
                class="px-4 py-2 bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
