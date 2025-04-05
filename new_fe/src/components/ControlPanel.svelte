<script lang="ts">
  import {
    selectedScene,
    scenes,
    isConnected,
    isLoading,
    selectedResolution,
    isRunning,
  } from "$lib/store";
  import {
    connect,
    disconnect,
    setResolution,
    toggleRunning,
  } from "$lib/connection";
  import { onMount } from "svelte";

  // TypeScript interfaces
  interface Coordinate {
    min: number;
    max: number;
  }

  interface CoordinateRanges {
    x: Coordinate;
    y: Coordinate;
    z: Coordinate;
  }

  interface Position {
    x: number;
    y: number;
    z: number;
  }

  interface ObjectPositions {
    red: Position;
    black: Position;
    green: Position;
    purple: Position;
  }

  type ObjectColor = "red" | "black" | "green" | "purple";

  // Define coordinate ranges for validation
  const ranges: CoordinateRanges = {
    x: { min: 30, max: 80 },
    y: { min: 30, max: 80 },
    z: { min: 0, max: 20 },
  };

  // Set randomized positions for objects that are ~4 units apart from each other
  // Spread objects across the valid range and ensure they don't overlap
  let positions: ObjectPositions = {
    red: { x: 40, y: 40, z: 0 },
    black: { x: 40, y: 70, z: 0 },
    green: { x: 70, y: 40, z: 0 },
    purple: { x: 70, y: 70, z: 0 },
  };

  // Auto-connect on load
  onMount(() => {
    // Wait a brief moment to make sure the environment list is loaded
    setTimeout(() => {
      if (!$isConnected) {
        connect();
      }
    }, 500);
  });

  // Validate and clamp input values to allowed ranges
  function validateInput(
    value: string | number,
    min: number,
    max: number,
  ): number {
    const numValue = Number(value);
    if (isNaN(numValue)) return min;
    return Math.min(Math.max(numValue, min), max);
  }

  // Validation handlers for each coordinate
  function validateX(event: Event, object: ObjectColor): void {
    const target = event.target as HTMLInputElement;
    positions[object].x = validateInput(
      target.value,
      ranges.x.min,
      ranges.x.max,
    );
  }

  function validateY(event: Event, object: ObjectColor): void {
    const target = event.target as HTMLInputElement;
    positions[object].y = validateInput(
      target.value,
      ranges.y.min,
      ranges.y.max,
    );
  }

  function validateZ(event: Event, object: ObjectColor): void {
    const target = event.target as HTMLInputElement;
    positions[object].z = validateInput(
      target.value,
      ranges.z.min,
      ranges.z.max,
    );
  }
</script>

