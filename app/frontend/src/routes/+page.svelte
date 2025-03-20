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
    <div class="container mx-auto h-full p-4">
      <div class="grid grid-cols-12 gap-4 h-full pointer-events-none">
        <!-- Left Side Panels - Control Panel and Telemetry -->
        <div class="col-span-2 space-y-4 pointer-events-auto">
          <ControlPanel />
          <Telemetry />
        </div>

        <!-- Empty middle space -->
        <div class="col-span-7"></div>

        <!-- Right Side Panels -->
        <div class="col-span-3 space-y-4 pointer-events-auto">
          <SecondaryView />
          <Instruction />
        </div>
      </div>
    </div>
  </div>
</div>
