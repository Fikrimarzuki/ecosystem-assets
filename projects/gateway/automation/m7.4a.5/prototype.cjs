const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const app='D:/Code/porto-projects/app-gateway-fe',req=Module.createRequire(app+'/package.json'),ts=req('typescript');
const compile=s=>ts.transpileModule(s,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText;
require.extensions['.ts']=(m,f)=>m._compile(compile(fs.readFileSync(f,'utf8')),f);
const original=require(app+'/lib/third-person.ts'),{PerspectiveCamera,Vector3}=req('three');
const source=fs.readFileSync(app+'/lib/third-person.ts','utf8');
const prepare=`
    let passageCeiling = Infinity;
    if (checkVisibility) for (const box of walkableCeilings(nav)) {
      if (box.min.y < player.position.y + PLAYER.height - .0001 || box.min.y - THIRD_PERSON.radius - .002 >= pivot.y) continue;
      const dx = Math.max(box.min.x - THIRD_PERSON.radius - pivot.x, 0, pivot.x - box.max.x - THIRD_PERSON.radius);
      const dz = Math.max(box.min.z - THIRD_PERSON.radius - pivot.z, 0, pivot.z - box.max.z - THIRD_PERSON.radius);
      const proximity = Math.min(1, Math.max(0, (Math.hypot(dx, dz) - THIRD_PERSON.distance) / .36));
      if (proximity < 1) {
        const ease = proximity * proximity * (3 - 2 * proximity);
        const targetY = box.min.y - THIRD_PERSON.radius - .002;
        const safeY = box.min.y - THIRD_PERSON.radius - .012;
        passageCeiling = Math.min(passageCeiling, safeY + (player.position.y + thirdPersonTargetHeight(nav) + .50 - safeY) * ease);
        pivot.y = Math.min(pivot.y, targetY + (pivot.y - targetY) * ease);
      }
    }
`;
const candidateSource=source.replace('    // A player may fit beneath',prepare+'    // A player may fit beneath').replace('    let ceiling = Infinity;','    let ceiling = passageCeiling;');
fs.writeFileSync(path.join(__dirname,'prototype-third-person.ts'),candidateSource);
const mod=new Module(app+'/lib/third-person-prototype.ts');mod.filename=mod.id;mod.paths=Module._nodeModulePaths(app+'/lib');mod._compile(compile(candidateSource),mod.id);const candidate=mod.exports;
const reports=['report','targeted-report'].flatMap(n=>JSON.parse(fs.readFileSync('D:/Code/porto-projects/gateway-assets/automation/m7.4a.4/'+n+'.json')).runs);
const envelopes=[[-.075,-.075,0],[.075,-.075,0],[-.075,.075,0],[.075,.075,0],[-.075,-.075,.32],[.075,-.075,.32],[-.075,.075,.32],[.075,.075,.32]];
const results=[];
for(const run of reports){
 const nav=run.navigation,first=run.frames[0].player,camera=new candidate.ThirdPersonCamera(),baseline=new original.ThirdPersonCamera();
 for(let i=0;i<120;i++){const p={position:nav.spawn,yaw:first.yaw,pitch:first.pitch};camera.update(p,nav,1/60,false,true,1.6);baseline.update(p,nav,1/60,false,true,1.6);}
 const result={name:run.name,failures:0,collisionFailures:0,pathFailures:0,maxStep:0,maxRatio:0,minBoom:Infinity,maxCrop:0,baselineMaxStep:0,baselineMinBoom:Infinity,frames:0};
 for(const f of run.frames){
  const p={position:{x:f.player.x,y:f.player.y,z:f.player.z},yaw:f.player.yaw,pitch:f.player.pitch},prev={...camera.position},bp={...baseline.position};const dt=f.delta;
  camera.update(p,nav,dt,false,true,1.6);baseline.update(p,nav,dt,false,true,1.6);result.frames++;
  const len=(a,b)=>Math.hypot(a.x-b.x,a.y-b.y,a.z-b.z),step=len(prev,camera.position);
  result.maxStep=Math.max(result.maxStep,step);result.maxRatio=Math.max(result.maxRatio,step/(2*Math.min(.1,dt)));result.minBoom=Math.min(result.minBoom,len(camera.position,camera.target));result.baselineMaxStep=Math.max(result.baselineMaxStep,len(bp,baseline.position));result.baselineMinBoom=Math.min(result.baselineMinBoom,len(baseline.position,baseline.target));
  if(original.cameraBoomFraction(camera.target,camera.position,nav.obstacles)<1)result.collisionFailures++;
  if(original.cameraBoomFraction(prev,camera.position,nav.obstacles)<1)result.pathFailures++;
  const c=new PerspectiveCamera(camera.fov,1.6,.01,100);c.position.set(camera.position.x,camera.position.y,camera.position.z);c.lookAt(camera.target.x,camera.target.y,camera.target.z);c.updateMatrixWorld();
  let max=0;for(const [x,z,y]of envelopes){const sin=Math.sin(p.yaw),cos=Math.cos(p.yaw),point=new Vector3(p.position.x+cos*x+sin*z,p.position.y+y,p.position.z-sin*x+cos*z).project(c);max=Math.max(max,Math.abs(point.x),Math.abs(point.y));}result.maxCrop=Math.max(result.maxCrop,(max-1)*450);if(max>1.0001)result.failures++;
 }
 results.push(result);
}
fs.writeFileSync(path.join(__dirname,'prototype-results.json'),JSON.stringify(results,null,2));console.log(JSON.stringify(results,null,2));
