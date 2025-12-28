import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { PythonWorkerBridge } from "./bridge/pythonProc.js";

const NotifySendSchema = z.object({
  title: z.string().describe("Notification title"),
  content: z.string().describe("Notification content"),
  ignore_default_config: z.boolean().optional().describe("Ignore default push config"),
});

const NotifyEventSchema = z.object({
  run_id: z.string().describe("Unique task identifier"),
  event: z.enum(["start", "update", "end", "error"]).describe("Event type"),
  message: z.string().describe("Event message"),
  timestamp: z.string().optional().describe("ISO 8601 timestamp"),
  data: z.record(z.unknown()).optional().describe("Additional structured data"),
});

export class McpPushServer {
  private server: Server;
  private bridge: PythonWorkerBridge;

  constructor() {
    this.server = new Server(
      {
        name: "mcp-push",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.bridge = new PythonWorkerBridge();
    this.setupToolHandlers();

    this.server.onerror = (error) => {
      console.error("[MCP Error]", error);
    };

    process.on("SIGINT", async () => {
      await this.stop();
      process.exit(0);
    });
  }

  private setupToolHandlers(): void {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "notify.send",
          description:
            "Send notification to all configured channels (DingTalk, Feishu, Telegram, WeChat, Email, etc.)",
          inputSchema: {
            type: "object",
            properties: {
              title: {
                type: "string",
                description: "Notification title",
              },
              content: {
                type: "string",
                description: "Notification content",
              },
              ignore_default_config: {
                type: "boolean",
                description: "Ignore default push config",
              },
            },
            required: ["title", "content"],
          },
        },
        {
          name: "notify.event",
          description:
            "Send structured task event notification with run_id tracking (start, update, end, error)",
          inputSchema: {
            type: "object",
            properties: {
              run_id: {
                type: "string",
                description: "Unique task identifier",
              },
              event: {
                type: "string",
                enum: ["start", "update", "end", "error"],
                description: "Event type",
              },
              message: {
                type: "string",
                description: "Event message",
              },
              timestamp: {
                type: "string",
                description: "ISO 8601 timestamp (optional, auto-generated if not provided)",
              },
              data: {
                type: "object",
                description: "Additional structured data (e.g., progress, step, artifact_url)",
              },
            },
            required: ["run_id", "event", "message"],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        let result: unknown;

        if (name === "notify.send") {
          const params = NotifySendSchema.parse(args);
          result = await this.bridge.callTool("notify.send", params);
        } else if (name === "notify.event") {
          const params = NotifyEventSchema.parse(args);
          result = await this.bridge.callTool("notify.event", params);
        } else {
          throw new Error(`Unknown tool: ${name}`);
        }

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ error: errorMessage }, null, 2),
            },
          ],
          isError: true,
        };
      }
    });
  }

  async start(): Promise<void> {
    await this.bridge.start();

    const transport = new StdioServerTransport();
    await this.server.connect(transport);

    console.error("MCP Push Server running on stdio");
  }

  async stop(): Promise<void> {
    await this.bridge.stop();
    await this.server.close();
  }
}
