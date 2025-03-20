<script lang="ts">
  import { instruction, isConnected } from "$lib/store";
  import { sendCommand } from "$lib/connection";

  function handleSendCommand() {
    if (sendCommand($instruction)) {
      instruction.set("");
    }
  }
</script>

<div class="bg-gray-800 rounded-lg p-4 flex flex-col border border-gray-700 shadow-lg">
  <div class="flex gap-2 w-full">
    <input
      type="text"
      bind:value={$instruction}
      placeholder="Instruction..."
      class="flex-grow px-3 py-2 bg-gray-700 rounded-md border border-gray-600 focus:outline-none focus:border-blue-500"
      on:keydown={(e) => e.key === "Enter" && handleSendCommand()}
    />
    <button
      on:click={handleSendCommand}
      disabled={!$isConnected}
      class="px-4 py-2 bg-gray-700 text-[#F95D03] font-medium border border-gray-600 rounded-md hover:bg-gray-600 hover:border-[#F95D03] disabled:text-gray-500 disabled:border-gray-700 disabled:bg-gray-800 disabled:cursor-not-allowed whitespace-nowrap transition-colors duration-200"
    >
      Send
    </button>
  </div>
</div>