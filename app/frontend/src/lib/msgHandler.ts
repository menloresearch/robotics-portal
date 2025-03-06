export function viewRender(
	image,
	ctx,
	canvas,
	frameCount,
	lastFrameTime,
	fpsArray,
	fps,
	latencyArray,
	latency,
) {
	return new Promise((resolve) => {
		// Create an image from the base64 data
		const now = performance.now();
		const img = new Image();

		img.onload = () => {
			// Draw image on canvas
			ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

			// Update metrics
			frameCount += 1;

			// Calculate FPS
			const elapsed = now - lastFrameTime;
			if (lastFrameTime !== 0) {
				const currentFps = 1000 / elapsed;
				fpsArray.push(currentFps);
				if (fpsArray.length > 30) fpsArray.shift();
				fps = (
					fpsArray.reduce((a: number, b: number) => a + b, 0) / fpsArray.length
				).toFixed(1);
			}

			// Estimate latency using client-side timestamps
			const currentLatency = performance.now() - now;
			latencyArray.push(currentLatency);
			if (latencyArray.length > 30) latencyArray.shift();
			latency = (
				latencyArray.reduce((a: number, b: number) => a + b, 0) /
				latencyArray.length
			).toFixed(1);

			// Return updated values
			resolve([frameCount, now, fps, latency]);
		};

		// Set the source to the base64 image data
		img.src = `data:image/jpeg;base64,${image}`;
	});
}
