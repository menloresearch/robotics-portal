<script lang="ts">
  import ControlPanel from "../components/ControlPanel.svelte";
  import Telemetry from "../components/Telemetry.svelte";
  import MainView from "../components/MainView.svelte";
  import SecondaryView from "../components/SecondaryView.svelte";
  import InputBox from "../components/InputBox.svelte";
  import ReasoningLog from "../components/ReasoningLog.svelte";
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

    <!-- Secondary View, Telemetry, and Reasoning Log -->
    <div class="absolute right-6 top-6 pointer-events-auto max-w-sm">
      <div class="space-y-4">
        <!-- Secondary View and Telemetry in a bordered container -->
        <div
          class="bg-gray-800 rounded-lg border border-gray-700 shadow-lg overflow-hidden"
        >
          <div class="p-2 space-y-4">
            <SecondaryView />
            <Telemetry />
          </div>
        </div>
        <!-- Reasoning Log below -->
        <ReasoningLog />
      </div>
    </div>

    <!-- Input Box at middle-bottom -->
    <div
      class="absolute bottom-6 left-1/2 -translate-x-1/2 pointer-events-auto max-w-2xl w-full px-4"
    >
      <InputBox />
    </div>
  </div>
</div>
