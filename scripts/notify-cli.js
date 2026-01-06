#!/usr/bin/env node

/**
 * CLI tool to send notifications directly via sendNotify.js
 * Usage: node notify-cli.js --title "Title" --content "Content"
 */

const { sendNotify } = require('./sendNotify.js');

function parseArgs() {
  const args = process.argv.slice(2);
  const params = {};

  for (let i = 0; i < args.length; i++) {
    if (args[i].startsWith('--')) {
      const key = args[i].substring(2);
      const value = args[i + 1];
      if (value && !value.startsWith('--')) {
        params[key] = value;
        i++;
      }
    }
  }

  return params;
}

async function main() {
  const params = parseArgs();

  if (!params.title || !params.content) {
    console.error('Error: Both --title and --content are required');
    console.error('Usage: notify-cli.js --title "Title" --content "Content"');
    process.exit(1);
  }

  try {
    await sendNotify(params.title, params.content);
    console.log('Notification sent successfully');
  } catch (error) {
    console.error('Failed to send notification:', error);
    process.exit(1);
  }
}

main();
