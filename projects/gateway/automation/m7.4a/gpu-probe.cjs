const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { chromium } = require('D:/Code/porto-projects/app-gateway-fe/node_modules/@playwright/test');
(async () => {
  const report = { timestamp: new Date().toISOString(), os: { platform: os.platform(), release: os.release(), arch: os.arch() }, probes: [] };
  for (const launch of [{ channel: 'chrome', headless: false }, { channel: 'msedge', headless: false }, { headless: true }]) {
    const record = { launch, forcedGpuArguments: [], status: 'pending' };
    let browser;
    try {
      browser = await chromium.launch(launch);
      record.browserVersion = browser.version();
      const cdp = await browser.newBrowserCDPSession();
      const info = await cdp.send('SystemInfo.getInfo');
      record.gpu = info.gpu;
      record.commandLine = info.commandLine;
      const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
      await page.goto('about:blank');
      record.webgl = await page.evaluate(() => {
        const gl = document.createElement('canvas').getContext('webgl2');
        if (!gl) return { available: false, userAgent: navigator.userAgent };
        const debug = gl.getExtension('WEBGL_debug_renderer_info');
        return { available: true, userAgent: navigator.userAgent, vendor: gl.getParameter(gl.VENDOR), renderer: gl.getParameter(gl.RENDERER), unmaskedVendor: debug ? gl.getParameter(debug.UNMASKED_VENDOR_WEBGL) : null, unmaskedRenderer: debug ? gl.getParameter(debug.UNMASKED_RENDERER_WEBGL) : null, version: gl.getParameter(gl.VERSION), contextAttributes: gl.getContextAttributes() };
      });
      await page.goto(launch.channel === 'msedge' ? 'edge://gpu' : 'chrome://gpu');
      await page.waitForFunction(() => document.body.innerText.includes('Graphics Feature Status'), { timeout: 10000 }).catch(() => {});
      record.gpuPage = await page.locator('body').innerText();
      record.softwareRenderer = /swiftshader|llvmpipe|softpipe|software rasterizer|microsoft basic render/i.test(record.webgl.unmaskedRenderer || '');
      record.status = 'complete';
    } catch (error) { record.status = 'failed'; record.error = error.message; }
    finally { if (browser) await browser.close(); }
    report.probes.push(record);
    fs.writeFileSync(path.join(__dirname, 'gpu-capability.json'), JSON.stringify(report, null, 2));
    console.log(JSON.stringify({ launch, status: record.status, browserVersion: record.browserVersion, webgl: record.webgl, softwareRenderer: record.softwareRenderer, devices: record.gpu?.devices, features: record.gpu?.featureStatus, error: record.error }));
  }
})();
