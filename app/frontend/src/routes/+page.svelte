<script lang="ts">
  import ControlPanel from "../components/ControlPanel.svelte";
  import Telemetry from "../components/Telemetry.svelte";
  import MainView from "../components/MainView.svelte";
  import SecondaryView from "../components/SecondaryView.svelte";
  import Instruction from "../components/Instruction.svelte";
</script>

<div class="relative h-screen w-screen overflow-hidden">
  <!-- Full screen background MainView -->
  <MainView />

  <!-- Floating UI components with z-index to appear above MainView -->
  <div class="fixed inset-0 pointer-events-none">
    <!-- Left floating control panel centered vertically with slide animation -->
    <div class="absolute left-6 top-1/2 -translate-y-1/2 pointer-events-auto">
      <ControlPanel />
    </div>

    <!-- Telemetry positioned at bottom left -->
    <div class="absolute left-6 bottom-6 pointer-events-auto">
      <Telemetry />
    </div>

    <!-- Secondary View and Instruction -->
    <div
      class="absolute right-6 top-[calc(210px+1.5rem)] pointer-events-auto max-w-sm"
    >
      <div class="space-y-4">
        <SecondaryView />
        <Instruction />
      </div>
    </div>
  </div>
</div>
