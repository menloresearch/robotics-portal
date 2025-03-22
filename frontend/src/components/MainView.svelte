<script lang="ts">
  import { onMount } from "svelte";
  import { mainCanvas, mainCtx, isLoading, isConnected } from "$lib/store";

  // Set 16:9 aspect ratio dimensions
  const aspectRatio = 16 / 9;
  const resolution = 1080;

  onMount(() => {
    const canvas = document.getElementById("imageDisplay") as HTMLCanvasElement;
    mainCanvas.set(canvas);
    const context = canvas.getContext("2d") as CanvasRenderingContext2D;
    mainCtx.set(context);

    // Ensure canvas dimensions match the specified width and height
    canvas.width = resolution * aspectRatio;
    canvas.height = resolution;

    // Clear main canvas with dark background
    context.fillStyle = "#1f2937";
    context.fillRect(0, 0, canvas.width, canvas.height);

    // Handle window resize to maintain aspect ratio
    const handleResize = () => {
      // Canvas dimensions are controlled by CSS and the container's aspect ratio
      // The actual drawing surface maintains the 1920x1080 resolution
    };

    window.addEventListener("resize", handleResize);
    handleResize(); // Initialize

    return () => {
      window.removeEventListener("resize", handleResize);
      mainCanvas.set(null);
      mainCtx.set(null);
    };
  });
</script>

<div class="fixed inset-0 z-0 bg-gray-800 flex items-center justify-center">
  <div
    class="absolute top-0 left-0 p-2 bg-gray-700 bg-opacity-80 rounded-br-lg z-10"
  >
    <h2 class="text-sm font-medium">Main View</h2>
  </div>
  <div class="relative w-full h-full flex items-center justify-center">
    <!-- Container to maintain 16:9 aspect ratio -->
    <div class="relative w-full" style="aspect-ratio: 16/9; max-height: 100%;">
      <canvas
        id="imageDisplay"
        width="1920"
        height="1080"
        class="absolute top-0 left-0 w-full h-full object-cover cursor-grab active:cursor-grabbing"
      ></canvas>
      {#if $isLoading && $isConnected}
        <div
          class="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-70"
        >
          <div class="text-center">
            <svg
              class="animate-spin h-10 w-10 mx-auto text-blue-500"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            <p class="mt-2 text-white">Loading stream...</p>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>
