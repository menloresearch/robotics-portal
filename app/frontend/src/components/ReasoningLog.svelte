<script lang="ts">
  import { reasoningMessages } from "$lib/store";
  import { onMount } from "svelte";
  import { formatRobotCommandText } from "$lib/parser";

  let isReasoningExpanded = false;
  let parsedMessages: string = "";

  // Subscribe to reasoningMessages to detect changes
  onMount(() => {
    let prevLength = 0;

    const unsubscribe = reasoningMessages.subscribe((messages) => {
      // Parse the messages
      // parsedMessages = formatRobotCommandText(messages);
      parsedMessages = messages;

      // Only expand if there are new messages (length increased) and not just when sending a command
      if (
        messages.length > 0 &&
        messages.length > prevLength &&
        !isReasoningExpanded
      ) {
        isReasoningExpanded = true;
      }
      prevLength = messages.length;
    });

    return unsubscribe;
  });

  function toggleReasoning() {
    isReasoningExpanded = !isReasoningExpanded;
  }
</script>

<div
  class="bg-gray-800 rounded-lg p-4 flex flex-col border border-gray-700 shadow-lg"
>
  <div class="space-y-4 flex-grow flex flex-col">
    <!-- Reasoning toggle button -->
    <button
      on:click={toggleReasoning}
      class="flex items-center justify-between w-full text-left text-sm font-medium text-[#F95D03] hover:text-opacity-80 mb-2"
    >
      <span>Reasoning</span>
      <span class="material-icons">{isReasoningExpanded ? "↓" : "→"}</span>
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
            {@html parsedMessages}
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

