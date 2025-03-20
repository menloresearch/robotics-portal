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
  } from "$lib/store";
</script>

<div class="bg-gray-800 rounded-lg p-4">
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
      <span>Environment:</span>
      <span class="font-semibold">
        {$environments.find((env) => env.id === $selectedEnvironment)?.name ||
          $selectedEnvironment}
      </span>
    </div>
  </div>
</div>
