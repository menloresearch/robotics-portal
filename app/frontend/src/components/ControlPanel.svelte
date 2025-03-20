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

  let isExpanded = true;

  function togglePanel() {
    isExpanded = !isExpanded;
  }
</script>

<div class="relative">
  <!-- Control panel + tab as a single unit that animates together -->
  <div
    class="flex items-stretch transition-transform duration-500 ease-in-out"
    class:translate-x-0={isExpanded}
    class:-translate-x-[calc(100%-16px)]={!isExpanded}
  >
    <!-- Main control panel -->
    <div
      class="bg-gray-800 rounded-l-lg p-4 shadow-lg border border-gray-700 max-w-xs max-h-[80vh] overflow-y-auto"
    >
      <!-- Panel content -->
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
              class="px-4 py-2 bg-gray-700 text-[#F95D03] font-medium border border-gray-600 rounded-md hover:bg-gray-600 hover:border-[#F95D03] disabled:text-gray-500 disabled:border-gray-700 disabled:bg-gray-800 disabled:cursor-not-allowed transition-colors duration-200 relative"
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
              class="px-4 py-2 bg-gray-700 text-[#F95D03] font-medium border border-gray-600 rounded-md hover:bg-gray-600 hover:border-[#F95D03] disabled:text-gray-500 disabled:border-gray-700 disabled:bg-gray-800 disabled:cursor-not-allowed transition-colors duration-200"
            >
              Disconnect
            </button>
          </div>
        </div>

        <div class="space-y-2">
          <h3 class="text-sm font-medium text-gray-400">FPS</h3>
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
              class="px-2 py-1 bg-gray-700 text-[#F95D03] font-medium border border-gray-600 rounded-md hover:bg-gray-600 hover:border-[#F95D03] disabled:text-gray-500 disabled:border-gray-700 disabled:bg-gray-800 disabled:cursor-not-allowed text-sm transition-colors duration-200"
            >
              Set FPS
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Vertical "Control" tab attached to the panel -->
    <button
      on:click={togglePanel}
      class="bg-gray-800 text-[#F95D03] py-6 px-3 rounded-r-lg border-t border-r border-b border-gray-700 shadow-lg flex items-center justify-center self-center h-44 w-10 cursor-pointer hover:brightness-110 transition-all"
    >
      <div class="vertical-text font-medium text-sm">CONTROL</div>
    </button>
  </div>

  <style>
    .vertical-text {
      writing-mode: vertical-lr;
      text-orientation: upright;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
  </style>
</div>
