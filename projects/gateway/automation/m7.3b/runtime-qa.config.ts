import base from "../../../app-gateway-fe/playwright.config";
export default {
  ...base,
  testDir: "../../../app-gateway-fe/tests",
  outputDir: "./test-results",
  webServer: undefined,
  reporter: [["list"], ["json", { outputFile: "../gateway-assets/automation/m7.3b/test-report.json" }]],
  use: { ...base.use, viewport: { width: 1440, height: 900 } },
};
