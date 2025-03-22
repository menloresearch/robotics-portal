import { get } from "svelte/store";
import {
  frameCount as frameCountStore,
  lastFrameTime as lastFrameTimeStore,
  fpsArray as fpsArrayStore,
  fps as fpsStore,
  latencyArray as latencyArrayStore,
  latency as latencyStore,
} from "./store";

export function viewRender(
  image: string,
  ctx: CanvasRenderingContext2D,
  canvas: HTMLCanvasElement,
) {
  return new Promise((resolve) => {
    // Get current store values
    let frameCount = get(frameCountStore);
    let lastFrameTime = get(lastFrameTimeStore);
    let fpsArray = get(fpsArrayStore);
    let latencyArray = get(latencyArrayStore);

    const now = performance.now();

    // Convert base64 to binary
    const base64 = image;
    const binary = atob(base64);
    const len = binary.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binary.charCodeAt(i);
    }

    // Create blob and bitmap
    const blob = new Blob([bytes.buffer], { type: "image/jpeg" });

    createImageBitmap(blob).then((bitmap) => {
      // Draw bitmap directly - more efficient than Image
      ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);

      // Update metrics
      frameCount += 1;
      frameCountStore.set(frameCount);

      // Calculate FPS
      const elapsed = now - lastFrameTime;
      if (lastFrameTime !== 0) {
        const currentFps = 1000 / elapsed;
        fpsArray.push(currentFps);
        if (fpsArray.length > 30) fpsArray.shift();
        const newFps = (
          fpsArray.reduce((a: number, b: number) => a + b, 0) / fpsArray.length
        ).toFixed(1);
        fpsStore.set(newFps);
        fpsArrayStore.set(fpsArray);
      }

      // Store the last frame time
      lastFrameTimeStore.set(now);

      // Estimate latency using client-side timestamps
      const currentLatency = performance.now() - now;
      latencyArray.push(currentLatency);
      if (latencyArray.length > 30) latencyArray.shift();
      const newLatency = (
        latencyArray.reduce((a: number, b: number) => a + b, 0) /
        latencyArray.length
      ).toFixed(1);
      latencyStore.set(newLatency);
      latencyArrayStore.set(latencyArray);

      // Resolve promise
      resolve(true);
    });
  });
}
