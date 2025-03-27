<script lang="ts">
  import {
    connectionStatus,
    statusColor,
    frameCount,
    fps,
    latency,
    frameSize,
    selectedEnvironment,
    environments,
    frameBuffer,
    isBuffering,
    bufferSize
  } from "$lib/store";
  
  // Calculate buffer information
  $: bufferFrameCount = $frameBuffer.length;
  $: bufferStatus = $isBuffering ? "Buffering..." : "Streaming";
  $: bufferSeconds = $bufferSize;
</script>

<div class="p-4">
  <h2 class="text-xl font-semibold mb-4">Telemetry</h2>
  <div class="space-y-2 font-mono text-sm">
    <div class="flex justify-between">
      <span>Connection:</span>
      <span class={$statusColor}>{$connectionStatus}</span>
    </div>
    <div class="flex justify-between">
      <span>Frames:</span>
      <span class="font-semibold">{$frameCount}</span>
    </div>
    <div class="flex justify-between">
      <span>FPS:</span>
      <span class="font-semibold">{$fps}</span>
    </div>
    <div class="flex justify-between">
      <span>Latency:</span>
      <span class="font-semibold">{$latency} ms</span>
    </div>
    <div class="flex justify-between">
      <span>Frame Size:</span>
      <span class="font-semibold">{$frameSize} KB</span>
    </div>
    <div class="flex justify-between">
      <span>Buffer:</span>
      <span class={$isBuffering ? "text-yellow-400 font-semibold" : "font-semibold"}>
        {bufferFrameCount} frames ({bufferStatus})
      </span>
    </div>
    <div class="flex justify-between">
      <span>Buffer Size:</span>
      <span class="font-semibold">{bufferSeconds}s</span>
    </div>
    <div class="flex justify-between">
      <span>Environment:</span>
      <span class="font-semibold">
        {$environments.find((env) => env.id === $selectedEnvironment)?.name ||
          $selectedEnvironment}
      </span>
    </div>
  </div>
</div>
