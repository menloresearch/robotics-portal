<script lang="ts">
  import { instruction, reasoningMessages, isConnected } from "$lib/store";
  import { sendCommand } from "$lib/connection";
  import { onMount } from "svelte";

  let isReasoningExpanded = false;
  
  // Subscribe to reasoningMessages to detect changes
  onMount(() => {
    let prevLength = 0;
    
    const unsubscribe = reasoningMessages.subscribe(messages => {
      // Only expand if there are new messages (length increased) and not just when sending a command
      if (messages.length > 0 && messages.length > prevLength && !isReasoningExpanded) {
        isReasoningExpanded = true;
      }
      prevLength = messages.length;
    });
    
    return unsubscribe;
  });

  function handleSendCommand() {
    if (sendCommand($instruction)) {
      // Don't auto-expand when sending - wait for response
      instruction.set("");
    }
  }

  function toggleReasoning() {
    isReasoningExpanded = !isReasoningExpanded;
  }
</script>

<div class="bg-gray-800 rounded-lg p-4 flex flex-col border border-gray-700 shadow-lg">
  <div class="space-y-4 flex-grow flex flex-col">
    <!-- Reasoning toggle button -->
    <button 
      on:click={toggleReasoning}
      class="flex items-center justify-between w-full text-left text-sm font-medium text-[#F95D03] hover:text-opacity-80 mb-2"
    >
      <span>Reasoning</span>
      <span class="material-icons">{isReasoningExpanded ? '↓' : '→'}</span>
    </button>

    <!-- Collapsible reasoning section -->
    {#if isReasoningExpanded}
      <div
        id="reasoning-box"
        class="h-96 bg-gray-700 rounded-md p-3 overflow-y-auto flex-grow transition-all duration-300"
      >
        {#if $reasoningMessages.length === 0}
          <div class="text-gray-400 italic">Reasoning...</div>
        {:else}
          <div class="mb-2 text-sm whitespace-pre-wrap">
            {$reasoningMessages}
          </div>
        {/if}
      </div>
    {/if}
    
    <div class="flex gap-2 mt-auto w-full">
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
</div>
