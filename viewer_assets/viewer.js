
const I=()=>[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1];
const mul=(a,b)=>Array.from({length:16},(_,i)=>{let v=0;for(let k=0;k<4;k++)v+=a[(i>>2)*4+k]*b[k*4+i%4];return v});
const point=(m,p,w=1)=>[0,1,2].map(i=>m[i*4]*p[0]+m[i*4+1]*p[1]+m[i*4+2]*p[2]+m[i*4+3]*w);
const sub=(a,b)=>a.map((x,i)=>x-b[i]);
const norm=a=>{const l=Math.hypot(...a)||1;return a.map(x=>x/l)};
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
const glMatrix=m=>new Float32Array(Array.from({length:16},(_,i)=>m[(i%4)*4+(i>>2)]));
function srt(s){let [sx,sy,sz,x,y,z,w,tx,ty,tz]=s;return [(1-2*y*y-2*z*z)*sx,(2*x*y-2*z*w)*sy,(2*x*z+2*y*w)*sz,tx,(2*x*y+2*z*w)*sx,(1-2*x*x-2*z*z)*sy,(2*y*z-2*x*w)*sz,ty,(2*x*z-2*y*w)*sx,(2*y*z+2*x*w)*sy,(1-2*x*x-2*y*y)*sz,tz,0,0,0,1]}
function sample(keys,t){let lo=0,hi=keys.length-1;while(lo+1<hi){const m=(lo+hi)>>1;if(keys[m][0]<=t)lo=m;else hi=m}const a=keys[lo],b=keys[hi],v=Math.max(0,Math.min(1,(t-a[0])/(b[0]-a[0]||1)));let s=a.slice(1,11).map((x,i)=>x+(b[i+1]-x)*v);const qa=a.slice(4,8),qb=b.slice(4,8),sign=dot(qa,qb)<0?-1:1;const q=norm(qa.map((x,i)=>x+(sign*qb[i]-x)*v));s.splice(3,4,...q);return s}

