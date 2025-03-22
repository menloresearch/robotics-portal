import { get } from "svelte/store";
import { socket } from "./store";

export function handleZoom(event: WheelEvent) {
  const currentSocket = get(socket);
  if (!currentSocket || currentSocket.readyState !== WebSocket.OPEN) return;

  // Prevent default scrolling behavior
  event.preventDefault();

  // Determine zoom direction based on wheel delta
  const zoomDirection = event.deltaY < 0 ? "in" : "out";

  currentSocket.send(
    JSON.stringify({
      type: "zoom",
      direction: zoomDirection,
    }),
  );
}

