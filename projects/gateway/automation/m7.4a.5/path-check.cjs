const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
const app='D:/Code/porto-projects/app-gateway-fe',req=Module.createRequire(app+'/package.json'),ts=req('typescript');
require.extensions['.ts']=(m,f)=>m._compile(ts.transpileModule(fs.readFileSync(f,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2020}}).outputText,f);
const {ThirdPersonCamera,cameraBoomFraction}=require(app+'/lib/third-person.ts'),{PerspectiveCamera,Vector3}=req('three');
const r=JSON.parse(fs.readFileSync('D:/Code/porto-projects/gateway-assets/automation/m7.4a.4/targeted-report.json'));
const run=r.runs.find(r=>r.name==='latest-blocked-and-exit'),frame=run.matchedWorst.frame,nav=run.navigation;
const beam=nav.obstacles.find(b=>b.min.y>.59&&b.min.y<.61&&b.min.z>.73&&b.min.z<.75);
const previous=frame.trace.previous,pivot=frame.trace.pivot,step=2*frame.delta;
const expanded={min:{x:beam.min.x-.035,y:beam.min.y-.035,z:beam.min.z-.035},max:{x:beam.max.x+.035,y:beam.max.y+.035,z:beam.max.z+.035}};
// A cube containing the complete allowed movement ball gives conservative plane-hit bounds.
const plane=expanded.min.y,hit=[];
for(const dx of [-step,step])for(const dy of [-step,step])for(const dz of [-step,step]){
 const eye={x:previous.x+dx,y:previous.y+dy,z:previous.z+dz},t=(plane-pivot.y)/(eye.y-pivot.y);
 hit.push({x:pivot.x+t*(eye.x-pivot.x),z:pivot.z+t*(eye.z-pivot.z)});
}
const planeBounds={minX:Math.min(...hit.map(p=>p.x)),maxX:Math.max(...hit.map(p=>p.x)),minZ:Math.min(...hit.map(p=>p.z)),maxZ:Math.max(...hit.map(p=>p.z))};
const allHitInside=planeBounds.minX>expanded.min.x&&planeBounds.maxX<expanded.max.x&&planeBounds.minZ>expanded.min.z&&planeBounds.maxZ<expanded.max.z;
let nearCandidates=0,nearClear=0;
for(let x=-5;x<=5;x++)for(let y=-5;y<=5;y++)for(let z=-5;z<=5;z++){if(x*x+y*y+z*z>25)continue;nearCandidates++;const p={x:previous.x+x/5*step,y:previous.y+y/5*step,z:previous.z+z/5*step};if(cameraBoomFraction(pivot,p,nav.obstacles)===1)nearClear++;}
const startPlayer={position:{...nav.spawn},yaw:frame.player.yaw,pitch:frame.player.pitch},endPlayer={position:{x:.05487,y:.18,z:.7824},yaw:frame.player.yaw,pitch:frame.player.pitch};
const initial=new ThirdPersonCamera(),final=new ThirdPersonCamera();initial.update(startPlayer,nav,0,true,true,1.6);final.update(endPlayer,nav,0,true,true,1.6);
const lerp=(a,b,t)=>({x:a.x+(b.x-a.x)*t,y:a.y+(b.y-a.y)*t,z:a.z+(b.z-a.z)*t});
const envelope=[[-.075,-.075,0],[.075,-.075,0],[-.075,.075,0],[.075,.075,0],[-.075,-.075,.32],[.075,-.075,.32],[-.075,.075,.32],[.075,.075,.32]];
const paths=[];
for(const offset of [null,-.5,-.25,0,.25,.5]){
 const midpoint=offset===null?lerp(initial.position,final.position,.5):{x:startPlayer.position.x+Math.sin(startPlayer.yaw+offset)*Math.cos(-.52)*.68,y:initial.position.y,z:startPlayer.position.z+Math.cos(startPlayer.yaw+offset)*Math.cos(-.52)*.68};
 const stats={strategy:offset===null?'direct-early-transition':'existing-yaw-waypoint-'+offset,boomFailures:0,sweepFailures:0,framingFailures:0,maxStep:0,maxStepRatio:0,frames:0};
 for(const fps of [30,60,120]){let previous={...initial.position};for(let i=1;i<=Math.ceil(fps*.95);i++){
  const t=Math.min(1,i/(fps*.95)),player=lerp(startPlayer.position,endPlayer.position,t),ease=t*t*(3-2*t);
  const target={...player,y:initial.target.y+(final.target.y-initial.target.y)*ease},position=t<.5?lerp(initial.position,midpoint,2*t):lerp(midpoint,final.position,2*t-1);
  stats.frames++;const distance=Math.hypot(position.x-previous.x,position.y-previous.y,position.z-previous.z);stats.maxStep=Math.max(stats.maxStep,distance);stats.maxStepRatio=Math.max(stats.maxStepRatio,distance/(2/fps));
  if(cameraBoomFraction(target,position,nav.obstacles)<1)stats.boomFailures++;
  if(cameraBoomFraction(previous,position,nav.obstacles)<1)stats.sweepFailures++;
  const camera=new PerspectiveCamera(75,1.6,.01,100);camera.position.set(position.x,position.y,position.z);camera.lookAt(target.x,target.y,target.z);camera.updateMatrixWorld();let fail=false;
  for(const [side,depth,height]of envelope){const sin=Math.sin(startPlayer.yaw),cos=Math.cos(startPlayer.yaw),p=new Vector3(player.x+cos*side+sin*depth,player.y+height,player.z-sin*side+cos*depth).project(camera);if(Math.abs(p.x)>1||Math.abs(p.y)>1||p.z < -1||p.z>1)fail=true;}if(fail)stats.framingFailures++;
  previous=position;
 }}paths.push(stats);
}
const report={lateRepair:{previous,pivot,step,expandedBeam:expanded,planeBounds,allMovementBallRaysIntersectBeam:allHitInside,nearCandidates,nearClear,minimumVerticalDistanceToUnderside:previous.y-expanded.min.y},paths};
fs.writeFileSync(path.join(__dirname,'path-results.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
if(!allHitInside||nearClear!==0)throw Error('Late-repair proof failed');
