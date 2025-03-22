<script lang="ts">
  import "../app.css";
  import { onDestroy } from "svelte";
  import { socket } from "$lib/store";
  import { get } from "svelte/store";

  let { children } = $props();

  // Clean up WebSocket connection when layout is destroyed
  onDestroy(() => {
    const currentSocket = get(socket);
    if (currentSocket) {
      currentSocket.close();
    }
  });
</script>

<div class="min-h-screen min-w-screen bg-gray-900 text-white p-4">
  <h1 class="text-2xl font-bold mb-8">Portal</h1>

  {@render children()}
</div>
