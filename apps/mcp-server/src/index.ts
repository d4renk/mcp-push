#!/usr/bin/env node
import { McpPushServer } from "./server.js";

async function main() {
  const server = new McpPushServer();
  await server.start();
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
