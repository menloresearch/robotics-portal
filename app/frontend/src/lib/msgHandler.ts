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

    // Create an image from the base64 data
    const now = performance.now();
    const img = new Image();

    img.onload = () => {
      // Draw image on canvas
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

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
    };

    // Set the source to the base64 image data
    img.src = `data:image/jpeg;base64,${image}`;
  });
}
