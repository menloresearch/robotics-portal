<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import {
    secondaryCanvas,
    secondaryCtx,
    isLoading,
    isConnected,
  } from "$lib/store";
  import { handleZoom } from "$lib/interacts";
  import { browser } from "$app/environment";
  import { switchCamera } from "$lib/connection";

  onMount(() => {
    if (!browser) return;

    const canvas = document.getElementById(
      "secondaryDisplay",
    ) as HTMLCanvasElement;
    secondaryCanvas.set(canvas);
    const context = canvas.getContext("2d") as CanvasRenderingContext2D;
    secondaryCtx.set(context);

    // Clear secondary canvas with dark background
    context.fillStyle = "#1f2937";
    context.fillRect(0, 0, canvas.width, canvas.height);

    // Add zoom event listener
    canvas.addEventListener("wheel", handleZoom, { passive: false });

    return () => {
      secondaryCanvas.set(null);
      secondaryCtx.set(null);
    };
  });

  onDestroy(() => {
    if (!browser) return;

    const canvas = document.getElementById(
      "secondaryDisplay",
    ) as HTMLCanvasElement;
    if (canvas) {
      canvas.removeEventListener("wheel", handleZoom);
    }
  });

  // Camera selection
  let selectedMainCamera = 0;
  let selectedSecondaryCamera = 0;
</script>

<div class="overflow-hidden relative">
  <div class="p-2 bg-gray-700 flex items-center">
    <h2
      class="text-xs font-medium leading-tight flex-shrink-0 mr-4 pl-4"
      style="width: 100px;"
    >
      Secondary<br />View
    </h2>

    <!-- Camera selection dropdowns taking more space -->
    <div class="flex space-x-3 flex-grow">
      <div class="flex flex-col">
        <label
          for="mainCamera"
          class="text-xs text-gray-300 mb-1 leading-tight text-left"
          >Main View</label
        >
        <select
          id="mainCamera"
          bind:value={selectedMainCamera}
          on:change={() => switchCamera(selectedMainCamera, "main")}
          disabled={!$isConnected}
          class="px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white text-xs"
        >
          <option value={0}>First person</option>
          <option value={1}>Third person</option>
        </select>
      </div>

      <div class="flex flex-col">
        <label
          for="secondaryCamera"
          class="text-xs text-gray-300 mb-1 leading-tight text-left"
        >
          Secondary View
        </label>
        <select
          id="secondaryCamera"
          bind:value={selectedSecondaryCamera}
          on:change={() => switchCamera(selectedSecondaryCamera, "secondary")}
          disabled={!$isConnected}
          class="px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white text-xs"
        >
          <option value={0}>First person</option>
          <option value={1}>Third person</option>
        </select>
      </div>
    </div>
  </div>

  <div class="relative">
    <canvas id="secondaryDisplay" width="640" height="480" class="w-full h-auto"
    ></canvas>
    {#if $isLoading && $isConnected}
      <div
        class="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-70"
      >
        <div class="text-center">
          <svg
            class="animate-spin h-8 w-8 mx-auto text-blue-500"
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
          <p class="mt-2 text-white text-sm">Loading stream...</p>
        </div>
      </div>
    {/if}
  </div>
</div>
