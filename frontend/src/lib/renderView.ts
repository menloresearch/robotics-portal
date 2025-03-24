import { get } from "svelte/store";
import {
  frameCount as frameCountStore,
  fps as fpsStore,
  latencyArray as latencyArrayStore,
  latency as latencyStore,
  framesInLastSecond as framesInLastSecondStore,
  mainCtx as mainCtxStore,
  mainCanvas as mainCanvasStore,
  secondaryCtx as secondaryCtxStore,
  secondaryCanvas as secondaryCanvasStore,
} from "./store";

/**
 * Renders a single view to a canvas
 */
async function renderSingleView(
  imageData: string,
  ctx: CanvasRenderingContext2D,
  canvas: HTMLCanvasElement,
): Promise<void> {
  // Convert base64 to binary
  const binary = atob(imageData);
  const len = binary.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binary.charCodeAt(i);
  }

  // Create blob and bitmap
  const blob = new Blob([bytes.buffer], { type: "image/jpeg" });
  const bitmap = await createImageBitmap(blob);

  // Draw bitmap directly - more efficient than Image
  ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
}

/**
 * Renders both main and secondary views in a single operation
 */
export function renderView(mainViewImage: string, secondaryViewImage: string) {
  return new Promise<boolean>(async (resolve) => {
    // Get current store values
    let frameCount = get(frameCountStore);
    let latencyArray = get(latencyArrayStore);
    let framesInLastSecond = get(framesInLastSecondStore);

    // Get canvas contexts
    const mainCtx = get(mainCtxStore);
    const mainCanvas = get(mainCanvasStore);
    const secondaryCtx = get(secondaryCtxStore);
    const secondaryCanvas = get(secondaryCanvasStore);

    const now = performance.now();

    // Render both views in parallel
    const renderPromises: Promise<void>[] = [];

    if (mainCtx && mainCanvas) {
      renderPromises.push(renderSingleView(mainViewImage, mainCtx, mainCanvas));
    }

    if (secondaryCtx && secondaryCanvas) {
      renderPromises.push(
        renderSingleView(secondaryViewImage, secondaryCtx, secondaryCanvas),
      );
    }

    // Wait for both renders to complete
    await Promise.all(renderPromises);

    // Update metrics (only count once per frame pair)
    frameCount += 1;
    frameCountStore.set(frameCount);

    // Track frames with timestamps for FPS calculation
    framesInLastSecond.push(now);

    // Use a shorter 500ms window for more responsive FPS calculation
    const halfSecondAgo = now - 500;
    framesInLastSecond = framesInLastSecond.filter(
      (timestamp) => timestamp > halfSecondAgo,
    );

    // Calculate instantaneous FPS based on frames in the last 500ms with greater precision
    const framesInHalfSecond = framesInLastSecond.length;

    // For more accuracy, calculate time span between oldest and newest frame
    // This gives a more precise measurement than using exactly 500ms
    let timeSpan = 500; // Default to 500ms if fewer than 2 frames

    if (framesInLastSecond.length >= 2) {
      // Sort timestamps and calculate actual timespan
      const sortedFrames = [...framesInLastSecond].sort((a, b) => a - b);
      const oldestFrame = sortedFrames[0];
      const newestFrame = sortedFrames[sortedFrames.length - 1];
      timeSpan = newestFrame - oldestFrame;

      // Ensure we don't divide by zero or very small numbers
      if (timeSpan < 50) timeSpan = 500;
    }

    // Calculate precise FPS with one decimal place
    const preciseTimespan = timeSpan / 1000; // convert to seconds
    const preciseFps = (framesInHalfSecond / preciseTimespan).toFixed(1);

    // Update FPS display with decimal precision
    fpsStore.set(preciseFps);

    // Store the frame timestamps for next calculation
    framesInLastSecondStore.set(framesInLastSecond);

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
}
