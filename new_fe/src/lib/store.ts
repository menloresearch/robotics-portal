import { writable } from "svelte/store";

// WebSocket connection
export const socket = writable<WebSocket | null>(null);
export const connectionStatus = writable<string>("Disconnected");
export const statusColor = writable<string>("text-red-500");
export const isConnected = writable<boolean>(false);
export const isLoading = writable<boolean>(false);
export const receivedFirstFrame = writable<boolean>(false);

// Environment settings
export const selectedScene = writable<string>("");
export const scenes = writable([]);

// Telemetry data
export const frameCount = writable<number>(0);
export const fps = writable<string>("0");
export const latency = writable<string>("0");
export const frameSize = writable<string>("0");
export const latencyArray = writable<number[]>([]);
export const framesInLastSecond = writable<number[]>([]);
export const selectedResolution = writable<number>(720);

// Frame buffer settings
export interface FrameData {
  mainView: string;
  secondaryView: string;
  timestamp: number;
}
export const frameBuffer = writable<FrameData[]>([]);
export const isBuffering = writable<boolean>(true);

// Canvas references
export const mainCanvas = writable<HTMLCanvasElement | null>(null);
export const mainCtx = writable<CanvasRenderingContext2D | null>(null);
export const secondaryCanvas = writable<HTMLCanvasElement | null>(null);
export const secondaryCtx = writable<CanvasRenderingContext2D | null>(null);

// Instruction and reasoning
export const instruction = writable<string>("");
export const reasoningMessages = writable<string>("");

// Robot state
export const isRunning = writable<boolean>(false);
