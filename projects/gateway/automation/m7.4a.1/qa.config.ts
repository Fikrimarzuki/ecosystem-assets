import { defineConfig } from "../../../app-gateway-fe/node_modules/@playwright/test";

export default defineConfig({
  testDir: "../../../app-gateway-fe/tests",
  testMatch: "universe-exploration-layout.spec.ts",
  workers: 1,
  timeout: 90_000,
  expect: { timeout: 15_000 },
  outputDir: "./test-results",
  reporter: [["list"], ["json", { outputFile: "D:/Code/porto-projects/gateway-assets/automation/m7.4a.1/focused-tests.json" }]],
  use: {
    baseURL: "http://127.0.0.1:3001",
    reducedMotion: "reduce",
    channel: "chrome",
    headless: false,
    trace: "retain-on-failure",
  },
});
