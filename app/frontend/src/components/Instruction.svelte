<script lang="ts">
  import { instruction, reasoningMessages, isConnected } from "$lib/store";
  import { sendCommand } from "$lib/connection";

  function handleSendCommand() {
    if (sendCommand($instruction)) {
      instruction.set("");
    }
  }
</script>

<div class="bg-gray-800 rounded-lg p-4 flex flex-col">
  <h2 class="text-xl font-semibold mb-4">Frontal cortex</h2>
  <div class="space-y-4 flex-grow flex flex-col">
    <div
      id="reasoning-box"
      class="h-96 bg-gray-700 rounded-md p-3 overflow-y-auto flex-grow"
    >
      {#if $reasoningMessages.length === 0}
        <div class="text-gray-400 italic">Reasoning...</div>
      {:else}
        <div class="mb-2 text-sm whitespace-pre-wrap">
          {$reasoningMessages}
        </div>
      {/if}
    </div>
    <div class="flex flex-col gap-2 mt-auto w-full">
      <input
        type="text"
        bind:value={$instruction}
        placeholder="Instruction..."
        class="w-full px-3 py-2 bg-gray-700 rounded-md border border-gray-600 focus:outline-none focus:border-blue-500"
        on:keydown={(e) => e.key === "Enter" && handleSendCommand()}
      />
      <button
        on:click={handleSendCommand}
        disabled={!$isConnected}
        class="w-full sm:w-auto px-4 py-2 bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed"
      >
        Send
      </button>
    </div>
  </div>
</div>
