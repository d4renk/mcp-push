import { spawn, ChildProcess } from "child_process";
import { Socket } from "net";
import { readFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface JsonRpcRequest {
  id: string;
  method: string;
  params: Record<string, unknown>;
}

interface JsonRpcResponse {
  id: string | null;
  result: unknown;
  error: { message: string } | null;
}

const MAX_FRAME_SIZE = 10 * 1024 * 1024; // 10 MB limit

export class PythonWorkerBridge {
  private worker: ChildProcess | null = null;
  private socket: Socket | null = null;
  private socketPath: string | null = null;
  private pendingRequests = new Map<
    string,
    {
      resolve: (value: unknown) => void;
      reject: (error: Error) => void;
      timeout: NodeJS.Timeout;
    }
  >();
  private frameBuffer = Buffer.alloc(0);
  private currentFrameLength: number | null = null;
  private shuttingDown = false;

  async start(): Promise<void> {
    const pythonPath = join(__dirname, "../../../../start_worker.py");

    this.worker = spawn("python3", [pythonPath], {
      stdio: ["ignore", "pipe", "pipe"],
      env: { ...process.env },
    });

    this.worker.stderr?.on("data", (data: Buffer) => {
      process.stderr.write(`[Python Worker] ${data.toString()}`);
    });

    this.worker.on("exit", (code) => {
      console.error(`Python worker exited with code ${code}`);
      this.cleanup();
      if (!this.shuttingDown) {
        setTimeout(() => this.start(), 1000);
      }
    });

    this.socketPath = await this.waitForSocketPath();
    await this.connectSocket();
  }

  private async waitForSocketPath(): Promise<string> {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error("Timeout waiting for socket path"));
      }, 10000);

      const handler = (data: Buffer) => {
        const output = data.toString();
        const match = output.match(/Worker listening on (\/tmp\/mcp-push-\d+\.sock)/);
        if (match) {
          clearTimeout(timeout);
          this.worker?.stderr?.removeListener("data", handler);
          resolve(match[1]);
        }
      };

      this.worker?.stderr?.on("data", handler);
    });
  }

  private async connectSocket(): Promise<void> {
    if (!this.socketPath) throw new Error("Socket path not available");

    this.socket = new Socket();

    this.socket.on("data", (chunk: Buffer) => {
      this.handleSocketData(chunk);
    });

    this.socket.on("error", (err) => {
      console.error("Socket error:", err);
    });

    this.socket.on("close", () => {
      console.error("Socket closed");
      this.cleanup();
    });

    await new Promise<void>((resolve, reject) => {
      this.socket!.connect(this.socketPath!, () => {
        resolve();
      });
      this.socket!.once("error", reject);
    });
  }

  private handleSocketData(chunk: Buffer): void {
    this.frameBuffer = Buffer.concat([this.frameBuffer, chunk]);

    while (true) {
      if (this.currentFrameLength === null) {
        const headerEnd = this.frameBuffer.indexOf("\r\n\r\n");
        if (headerEnd === -1) break;

        const headerStr = this.frameBuffer.subarray(0, headerEnd).toString("ascii");
        const lengthMatch = headerStr.match(/Content-Length:\s*(\d+)/i);

        if (!lengthMatch) {
          console.error("Invalid frame header");
          this.frameBuffer = Buffer.alloc(0);
          break;
        }

        this.currentFrameLength = parseInt(lengthMatch[1], 10);
        if (this.currentFrameLength > MAX_FRAME_SIZE) {
          console.error(`Frame size ${this.currentFrameLength} exceeds maximum ${MAX_FRAME_SIZE}`);
          this.socket?.destroy();
          break;
        }
        this.frameBuffer = this.frameBuffer.subarray(headerEnd + 4);
      }

      if (this.frameBuffer.length < this.currentFrameLength) break;

      const body = this.frameBuffer.subarray(0, this.currentFrameLength);
      this.frameBuffer = this.frameBuffer.subarray(this.currentFrameLength);
      this.currentFrameLength = null;

      try {
        const response: JsonRpcResponse = JSON.parse(body.toString("utf-8"));
        this.handleResponse(response);
      } catch (err) {
        console.error("Failed to parse response:", err);
      }
    }
  }

  private handleResponse(response: JsonRpcResponse): void {
    if (!response.id) return;

    const pending = this.pendingRequests.get(response.id);
    if (!pending) return;

    this.pendingRequests.delete(response.id);
    clearTimeout(pending.timeout);

    if (response.error) {
      pending.reject(new Error(response.error.message));
    } else {
      pending.resolve(response.result);
    }
  }

  async callTool(method: string, params: Record<string, unknown>): Promise<unknown> {
    if (!this.socket) throw new Error("Socket not connected");

    const id = Math.random().toString(36).substring(2);
    const request: JsonRpcRequest = { id, method, params };

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error("Request timeout after 60s"));
        }
      }, 60000);

      this.pendingRequests.set(id, { resolve, reject, timeout });

      const body = Buffer.from(JSON.stringify(request), "utf-8");
      const header = Buffer.from(`Content-Length: ${body.length}\r\n\r\n`, "ascii");

      this.socket!.write(Buffer.concat([header, body]), (err) => {
        if (err) {
          const pending = this.pendingRequests.get(id);
          if (pending) {
            clearTimeout(pending.timeout);
            this.pendingRequests.delete(id);
          }
          reject(err);
        }
      });
    });
  }

  private cleanup(): void {
    this.socket?.destroy();
    this.socket = null;
    this.pendingRequests.forEach(({ reject, timeout }) => {
      clearTimeout(timeout);
      reject(new Error("Worker connection closed"));
    });
    this.pendingRequests.clear();
  }

  async stop(): Promise<void> {
    this.shuttingDown = true;
    this.cleanup();
    if (this.worker) {
      this.worker.kill();
      this.worker = null;
    }
  }
}
