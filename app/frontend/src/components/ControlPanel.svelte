<script lang="ts">
  import {
    selectedEnvironment,
    environments,
    isConnected,
    isLoading,
  } from "$lib/store";
  import {
    connect,
    disconnect,
    switchCamera,
    setFrameRate,
  } from "$lib/connection";
</script>

<div class="bg-gray-800 rounded-lg p-4">
  <h2 class="text-xl font-semibold mb-4">Control Panel</h2>

  <div class="space-y-4">
    <div class="space-y-2">
      <h3 class="text-sm font-medium text-gray-400">Environment</h3>
      <div class="flex flex-col space-y-2">
        <select
          bind:value={$selectedEnvironment}
          disabled={$isConnected}
          class="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded-md text-white"
        >
          {#each $environments as env}
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
          disabled={$isConnected || $isLoading}
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed relative"
        >
          {#if $isLoading}
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
              Connecting...
            </span>
          {:else}
            Connect
          {/if}
        </button>
        <button
          on:click={disconnect}
          disabled={!$isConnected}
          class="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:bg-gray-700 disabled:cursor-not-allowed"
        >
          Disconnect
        </button>
      </div>
    </div>

    <div class="space-y-2">
      <h3 class="text-sm font-medium text-gray-400">Frame Rate Control</h3>
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
          on:click={() => {
            const input = document.getElementById(
              "fpsInput",
            ) as HTMLInputElement;
            setFrameRate(input.value);
          }}
          disabled={!$isConnected}
          class="px-2 py-1 bg-gray-700 rounded-md hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          Set FPS
        </button>
      </div>
    </div>

    <div class="space-y-2">
      <h3 class="text-sm font-medium text-gray-400">Camera Selection</h3>
      <div class="grid grid-cols-1 gap-2">
        <button
          on:click={() => switchCamera(0)}
          disabled={!$isConnected}
          class="px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed"
        >
          First person view
        </button>
        <button
          on:click={() => switchCamera(1)}
          disabled={!$isConnected}
          class="px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:bg-gray-700 disabled:cursor-not-allowed"
        >
          Third person view
        </button>
      </div>
    </div>
  </div>
</div>

