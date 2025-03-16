<script lang="ts">
  import ControlPanel from "../components/ControlPanel.svelte";
  import Telemetry from "../components/Telemetry.svelte";
  import MainView from "../components/MainView.svelte";
  import SecondaryView from "../components/SecondaryView.svelte";
  import Instruction from "../components/Instruction.svelte";
</script>

<div class="grid grid-cols-12 gap-4">
  <!-- Left Side Panels - Control Panel and Telemetry -->
  <div class="col-span-2 space-y-4">
    <ControlPanel />
    <Telemetry />
  </div>

  <!-- Main Content Area -->
  <div class="col-span-7 space-y-4">
    <MainView />
  </div>

  <!-- Right Side Panels -->
  <div class="col-span-3 space-y-4">
    <SecondaryView />
    <Instruction />
  </div>
</div>
