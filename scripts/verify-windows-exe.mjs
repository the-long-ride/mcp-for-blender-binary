// Node.js 24 MCP-over-stdio smoke test for a real frozen Windows executable.
import { spawn } from "node:child_process";
import { resolve } from "node:path";

const exe = resolve(process.argv[2] ?? "dist/mcp-for-blender.exe");
const child = spawn(exe, [], { stdio: ["pipe", "pipe", "pipe"], windowsHide: true });
let buffer = "";
let errors = "";
let done = false;
const timeout = setTimeout(() => fail("MCP handshake timeout"), 60000);
function send(value) { child.stdin.write(JSON.stringify(value) + "\n"); }
function finish() {
  if (done) return;
  done = true;
  clearTimeout(timeout);
  console.log("PASS: Windows EXE initialized and listed Blender MCP tools");
  child.kill();
}
function fail(msg) {
  if (done) return;
  done = true;
  clearTimeout(timeout);
  console.error("FAIL:", msg, errors.slice(-3000));
  process.exitCode = 1;
  child.kill();
}
child.on("error", e => fail(e.message));
child.on("exit", code => { if (!done) fail("Server exited before handshake: " + code); });
child.stderr.setEncoding("utf8");
child.stderr.on("data", data => { errors = (errors + data).slice(-10000); });
child.stdout.setEncoding("utf8");
child.stdout.on("data", data => {
  buffer += data;
  while (buffer.includes("\n")) {
    const end = buffer.indexOf("\n");
    const line = buffer.slice(0, end).trim();
    buffer = buffer.slice(end + 1);
    if (!line) continue;
    let m;
    try { m = JSON.parse(line); }
    catch { fail("Non-JSON on stdio: " + line.slice(0, 300)); return; }
    if (m.id === 1) {
      if (m.error || !m.result?.capabilities) {
        fail("initialize did not return MCP capabilities: " + line.slice(0, 300)); return;
      }
      send({ jsonrpc: "2.0", method: "notifications/initialized" });
      send({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });
    }
    if (m.id === 2) {
      if (m.error || !Array.isArray(m.result?.tools) || m.result.tools.length < 1) {
        fail("MCP tools/list failed: " + line.slice(0, 300)); return;
      }
      console.log("Found", m.result.tools.length, "tools");
      finish();
    }
  }
});
send({ jsonrpc: "2.0", id: 1, method: "initialize", params: {
  protocolVersion: "2025-06-18",
  capabilities: {},
  clientInfo: { name: "mcp-for-blender-binary-ci", version: "1.0.0" }
} });