export class Viewer{
 constructor(canvas,onFrame){
  this.canvas=canvas;this.onFrame=onFrame;this.time=0;this.playing=false;this.speed=1;this.clip=-1;this.grid=true;this.bones=false;this.wire=false;this.texture=true;this.yaw=0;this.pitch=.07;this.distance=16;this.center=[0,3,0];this.radius=5;this.upAxis='Y';this.entries=[];this.scene=null;this.drag=null;this.highlightBone=null;this.highlightMesh=null;
  const g=this.gl=canvas.getContext('webgl',{antialias:true,alpha:false,preserveDrawingBuffer:true});if(!g)throw Error('WebGL est indisponible dans ce navigateur.');
  const shader=(type,source)=>{const s=g.createShader(type);g.shaderSource(s,source);g.compileShader(s);if(!g.getShaderParameter(s,g.COMPILE_STATUS))throw Error(g.getShaderInfoLog(s));return s};
  const vs=shader(g.VERTEX_SHADER,`attribute vec3 p;attribute vec3 n;attribute vec2 uv;uniform mat4 vp;varying vec3 normal;varying vec2 tex;void main(){gl_Position=vp*vec4(p,1.);normal=n;tex=uv;}`);
  const fs=shader(g.FRAGMENT_SHADER,`precision mediump float;varying vec3 normal;varying vec2 tex;uniform sampler2D img;uniform float textured;uniform float line;uniform vec4 color;void main(){if(line>.5){gl_FragColor=color;return;}vec4 c=mix(color,texture2D(img,tex),textured);if(c.a<.25)discard;float light=.76+.24*abs(dot(normalize(normal),normalize(vec3(.2,.8,1.))));gl_FragColor=vec4(c.rgb*light,c.a);}`);
  this.program=g.createProgram();g.attachShader(this.program,vs);g.attachShader(this.program,fs);g.linkProgram(this.program);if(!g.getProgramParameter(this.program,g.LINK_STATUS))throw Error(g.getProgramInfoLog(this.program));g.useProgram(this.program);
  this.attr=Object.fromEntries(['p','n','uv'].map(n=>[n,g.getAttribLocation(this.program,n)]));this.uni=Object.fromEntries(['vp','img','textured','line','color'].map(n=>[n,g.getUniformLocation(this.program,n)]));this.linebuf=g.createBuffer();this.white=this.makeTexture();this.textures=new Map();
  g.enable(g.DEPTH_TEST);g.enable(g.BLEND);g.blendFunc(g.SRC_ALPHA,g.ONE_MINUS_SRC_ALPHA);
  canvas.addEventListener('pointerdown',e=>{this.drag=[e.clientX,e.clientY,e.button,e.shiftKey];canvas.setPointerCapture(e.pointerId)});
  canvas.addEventListener('pointerup',()=>this.drag=null);canvas.addEventListener('pointercancel',()=>this.drag=null);canvas.addEventListener('contextmenu',e=>e.preventDefault());
  canvas.addEventListener('pointermove',e=>{if(!this.drag)return;const dx=e.clientX-this.drag[0],dy=e.clientY-this.drag[1];if(this.drag[2]===2||this.drag[3]){this.center[0]-=dx*this.distance/700;this.center[this.upAxis==='Z'?2:1]+=dy*this.distance/700}else{this.yaw-=dx*.008;this.pitch=Math.max(-1.5,Math.min(1.5,this.pitch+dy*.006))}this.drag[0]=e.clientX;this.drag[1]=e.clientY});
  canvas.addEventListener('wheel',e=>{e.preventDefault();this.distance=Math.max(this.radius*.15,Math.min(this.radius*50,this.distance*Math.exp(e.deltaY*.001)))},{passive:false});
  let last=performance.now();const tick=now=>{const dt=Math.min((now-last)/1000,.08);last=now;if(this.playing&&this.scene&&this.clip>=0){const d=this.scene.clips[this.clip].duration;this.time=d?(this.time+dt*this.speed)%d:0;}this.render();this.onFrame?.(this.time);this.raf=requestAnimationFrame(tick)};this.raf=requestAnimationFrame(tick);
 }
 makeTexture(){const g=this.gl,t=g.createTexture();g.bindTexture(g.TEXTURE_2D,t);g.texImage2D(g.TEXTURE_2D,0,g.RGBA,1,1,0,g.RGBA,g.UNSIGNED_BYTE,new Uint8Array([199,209,233,255]));g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MIN_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_MAG_FILTER,g.LINEAR);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_S,g.CLAMP_TO_EDGE);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_T,g.CLAMP_TO_EDGE);return t}
 async load(scene,textureBase,axis='Y'){
  const g=this.gl;for(const e of this.entries){g.deleteBuffer(e.buffer);g.deleteBuffer(e.edgeBuffer)}for(const t of this.textures.values())g.deleteTexture(t);this.textures.clear();this.entries=[];this.scene=scene;this.upAxis=axis;this.clip=-1;this.time=0;this.playing=false;
  for(const mesh of scene.meshes){const sourceMesh=scene.nodes.find(n=>n.meshes?.includes(mesh.name))?.name?.replace(/^mesh_/,'')||mesh.name;for(const p of mesh.primitives){const packed=new Float32Array(p.vertices.length*8);p.vertices.forEach((v,i)=>packed.set(v.length===8?v:[...v.slice(0,3),0,1,0,...v.slice(3)],i*8));this.entries.push({mesh:mesh.name,sourceMesh,primitive:p,skin:scene.skins.find(s=>s.name===mesh.name),buffer:g.createBuffer(),edgeBuffer:g.createBuffer(),packed,edges:new Float32Array(p.vertices.length*2*8)});}}
  this.fit();
  const pot=n=>n>0&&(n&(n-1))===0;const failed=[];await Promise.all(scene.materials.filter(m=>m.texture).map(m=>new Promise(resolve=>{const tex=this.makeTexture();this.textures.set(m.name,tex);const img=new Image();img.onload=()=>{g.bindTexture(g.TEXTURE_2D,tex);g.pixelStorei(g.UNPACK_FLIP_Y_WEBGL,false);g.texImage2D(g.TEXTURE_2D,0,g.RGBA,g.RGBA,g.UNSIGNED_BYTE,img);if(pot(img.width)&&pot(img.height)){g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_S,g.REPEAT);g.texParameteri(g.TEXTURE_2D,g.TEXTURE_WRAP_T,g.REPEAT)}resolve()};img.onerror=()=>{failed.push(m.texture);resolve()};img.src=textureBase+encodeURIComponent(m.texture+'.png')})));return failed;
 }
 fit(){
  if(!this.scene)return;const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity],saved=this.time,clip=this.scene.clips[this.clip];
  
  for(let frame=0;frame<(clip?17:1);frame++){
   this.time=clip?clip.duration*frame/16:0;const world=this.worlds();
   for(const e of this.entries){const skin=e.skin,matrices=skin?.bones.map(b=>mul(world[b.name],b.inverse));for(let i=0;i<e.primitive.vertices.length;i++){const v=e.primitive.vertices[i];let p=v;if(skin){p=[0,0,0];for(const [bi,w]of skin.weights[e.primitive.indices[i]]){if(w){const q=point(matrices[bi],v);for(let k=0;k<3;k++)p[k]+=w*q[k]}}}for(let k=0;k<3;k++){min[k]=Math.min(min[k],p[k]);max[k]=Math.max(max[k],p[k])}}}
  }
  this.time=saved;this.center=min.map((v,i)=>(v+max[i])/2);this.radius=Math.max(.001,Math.hypot(...sub(max,min))/2);const aspect=this.canvas.clientWidth/Math.max(1,this.canvas.clientHeight);this.distance=this.radius*3.2/Math.min(1,aspect);this.ground=min[this.upAxis==='Z'?2:1];this.yaw=0;this.pitch=.05;
 }
 view(direction){this.yaw=direction==='side'?Math.PI/2:0;this.pitch=direction==='top'?1.5:.05;}
 worlds(){const nodes=this.scene.nodes,locals={};for(const n of nodes)locals[n.name]=n.srt;const clip=this.scene.clips[this.clip];if(clip)for(const t of clip.tracks)locals[t.node]=sample(t.keys,this.time);const byName=Object.fromEntries(nodes.map(n=>[n.name,n])),world={};const calc=name=>world[name]||(world[name]=byName[name].parent?mul(calc(byName[name].parent),srt(locals[name])):srt(locals[name]));for(const n of nodes)calc(n.name);return world;}
 bind(buffer,packed){const g=this.gl;g.bindBuffer(g.ARRAY_BUFFER,buffer);g.bufferData(g.ARRAY_BUFFER,packed,g.DYNAMIC_DRAW);for(const [key,size,offset]of [['p',3,0],['n',3,12],['uv',2,24]]){g.enableVertexAttribArray(this.attr[key]);g.vertexAttribPointer(this.attr[key],size,g.FLOAT,false,32,offset)}}
 lines(points,color){if(!points.length)return;const g=this.gl,packed=new Float32Array(points.length*8);points.forEach((p,i)=>packed.set([...p,0,1,0,0,0],i*8));this.bind(this.linebuf,packed);g.uniform1f(this.uni.line,1);g.uniform4fv(this.uni.color,color);g.drawArrays(g.LINES,0,points.length);}
 render(){
  const g=this.gl,c=this.canvas,dpr=Math.min(devicePixelRatio||1,2),w=Math.max(1,Math.round(c.clientWidth*dpr)),h=Math.max(1,Math.round(c.clientHeight*dpr));if(c.width!==w||c.height!==h){c.width=w;c.height=h}g.viewport(0,0,w,h);g.clearColor(.047,.065,.105,1);g.clear(g.COLOR_BUFFER_BIT|g.DEPTH_BUFFER_BIT);if(!this.scene)return;g.useProgram(this.program);
  let offset=[Math.sin(this.yaw)*Math.cos(this.pitch),Math.sin(this.pitch),Math.cos(this.yaw)*Math.cos(this.pitch)].map(v=>v*this.distance);if(this.upAxis==='Z')offset=[offset[0],-offset[2],offset[1]];const eye=this.center.map((v,i)=>v+offset[i]),up=this.upAxis==='Z'?[0,0,1]:[0,1,0],z=norm(sub(eye,this.center)),x=norm(cross(up,z)),y=cross(z,x),view=[...x,-dot(x,eye),...y,-dot(y,eye),...z,-dot(z,eye),0,0,0,1];const f=1/Math.tan(Math.PI/8),near=this.radius*.005,far=this.radius*120,proj=[f/(w/h),0,0,0,0,f,0,0,0,0,(far+near)/(near-far),2*far*near/(near-far),0,0,-1,0];g.uniformMatrix4fv(this.uni.vp,false,glMatrix(mul(proj,view)));
  if(this.grid){let ps=[],a=this.radius*1.8;for(let i=-10;i<=10;i++){const t=i*a/10;ps.push([-a,this.ground,t],[a,this.ground,t],[t,this.ground,-a],[t,this.ground,a])}if(this.upAxis==='Z')ps=ps.map(p=>[p[0],p[2],p[1]]);this.lines(ps,[.2,.29,.39,.38])}
  const world=this.worlds();
  for(const e of this.entries){const p=e.primitive,skin=e.skin,matrices=skin?.bones.map(b=>mul(world[b.name],b.inverse));for(let i=0;i<p.vertices.length;i++){const v=p.vertices[i],n=v.length===8?v.slice(3,6):[0,1,0];let pos=v.slice(0,3),normal=n;if(skin){pos=[0,0,0];normal=[0,0,0];for(const [bi,weight]of skin.weights[p.indices[i]]){if(!weight)continue;const tp=point(matrices[bi],v),tn=point(matrices[bi],n,0);for(let k=0;k<3;k++){pos[k]+=tp[k]*weight;normal[k]+=tn[k]*weight}}}e.packed.set(pos,i*8);e.packed.set(norm(normal),i*8+3)}
   this.bind(e.buffer,e.packed);g.uniform1f(this.uni.line,0);g.uniform4fv(this.uni.color,[.62,.71,.87,1]);g.uniform1f(this.uni.textured,this.texture&&this.textures.has(p.material)?1:0);g.activeTexture(g.TEXTURE0);g.bindTexture(g.TEXTURE_2D,this.textures.get(p.material)||this.white);g.uniform1i(this.uni.img,0);g.enable(g.POLYGON_OFFSET_FILL);g.polygonOffset(1,1);g.drawArrays(g.TRIANGLES,0,p.vertices.length);g.disable(g.POLYGON_OFFSET_FILL);
   if(this.wire||this.highlightMesh===e.sourceMesh){for(let i=0;i<p.vertices.length;i+=3)for(let j=0;j<6;j++){const vi=i+[0,1,1,2,2,0][j];e.edges.set(e.packed.subarray(vi*8,vi*8+8),(i*2+j)*8)}this.bind(e.edgeBuffer,e.edges);g.uniform1f(this.uni.line,1);g.uniform4fv(this.uni.color,this.highlightMesh===e.sourceMesh?[1,.78,.28,.95]:[.33,.95,.83,.65]);g.drawArrays(g.LINES,0,p.vertices.length*2)}
  }
  if(this.bones||this.highlightBone){const points=[],hi=[];for(const n of this.scene.nodes)if(n.parent&&!n.meshes.length&&n.parent!=='model_root'){const a=point(world[n.name],[0,0,0]),b=point(world[n.parent],[0,0,0]);if(this.bones)points.push(a,b);if(this.highlightBone&&(n.name===this.highlightBone||n.parent===this.highlightBone))hi.push(a,b)}if(this.highlightBone&&world[this.highlightBone]){const p=point(world[this.highlightBone],[0,0,0]),r=this.radius*.06;hi.push([p[0]-r,p[1],p[2]],[p[0]+r,p[1],p[2]],[p[0],p[1]-r,p[2]],[p[0],p[1]+r,p[2]],[p[0],p[1],p[2]-r],[p[0],p[1],p[2]+r])}g.disable(g.DEPTH_TEST);this.lines(points,[1,.72,.24,1]);this.lines(hi,[.35,.98,.78,1]);g.enable(g.DEPTH_TEST)}
 }
 screenshot(){this.render();return this.canvas.toDataURL('image/png')}
}
