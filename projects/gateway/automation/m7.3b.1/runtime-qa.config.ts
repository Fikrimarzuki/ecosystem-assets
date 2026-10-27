import base from "../../../app-gateway-fe/playwright.config";
export default {
  ...base,
  testDir: "../../../app-gateway-fe/tests",
  outputDir: "./test-results",
  webServer: undefined,
  reporter: [["list"], ["json", { outputFile: "./test-report.json" }]],
  use: { ...base.use, viewport: { width: 1440, height: 900 }, video: { mode: "on", size: { width: 1440, height: 900 } } },
};
