const {defineConfig}=require('D:/Code/porto-projects/app-gateway-fe/node_modules/@playwright/test');
process.env.NEXT_PUBLIC_GATEWAY_WALKING_EXPLORATION='true';
module.exports=defineConfig({testDir:'D:/Code/porto-projects/app-gateway-fe/tests',workers:1,timeout:120000,expect:{timeout:20000},outputDir:__dirname+'/test-results',reporter:[['list'],['json',{outputFile:__dirname+'/test-report.json'}]],use:{baseURL:'http://127.0.0.1:3001',viewport:{width:1440,height:900},reducedMotion:'reduce',channel:'chrome',headless:false}});
