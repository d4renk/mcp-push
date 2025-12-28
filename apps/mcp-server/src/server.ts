import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  GetPromptRequestSchema,
  ListToolsRequestSchema,
  ListPromptsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { PythonWorkerBridge } from "./bridge/pythonProc.js";
import { readFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const PROMPT_NAME = "mcp-push-usage";
const PROMPT_PATH = join(__dirname, "../../../prompt.json");

const loadPromptText = (): string => {
  try {
    return readFileSync(PROMPT_PATH, "utf-8").trim();
  } catch (error) {
    console.error("Failed to load prompt file:", error);
    return "Use mcp-push only for task completion (>60s) or when user confirmation is needed.";
  }
};

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
  private promptText: string;

  constructor() {
    this.server = new Server(
      {
        name: "mcp-push",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
          prompts: {},
        },
      }
    );

    this.bridge = new PythonWorkerBridge();
    this.promptText = loadPromptText();
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
    this.server.setRequestHandler(ListPromptsRequestSchema, async () => ({
      prompts: [
        {
          name: PROMPT_NAME,
          title: "mcp-push usage guidelines",
          description: "When to notify via mcp-push",
        },
      ],
    }));

    this.server.setRequestHandler(GetPromptRequestSchema, async (request) => {
      if (request.params.name !== PROMPT_NAME) {
        throw new Error(`Unknown prompt: ${request.params.name}`);
      }
      return {
        description: "Guidelines for when to send notifications via mcp-push.",
        messages: [
          {
            role: "user",
            content: [{ type: "text", text: this.promptText }],
          },
        ],
      };
    });

    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "notify_send",
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
          name: "notify_event",
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
      const normalizedName =
        name === "notify.send" ? "notify_send" : name === "notify.event" ? "notify_event" : name;

      try {
        let result: unknown;

        if (normalizedName === "notify_send") {
          const params = NotifySendSchema.parse(args);
          result = await this.bridge.callTool("notify.send", params);
        } else if (normalizedName === "notify_event") {
          const params = NotifyEventSchema.parse(args);
          result = await this.bridge.callTool("notify.event", params);
        } else {
          throw new Error(`Unknown tool: ${name}`);
        }

        const status = (result as { status?: string } | null)?.status;
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
          isError: status === "error",
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
