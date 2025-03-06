export function handleZoom(socket: WebSocket, event: WheelEvent) {
  if (!socket || socket.readyState !== WebSocket.OPEN) return;

  // Prevent default scrolling behavior
  event.preventDefault();

  // Determine zoom direction based on wheel delta
  const zoomDirection = event.deltaY < 0 ? "in" : "out";

  socket.send(
    JSON.stringify({
      type: "zoom",
      direction: zoomDirection,
    }),
  );
}

// function handleMouseDown(socket: WebSocket, event: MouseEvent) {
//   if (!socket || socket.readyState !== WebSocket.OPEN) return;
//
//   isDragging = true;
//   lastMouseX = event.clientX;
//   lastMouseY = event.clientY;
// }
//
// function handleMouseMove(event: MouseEvent) {
//   if (!isDragging || !socket || socket.readyState !== WebSocket.OPEN) return;
//
//   const deltaX = event.clientX - lastMouseX;
//   const deltaY = event.clientY - lastMouseY;
//
//   // Calculate relative movement (as percentage of canvas size)
//   const relativeX = deltaX / canvas.width;
//   const relativeY = deltaY / canvas.height;
//
//   // Send pan message to server
//   socket.send(
//     JSON.stringify({
//       type: "pan",
//       delta: [relativeY, relativeX, 0],
//     }),
//   );
//
//   lastMouseX = event.clientX;
//   lastMouseY = event.clientY;
// }
//
// function handleMouseUp() {
//   isDragging = false;
// }