<div class="relative">
  <!-- Main control panel -->
  <div
    class="bg-gray-800 rounded-lg p-4 shadow-lg border border-gray-700 w-60 max-h-[80vh] overflow-y-auto"
  >
    <!-- Panel content -->
    <div class="space-y-4">
      <div class="space-y-2">
        <h3 class="text-sm font-medium text-gray-400">Environment</h3>
        <div class="flex flex-col space-y-2">
          <select
            bind:value={$selectedScene}
            disabled={$isRunning}
            class="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white"
          >
            {#each $scenes as scene}
              <option value={scene.id}>{scene.name}</option>
            {/each}
          </select>
        </div>
      </div>

      {#if $selectedScene === "arm-stack" || $selectedScene === "arm-place"}
        <div class="space-y-4">
          <h3 class="text-sm font-medium text-gray-400">Object Coordinates</h3>
          <p class="text-xs text-gray-400 mb-2">
            Set coordinates (X: 30-80, Y: 30-80, Z: 0-20)
          </p>

          <!-- Table-style coordinate inputs -->
          <div class="w-full">
            <!-- Table Header -->
            <div class="grid grid-cols-4 gap-2 mb-2 text-center">
              <div class="text-xs font-medium text-gray-500">Object</div>
              <div class="text-xs font-medium text-gray-500">X</div>
              <div class="text-xs font-medium text-gray-500">Y</div>
              <div class="text-xs font-medium text-gray-500">Z</div>
            </div>

            <!-- Red Object Row -->
            <div class="grid grid-cols-4 gap-2 mb-2 items-center">
              <div class="text-sm font-medium text-red-400">Red</div>
              <input
                id="redX"
                type="number"
                bind:value={positions.red.x}
                on:blur={(e) => validateX(e, "red")}
                on:change={(e) => validateX(e, "red")}
                min={ranges.x.min}
                max={ranges.x.max}
                disabled={$isRunning}
                class="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white text-sm"
              />
              <input
                id="redY"
                type="number"
                bind:value={positions.red.y}
                on:blur={(e) => validateY(e, "red")}
                on:change={(e) => validateY(e, "red")}
                min={ranges.y.min}
                max={ranges.y.max}
                disabled={$isRunning}
                class="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white text-sm"
              />
              <input
                id="redZ"
                type="number"
                bind:value={positions.red.z}
                on:blur={(e) => validateZ(e, "red")}
                on:change={(e) => validateZ(e, "red")}
                min={ranges.z.min}
                max={ranges.z.max}
                disabled={$isRunning}
                class="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white text-sm"
              />
            </div>

            <!-- Black Object Row -->
            <div class="grid grid-cols-4 gap-2 mb-2 items-center">
              <div class="text-sm font-medium text-gray-400">Black</div>
              <input
                id="blackX"
                type="number"
                bind:value={positions.black.x}
                on:blur={(e) => validateX(e, "black")}
                on:change={(e) => validateX(e, "black")}
                min={ranges.x.min}
                max={ranges.x.max}
                disabled={$isRunning}
                class="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white text-sm"
              />
              <input
                id="blackY"
                type="number"
                bind:value={positions.black.y}
                on:blur={(e) => validateY(e, "black")}
                on:change={(e) => validateY(e, "black")}
                min={ranges.y.min}
                max={ranges.y.max}
                disabled={$isRunning}
                class="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white text-sm"
              />
              <input
                id="blackZ"
                type="number"
                bind:value={positions.black.z}
                on:blur={(e) => validateZ(e, "black")}
                on:change={(e) => validateZ(e, "black")}
                min={ranges.z.min}
                max={ranges.z.max}
                disabled={$isRunning}
                class="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white text-sm"
              />
            </div>

            <!-- Green Object Row -->
            <div class="grid grid-cols-4 gap-2 mb-2 items-center">
              <div class="text-sm font-medium text-green-400">Green</div>
              <input
                id="greenX"
                type="number"
                bind:value={positions.green.x}
                on:blur={(e) => validateX(e, "green")}
                on:change={(e) => validateX(e, "green")}
                min={ranges.x.min}
                max={ranges.x.max}
                disabled={$isRunning}
                class="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white text-sm"
              />
              <input
                id="greenY"
                type="number"
                bind:value={positions.green.y}
                on:blur={(e) => validateY(e, "green")}
                on:change={(e) => validateY(e, "green")}
                min={ranges.y.min}
                max={ranges.y.max}
                disabled={$isRunning}
                class="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white text-sm"
              />
              <input
                id="greenZ"
                type="number"
                bind:value={positions.green.z}
                on:blur={(e) => validateZ(e, "green")}
                on:change={(e) => validateZ(e, "green")}
                min={ranges.z.min}
                max={ranges.z.max}
                disabled={$isRunning}
                class="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white text-sm"
              />
            </div>

            <!-- Purple Object Row -->
            <div class="grid grid-cols-4 gap-2 mb-2 items-center">
              <div class="text-sm font-medium text-purple-400">Purple</div>
              <input
                id="purpleX"
                type="number"
                bind:value={positions.purple.x}
                on:blur={(e) => validateX(e, "purple")}
                on:change={(e) => validateX(e, "purple")}
                min={ranges.x.min}
                max={ranges.x.max}
                disabled={$isRunning}
                class="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white text-sm"
              />
              <input
                id="purpleY"
                type="number"
                bind:value={positions.purple.y}
                on:blur={(e) => validateY(e, "purple")}
                on:change={(e) => validateY(e, "purple")}
                min={ranges.y.min}
                max={ranges.y.max}
                disabled={$isRunning}
                class="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white text-sm"
              />
              <input
                id="purpleZ"
                type="number"
                bind:value={positions.purple.z}
                on:blur={(e) => validateZ(e, "purple")}
                on:change={(e) => validateZ(e, "purple")}
                min={ranges.z.min}
                max={ranges.z.max}
                disabled={$isRunning}
                class="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white text-sm"
              />
            </div>
          </div>
        </div>
      {/if}

      <div class="space-y-2 mt-4">
        <h3 class="text-sm font-medium text-gray-400">Camera Resolution</h3>
        <div class="flex flex-col space-y-2">
          <select
            bind:value={$selectedResolution}
            on:change={() => setResolution($selectedResolution)}
            disabled={!$isConnected}
            class="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white"
          >
            <option value={480}>480p</option>
            <option value={720}>720p</option>
            <option value={1080}>1080p</option>
          </select>
        </div>
      </div>

      <div class="space-y-2 mt-4">
        <h3 class="text-sm font-medium text-gray-400">Connection</h3>
        <div class="flex flex-col space-y-2">
          <button
            on:click={() => {
              if ($isConnected) {
                disconnect();
              } else {
                if (
                  $selectedScene === "arm-stack" ||
                  $selectedScene === "arm-place"
                ) {
                  // Log the positions being sent
                  console.info("Sending object positions:", positions);
                  // Connect with positions data
                  connect(positions);
                } else {
                  // Connect without positions data for other environments
                  connect();
                }
              }
            }}
            disabled={false}
            class="px-4 py-2 bg-gray-700 text-[#F95D03] font-medium border border-gray-600 rounded-md hover:bg-gray-600 hover:border-[#F95D03] disabled:text-gray-500 disabled:border-gray-700 disabled:bg-gray-800 disabled:cursor-not-allowed transition-colors duration-200 relative"
          >
            {$isConnected ? "Disconnect" : "Connect"}
          </button>
        </div>
      </div>

      <!-- Run/Stop control (only available when connected) -->
      <div class="space-y-2 mt-4">
        <h3 class="text-sm font-medium text-gray-400">Robot Control</h3>
        <div class="flex flex-col space-y-2">
          <button
            on:click={() => {
              // If we're in loading state, clicking the button should stop the simulation
              if ($isLoading && $isRunning) {
                toggleRunning(); // This will stop the robot and clear loading state
              } else if (!$isRunning) {
                // If we're starting the robot, pass the object positions for arm environments
                if (
                  $selectedScene === "arm-stack" ||
                  $selectedScene === "arm-place"
                ) {
                  // Log the positions being sent
                  console.info("Sending object positions:", positions);
                  // Start simulation with positions data
                  toggleRunning(positions);
                } else {
                  // Start simulation without positions data for other environments
                  toggleRunning();
                }
              } else {
                // Just toggle (stop) without object positions
                toggleRunning();
              }
            }}
            disabled={!$isConnected}
            class="px-4 py-2 bg-gray-700 font-medium border border-gray-600 rounded-md hover:bg-gray-600 disabled:text-gray-500 disabled:border-gray-700 disabled:bg-gray-800 disabled:cursor-not-allowed transition-colors duration-200 {$isRunning
              ? 'text-red-500 hover:border-red-500'
              : 'text-green-500 hover:border-green-500'}"
          >
            {#if $isLoading && $isRunning}
              <span class="flex items-center justify-center">
                <svg
                  class="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
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
                Loading...
              </span>
            {:else}
              {$isRunning ? "Stop" : "Run"}
            {/if}
          </button>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  /* Remove spinner buttons from number inputs */
  input[type="number"]::-webkit-inner-spin-button,
  input[type="number"]::-webkit-outer-spin-button {
    -webkit-appearance: none;
    margin: 0;
  }

  input[type="number"] {
    appearance: textfield;
    -moz-appearance: textfield; /* Firefox */
  }
</style>

