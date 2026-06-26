import { chromium } from "playwright";

const browser = await chromium.launch({ args: ["--no-sandbox"] });
const page = await (await browser.newContext()).newPage();
const errors = [];
page.on("console", (msg) => {
  if (msg.type() === "error") errors.push(msg.text());
});
page.on("pageerror", (err) => errors.push(String(err)));

await page.goto("http://localhost:5173/", { waitUntil: "networkidle" });
await page.waitForSelector("header h1");
await page.screenshot({ path: "/tmp/run_1_initial.png" });

// Switch to Gwalior (just refreshed today) and confirm the city selector + map both work
await page.selectOption("select", "gwalior");
await page.waitForTimeout(1000);
await page.click("text=Map");
await page.waitForSelector(".leaflet-container", { timeout: 15000 });
await page.waitForTimeout(1500);
const markerCount = await page.locator("path.leaflet-interactive").count();
console.log("GWALIOR_MARKER_PATHS:", markerCount);
await page.screenshot({ path: "/tmp/run_2_gwalior_map.png" });

// Back to chat, ask something to confirm the live pipeline still answers
await page.click("text=Chat");
await page.waitForSelector('input[placeholder*="Ask about"]');
await page.fill('input[placeholder*="Ask about"]', "any good restaurants here?");
await page.press('input[placeholder*="Ask about"]', "Enter");
await page.waitForSelector(".message.assistant:not(.pending)", { timeout: 120000 });
await page.screenshot({ path: "/tmp/run_3_gwalior_chat.png" });

console.log("CONSOLE_ERRORS:", JSON.stringify(errors));
await browser.close();
