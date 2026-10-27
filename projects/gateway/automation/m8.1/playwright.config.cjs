const { defineConfig } = require('D:/Code/porto-projects/app-gateway-fe/node_modules/@playwright/test');
module.exports = defineConfig({
  testDir: 'D:/Code/porto-projects/app-gateway-fe/tests',
  outputDir: 'D:/Code/porto-projects/gateway-assets/automation/m8.1/test-results',
  fullyParallel: false, workers: 1, timeout: 120000, expect: { timeout: 20000 },
  reporter: [['list']],
  use: { baseURL: 'http://127.0.0.1:3108', channel: 'chrome', headless: false,
    viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce', trace: 'retain-on-failure' }
});
