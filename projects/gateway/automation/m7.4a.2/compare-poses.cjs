const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const app=path.resolve('D:/Code/porto-projects/app-gateway-fe'),req=Module.createRequire(path.join(app,'package.json')),ts=req('typescript');
const resolve=Module._resolveFilename;Module._resolveFilename=function(id,p,...r){return resolve.call(this,id.startsWith('@/')?path.join(app,id.slice(2)):id,p,...r);};
const compile=s=>ts.transpileModule(s,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true}}).outputText;
for(const ext of ['.ts','.tsx'])require.extensions[ext]=(m,f)=>m._compile(compile(fs.readFileSync(f,'utf8')),f);
const m=new Module(path.join(app,'lib/third-person-baseline.ts'));m.filename=m.id;m.paths=Module._nodeModulePaths(path.join(app,'lib'));m._compile(compile(fs.readFileSync(path.join(__dirname,'baseline-third-person.ts'),'utf8')),m.id);
const baseline=m.exports,current=require(path.join(app,'lib/third-person.ts'));
const captures=JSON.parse(fs.readFileSync(path.join(__dirname,'after-report.json'))).captures;
if(fs.existsSync(path.join(__dirname,'clearance-report.json')))captures.push(...JSON.parse(fs.readFileSync(path.join(__dirname,'clearance-report.json'))).captures);
const report=[];
for(const c of captures){
 const s=c.snapshot,player={position:{x:s.player.x,y:s.player.y,z:s.player.z},yaw:s.player.yaw,pitch:s.player.pitch},before=new baseline.ThirdPersonCamera(),after=new current.ThirdPersonCamera();let maxPositionError=0,maxTargetError=0;
 for(let i=0;i<120;i++){
  before.update(player,s.navigation,1/60,false,true);after.update(player,s.navigation,1/60,false,true,1.6);
  maxPositionError=Math.max(maxPositionError,Math.hypot(...['x','y','z'].map(a=>before.position[a]-after.position[a])));
  maxTargetError=Math.max(maxTargetError,Math.hypot(...['x','y','z'].map(a=>before.target[a]-after.target[a])));
 }
 const probes=[0,.08,.16,.32].map(height=>{const p={...player.position,y:player.position.y+height};return{height,unobstructed:current.cameraBoomFraction(after.position,p,s.navigation.obstacles,0)===1};});
 report.push({name:c.name,maxPositionError,maxTargetError,beforeFov:before.fov,afterFov:after.fov,clearBoom:current.cameraBoomFraction(after.target,after.position,s.navigation.obstacles)===1,probes});
 if(maxPositionError!==0||maxTargetError!==0||!report.at(-1).clearBoom)throw Error('Position/aim/collision compatibility failed');
}
fs.writeFileSync(path.join(__dirname,'pose-comparison-report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
