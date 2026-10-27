import base from "../../../app-gateway-fe/playwright.config";
// Reuse the explicitly started local server; avoid npm's unrelated config sync hook.
export default {
  ...base,
  testDir: "../../../app-gateway-fe/tests",
  outputDir: "./test-results",
  webServer: undefined,
  use: { ...base.use, viewport: { width: 1440, height: 900 } },
};
