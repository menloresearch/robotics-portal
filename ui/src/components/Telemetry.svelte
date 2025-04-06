<script lang="ts">
  import {
    connectionStatus,
    statusColor,
    frameCount,
    fps,
    latency,
    frameSize,
    selectedScene,
    scenes,
  } from "$lib/store";
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
      <span>Environment:</span>
      <span class="font-semibold">
        {$scenes.find((scene) => scene.id === $selectedScene)?.name ||
          $selectedScene}
      </span>
    </div>
  </div>
</div>
