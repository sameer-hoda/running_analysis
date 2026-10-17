/* RUNFORM v3 avatar renderer — dependency-free Canvas 2D turntable.
   Skeleton joint ANGLES come from YOLOv8m-pose detection on the analyzed photo
   (IK-retargeted to anatomical segment lengths); only L/R root split + limb
   depths are presentation priors. No CDN, no WebGL — works from file://. */
(function(){
'use strict';

var ZONES = [
  {id:'trunk', title:'Trunk & Forward Lean', score:56, status:'fair', joint:'TRUNK',
   see:'Torso overly upright, minimal lean from the ankles.', tldr:'Vertical torso limits forward drive.',
   eli5:'Lean slightly forward from the ankles like a ski jumper — gravity then pulls you forward instead of you muscling every step.',
   signs:['Vertical spine angle','Absent ankle lean'],
   actions:['Cue slight forward tilt from ankles','Engage core','Wall-lean drill 3×30s, body straight from ankles'],
   evi:'Ankle-derived lean uses gravitational torque to assist progression; hinging at the waist loads the lower back. Judge the source of lean, not just the angle.'},
  {id:'sh', title:'Shoulder Carriage', score:58, status:'fair', joint:'R_SH',
   see:'Shoulders slightly elevated and drawn back.', tldr:'Minor shoulder tightness wasting energy.',
   eli5:'Keep shoulders relaxed away from ears. High shoulders waste effort — like shrugging for your whole run.',
   signs:['Mild elevation','Upper-trapezius contraction'],
   actions:['Exhale and drop shoulders every km','Shoulder rolls mid-run'],
   evi:'Shoulder elevation raises upper-body tension and metabolic cost; relaxed, dropped shoulders with natural oscillation is the efficient pattern.'},
  {id:'head', title:'Head & Neck', score:60, status:'fair', joint:'NECK',
   see:'Head upright, forward gaze, slight neck tension.', tldr:'Neutral gaze with minor neck tightness.',
   eli5:'Look straight ahead, ~20–30m down the road. Relax the neck, unclench the jaw.',
   signs:['Forward gaze ✓','Mild cervical tension'],
   actions:['Relax jaw, lips slightly parted','Gaze on horizon, not feet'],
   evi:'Cervical orientation drives vestibular stabilization and downstream trunk alignment; neutral neck supports the whole posture chain.'},
  {id:'knee', title:'Knee Mechanics', score:60, status:'fair', joint:'R_KNEE',
   see:'Stance knee flexes moderately under the body.', tldr:'Knee compliance absorbs impact adequately.',
   eli5:'Bend knees softly on landing like springs. A soft knee catches you; a locked knee crashes you.',
   signs:['Load-absorbing flexion','Good swing clearance'],
   actions:['Keep landings soft and quiet','Nudge cadence up ~5% if landings feel heavy'],
   evi:'Knee flexion in early stance attenuates vertical impact loading rates — the knee is the primary shock absorber at contact.'},
  {id:'arm', title:'Arm Swing (elbow)', score:62, status:'fair', joint:'R_ELB',
   see:'Arms near 90°, swinging in the sagittal plane.', tldr:'Functional arm swing, slight asymmetry.',
   eli5:'Swing arms like pendulums, straight back — never across the chest, which twists you sideways.',
   signs:['Functional 90° flexion','Slight trailing-arm asymmetry'],
   actions:['Drive elbows straight back','Hands loosely closed, wrists neutral'],
   evi:'Arm drive counterbalances torso rotational moments — economical swing stabilizes the trunk and steadies cadence.'},
  {id:'foot', title:'Foot Strike & Overstride', score:62, status:'fair', joint:'R_ANK',
   see:'Midfoot contact, nearly vertical tibia under sand.', tldr:'Foot lands close to center of mass.',
   eli5:'Step beneath yourself, not far ahead. Landing under hips rolls like a wheel; reaching ahead steps on the brakes.',
   signs:['Midfoot contact','Minimal overstride'],
   actions:['Land beneath hips, not ahead of knee','Light, quick turnover'],
   evi:'Landing near the center of mass minimizes braking impulse (Lieberman foot-strike work). Rearfoot alone is common even in elites — the risk combo is heel + locked knee + foot far ahead.'}
];
var STATUS_COLOR = {optimal:'#4ade80', fair:'#facc15', critical:'#f87171'};

/* skeleton from /tmp/skeleton.json (YOLOv8m-pose + anthropometric IK) */
var SK = {
  HIPM:[0,0.802,0], SHM:[0.127,1.299,0], NECK:[0.144,1.367,0], HEAD:[0.250,1.442,0],
  R_SH:[0.097,1.289,0.21], R_ELB:[-0.177,1.160,0.21], R_WR:[-0.066,0.898,0.21], R_HAND:[0.009,0.721,0.21],
  L_SH:[0.157,1.289,-0.21], L_ELB:[0.097,0.992,-0.21], L_WR:[0.353,1.117,-0.21], L_HAND:[0.526,1.201,-0.21],
  R_HIP:[-0.020,0.802,0.10], R_KNEE:[0.296,0.502,0.10], R_ANK:[0.367,0.070,0.10], R_TOE:[0.537,0.070,0.10],
  L_HIP:[0.020,0.802,-0.10], L_KNEE:[-0.241,0.453,-0.10], L_ANK:[-0.634,0.260,-0.10], L_TOE:[-0.787,0.185,-0.10]
};
SK.TRUNK = [(SK.HIPM[0]+SK.SHM[0])/2+0.07, (SK.HIPM[1]+SK.SHM[1])/2, 0.10];

var LIMBS = [
  ['SHM','NECK',0.058],
  ['R_SH','R_ELB',0.056],['R_ELB','R_WR',0.046],['R_WR','R_HAND',0.040],
  ['L_SH','L_ELB',0.056],['L_ELB','L_WR',0.046],['L_WR','L_HAND',0.040],
  ['R_HIP','R_KNEE',0.088],['R_KNEE','R_ANK',0.060],
  ['L_HIP','L_KNEE',0.088],['L_KNEE','L_ANK',0.060]
];
var BALLS = [
  ['HEAD',0.105],['R_SH',0.075],['L_SH',0.075],
  ['R_ELB',0.056],['L_ELB',0.056],['R_WR',0.044],['L_WR',0.044],
  ['R_KNEE',0.076],['L_KNEE',0.076],['R_ANK',0.055],['L_ANK',0.055]
];

var stage = document.getElementById('stage3d');
var labelLayer = document.getElementById('labels');
var pane = document.getElementById('pane');
var canvas = document.createElement('canvas');
stage.insertBefore(canvas, labelLayer);
var ctx = canvas.getContext('2d');

var CX=0.05, CY=0.85, CZ=0;
var yaw=0, pitch=0.07, zoom=1, auto=true;
var W=300, H=300, S=300, OX=150, OY=150, F=0.55, DPR=1;

function rot(p){
  var x=p[0]-CX, y=p[1]-CY, z=p[2]-CZ;
  var cy=Math.cos(yaw), sy=Math.sin(yaw);
  var x1=x*cy+z*sy, z1=-x*sy+z*cy;
  var cp=Math.cos(pitch), sp=Math.sin(pitch);
  return [x1, y*cp-z1*sp, y*sp+z1*cp];
}
function proj(p){
  var v=rot(p), d=1/(1+v[2]*F);
  return {x:OX+v[0]*S*d, y:OY-v[1]*S*d, d:d, z:v[2]};
}
function fit(){
  var mnx=1e9,mxx=-1e9,mny=1e9,mxy=-1e9;
  Object.keys(SK).forEach(function(k){
    var p=SK[k], x=(p[0]-CX), y=(p[1]-CY);
    if(x<mnx)mnx=x; if(x>mxx)mxx=x; if(y<mny)mny=y; if(y>mxy)mxy=y;
  });
  var s0=Math.min(W/((mxx-mnx)+1.1), H/((mxy-mny)+0.8));
  S=s0*zoom;
  OX=W/2-((mnx+mxx)/2)*S; OY=H/2+((mny+mxy)/2)*S;
}
function size(){
  DPR=Math.min(window.devicePixelRatio||1,2);
  W=stage.clientWidth; H=stage.clientHeight;
  canvas.width=W*DPR; canvas.height=H*DPR;
  canvas.style.width=W+'px'; canvas.style.height=H+'px';
  fit();
}
window.addEventListener('resize', size);

var stars=[];
for(var si=0;si<130;si++) stars.push({x:(Math.random()-0.5)*10, y:Math.random()*3.4-0.6, z:(Math.random()-0.5)*10, r:Math.random()*1.3+0.4, p:Math.random()*6.28});

/* ---------- upgraded body drawing ---------- */
function capsule(ax,ay,ar,bx,by,br){
  var dx=bx-ax, dy=by-ay, len=Math.hypot(dx,dy)||1;
  var nx=-dy/len, ny=dx/len;
  ctx.strokeStyle='rgba(0,0,0,0.35)'; ctx.lineWidth=1;
  var g=ctx.createLinearGradient(ax+nx*ar,ay+ny*ar,ax-nx*ar,ay-ny*ar);
  g.addColorStop(0,'#d8dde3'); g.addColorStop(0.45,'#9ea4ac'); g.addColorStop(1,'#54595f');
  ctx.fillStyle=g;
  ctx.beginPath();
  ctx.moveTo(ax+nx*ar,ay+ny*ar); ctx.lineTo(bx+nx*br,by+ny*br);
  ctx.arc(bx,by,Math.max(br,0.5),Math.atan2(ny,nx),Math.atan2(-ny,-nx));
  ctx.lineTo(ax-nx*ar,ay-ny*ar);
  ctx.arc(ax,ay,Math.max(ar,0.5),Math.atan2(-ny,-nx),Math.atan2(ny,nx));
  ctx.closePath(); ctx.fill(); ctx.stroke();
  /* gloss streak toward the light */
  ctx.strokeStyle='rgba(255,255,255,0.38)'; ctx.lineWidth=Math.max(1,ar*0.22); ctx.lineCap='round';
  ctx.beginPath();
  ctx.moveTo(ax+nx*ar*0.45,ay+ny*ar*0.45); ctx.lineTo(bx+nx*br*0.45,by+ny*br*0.45);
  ctx.stroke();
}
function ball2d(x,y,r){
  var g=ctx.createRadialGradient(x-r*0.35,y-r*0.4,r*0.1,x,y,r);
  g.addColorStop(0,'#e2e7ec'); g.addColorStop(0.55,'#9ea4ac'); g.addColorStop(1,'#50555b');
  ctx.fillStyle=g; ctx.beginPath(); ctx.arc(x,y,r,0,6.2832); ctx.fill();
  ctx.strokeStyle='rgba(0,0,0,0.3)'; ctx.lineWidth=1; ctx.stroke();
  ctx.fillStyle='rgba(255,255,255,0.75)';
  ctx.beginPath(); ctx.arc(x-r*0.33,y-r*0.38,Math.max(1,r*0.14),0,6.2832); ctx.fill();
}
/* hourglass torso: pelvis -> waist -> chest -> shoulders */
function torso(){
  var a=proj(SK.HIPM), b=proj(SK.SHM);
  var prof=[[0,0.150],[0.35,0.112],[0.70,0.148],[1,0.118]];
  var pts=prof.map(function(pr){
    var t=pr[0];
    return {x:a.x+(b.x-a.x)*t, y:a.y+(b.y-a.y)*t, r:pr[1]*S*((a.d+b.d)/2)};
  });
  var dx=b.x-a.x, dy=b.y-a.y, len=Math.hypot(dx,dy)||1, nx=-dy/len, ny=dx/len;
  var g=ctx.createLinearGradient(a.x,a.y,b.x,b.y);
  g.addColorStop(0,'#8f959d'); g.addColorStop(0.4,'#aeb4bc'); g.addColorStop(1,'#c9ced4');
  ctx.fillStyle=g;
  ctx.beginPath();
  pts.forEach(function(p,i){ var px=p.x+nx*p.r, py=p.y+ny*p.r; if(i===0)ctx.moveTo(px,py); else ctx.lineTo(px,py); });
  for(var i=pts.length-1;i>=0;i--){ var q=pts[i]; ctx.lineTo(q.x-nx*q.r, q.y-ny*q.r); }
  ctx.closePath(); ctx.fill();
  ctx.strokeStyle='rgba(0,0,0,0.35)'; ctx.lineWidth=1; ctx.stroke();
  /* edge shading: darker on the away side */
  var sh=ctx.createLinearGradient(a.x+nx*pts[0].r,a.y+ny*pts[0].r,a.x-nx*pts[0].r,a.y-ny*pts[0].r);
  sh.addColorStop(0,'rgba(255,255,255,0.20)'); sh.addColorStop(0.5,'rgba(255,255,255,0)'); sh.addColorStop(1,'rgba(0,0,0,0.28)');
  ctx.fillStyle=sh;
  ctx.beginPath();
  pts.forEach(function(p,i){ var px=p.x+nx*p.r, py=p.y+ny*p.r; if(i===0)ctx.moveTo(px,py); else ctx.lineTo(px,py); });
  for(var j=pts.length-1;j>=0;j--){ var r2=pts[j]; ctx.lineTo(r2.x-nx*r2.r, r2.y-ny*r2.r); }
  ctx.closePath(); ctx.fill();
}
/* shoe: tapered quad ankle->toe + sole stripe */
function shoe(A,T){
  var a=proj(SK[A]), b=proj(SK[T]);
  var dx=b.x-a.x, dy=b.y-a.y, len=Math.hypot(dx,dy)||1, nx=-dy/len, ny=dx/len;
  var ra=0.075*S*a.d, rb=0.048*S*b.d;
  var g=ctx.createLinearGradient(a.x,a.y- ra,a.x,a.y+ra);
  g.addColorStop(0,'#c4c9d0'); g.addColorStop(1,'#5b6067');
  ctx.fillStyle=g;
  ctx.beginPath();
  ctx.moveTo(a.x+nx*ra*0.4,a.y+ny*ra*0.4- ra*0.55);
  ctx.lineTo(b.x+nx*rb,b.y+ny*rb-rb*0.4);
  ctx.lineTo(b.x-nx*rb,b.y-ny*rb+rb*0.7);
  ctx.lineTo(a.x-nx*ra*0.4,a.y-ny*ra*0.4+ra*0.75);
  ctx.closePath(); ctx.fill();
  ctx.strokeStyle='rgba(0,0,0,0.4)'; ctx.lineWidth=1; ctx.stroke();
  /* sole */
  ctx.strokeStyle='rgba(230,234,238,0.85)'; ctx.lineWidth=Math.max(1.5,ra*0.28);
  ctx.beginPath(); ctx.moveTo(a.x-nx*ra*0.4,a.y-ny*ra*0.4+ra*0.75); ctx.lineTo(b.x-nx*rb,b.y-ny*rb+rb*0.7); ctx.stroke();
}

function drawFigure(){
  var items=[];
  LIMBS.forEach(function(L){
    var a=proj(SK[L[0]]), b=proj(SK[L[1]]);
    items.push({z:Math.min(a.z,b.z), k:'l', a:a, b:b, r:L[2]});
  });
  BALLS.forEach(function(B){
    var p=proj(SK[B[0]]);
    items.push({z:p.z, k:'b', p:p, r:B[1]});
  });
  /* torso + shoes drawn at pelvis/ankle depth */
  var tz=(rot(SK.HIPM)[2]+rot(SK.SHM)[2])/2;
  items.push({z:tz+0.001, k:'t'});
  items.push({z:rot(SK.R_ANK)[2]-0.001, k:'s', w:'R'});
  items.push({z:rot(SK.L_ANK)[2]-0.001, k:'s', w:'L'});
  items.sort(function(m,n){ return m.z-n.z; });
  items.forEach(function(it){
    if(it.k==='l') capsule(it.a.x,it.a.y,it.r*S*it.a.d, it.b.x,it.b.y,it.r*S*it.b.d);
    else if(it.k==='b') ball2d(it.p.x,it.p.y,it.r*S*it.p.d);
    else if(it.k==='t') torso();
    else shoe(it.w+'_ANK', it.w+'_TOE');
  });
}

/* ---------- pane, chips, interaction (unchanged behavior) ---------- */
function renderPane(z){
  var c=STATUS_COLOR[z.status];
  pane.innerHTML =
    '<div class="lbl">Zone detail · click markers to switch</div>' +
    '<div class="p-title">'+z.title+'</div>' +
    '<span class="p-score" style="background:rgba(250,204,21,.13);color:'+c+'">'+z.score+' · '+z.status.toUpperCase()+'</span>' +
    '<div class="sec"><h4>WHAT WE SEE</h4><p>'+z.see+'</p></div>' +
    '<div class="sec"><h4>TL;DR</h4><p>'+z.tldr+'</p></div>' +
    '<div class="sec"><h4>ELI5</h4><p>'+z.eli5+'</p></div>' +
    '<div class="sec"><h4>SIGNS</h4><div class="signs">'+z.signs.map(function(s){return '<span class="sign">'+s+'</span>';}).join('')+'</div></div>' +
    '<div class="sec"><h4>WHAT TO DO</h4><ul class="actions">'+z.actions.map(function(a){return '<li>'+a+'</li>';}).join('')+'</ul></div>' +
    '<div class="sec evi"><b>WHY SCIENCE SAYS SO</b>'+z.evi+'</div>';
}
renderPane(ZONES[0]);

ZONES.forEach(function(z){
  var el=document.createElement('div');
  el.className='tag';
  el.innerHTML='<span class="dot" style="background:'+STATUS_COLOR[z.status]+'"></span><span><b>'+z.title+' · '+z.score+'</b><span>'+z.tldr+'</span></span>';
  el.addEventListener('click',function(){ select(z.id); });
  labelLayer.appendChild(el); z._el=el;
});
function select(id){
  var z=null; ZONES.forEach(function(o){ if(o.id===id) z=o; });
  if(!z) return;
  renderPane(z);
  ZONES.forEach(function(o){ o._el.classList.toggle('sel', o.id===id); });
  if(window.innerWidth<=900) pane.scrollIntoView({behavior:'smooth',block:'nearest'});
}

var down=null, moved=0;
canvas.style.touchAction='none';
canvas.addEventListener('pointerdown',function(e){ auto=false; down=[e.clientX,e.clientY]; moved=0; canvas.setPointerCapture(e.pointerId); });
canvas.addEventListener('pointermove',function(e){
  if(!down) return;
  var dx=e.clientX-down[0], dy=e.clientY-down[1];
  moved+=Math.abs(dx)+Math.abs(dy);
  yaw+=dx*0.008; pitch=Math.max(-0.15,Math.min(0.6,pitch+dy*0.004));
  down=[e.clientX,e.clientY]; fit();
});
canvas.addEventListener('pointerup',function(e){
  var wasTap = down && moved<8; down=null;
  if(!wasTap) return;
  var r=canvas.getBoundingClientRect(), mx=e.clientX-r.left, my=e.clientY-r.top;
  var best=null, bd=26;
  ZONES.forEach(function(z){ var d=Math.hypot(z._sx-mx, z._sy-my); if(d<bd){bd=d;best=z;} });
  if(best) select(best.id);
});
canvas.addEventListener('wheel',function(e){ e.preventDefault(); auto=false; zoom=Math.max(0.55,Math.min(1.8,zoom*(1-e.deltaY*0.001))); fit(); },{passive:false});

var T0=performance.now();
function frame(now){
  requestAnimationFrame(frame);
  var t=(now-T0)/1000;
  if(auto) yaw=0.38*Math.sin(t*0.45);
  fit();
  ctx.setTransform(DPR,0,0,DPR,0,0);
  ctx.clearRect(0,0,W,H);

  stars.forEach(function(s){
    var a=0.25+0.35*Math.abs(Math.sin(t*0.9+s.p));
    var sx=((s.x*Math.cos(yaw*0.12)-s.z*Math.sin(yaw*0.12))/9+0.5)*W;
    var sy=H*0.08+((s.y+0.6)/4.2)*H*0.9;
    ctx.fillStyle='rgba(160,160,180,'+a.toFixed(2)+')';
    ctx.fillRect(sx,sy,s.r,s.r);
  });

  /* floor: lime horizon ring + soft shadow */
  var gb=proj([0.05,0,0]);
  ctx.strokeStyle='rgba(214,245,66,0.14)'; ctx.lineWidth=1.5;
  ctx.beginPath(); ctx.ellipse(gb.x,gb.y+8,S*0.62,S*0.11,0,0,6.2832); ctx.stroke();
  var sh=ctx.createRadialGradient(gb.x,gb.y+6,4,gb.x,gb.y+6,S*0.55);
  sh.addColorStop(0,'rgba(0,0,0,0.5)'); sh.addColorStop(1,'rgba(0,0,0,0)');
  ctx.fillStyle=sh;
  ctx.beginPath(); ctx.ellipse(gb.x,gb.y+6,S*0.55,S*0.10,0,0,6.2832); ctx.fill();

  /* faint floor reflection */
  var gy=proj([0,0,0]).y;
  ctx.save(); ctx.translate(0,2*gy); ctx.scale(1,-1); ctx.globalAlpha=0.10;
  drawFigure(); ctx.restore(); ctx.globalAlpha=1;

  drawFigure();

  /* markers + callout chips */
  var chestZ=rot(SK.SHM)[2];
  var placed=[];
  ZONES.forEach(function(z){
    var p=proj(SK[z.joint]); z._sx=p.x; z._sy=p.y;
    var c=STATUS_COLOR[z.status];
    var pulse=8+2*Math.sin(t*3+z.score);
    var gl=ctx.createRadialGradient(p.x,p.y,1,p.x,p.y,24);
    gl.addColorStop(0,c); gl.addColorStop(1,'rgba(0,0,0,0)');
    ctx.globalAlpha=0.45; ctx.fillStyle=gl;
    ctx.beginPath(); ctx.arc(p.x,p.y,24,0,6.2832); ctx.fill();
    ctx.globalAlpha=1;
    ctx.strokeStyle=c; ctx.lineWidth=2.5;
    ctx.beginPath(); ctx.arc(p.x,p.y,pulse,0,6.2832); ctx.stroke();
    ctx.fillStyle=c; ctx.beginPath(); ctx.arc(p.x,p.y,4.5,0,6.2832); ctx.fill();
    ctx.fillStyle='#0a0a0b'; ctx.beginPath(); ctx.arc(p.x,p.y,1.8,0,6.2832); ctx.fill();
    placed.push({z:z, x:p.x, y:p.y});
  });
  var sides=[[],[]];
  placed.forEach(function(o){ ((o.x>=OX)?sides[1]:sides[0]).push(o); });
  sides.forEach(function(group,gi){
    group.sort(function(a,b){return a.y-b.y;});
    for(var i=1;i<group.length;i++){
      var need=(group[i-1].z._el.offsetHeight||70)+14;
      if(group[i].y-group[i-1].y<need) group[i].y=group[i-1].y+need;
    }
    group.forEach(function(o){
      var side=gi===1?1:-1;
      o.cx=Math.max(115,Math.min(W-115,o.x+side*150));
      o.cy=Math.max(46,Math.min(H-40,o.y-24));
    });
  });
  placed.forEach(function(o){
    var el=o.z._el;
    el.style.display='flex'; el.style.left=o.cx+'px'; el.style.top=o.cy+'px';
    var halfW=(el.offsetWidth||190)/2;
    var ex=o.cx+((o.cx>o.z._sx)?-halfW:halfW);
    ctx.strokeStyle='rgba(255,255,255,0.28)'; ctx.lineWidth=1;
    ctx.beginPath(); ctx.moveTo(o.z._sx,o.z._sy); ctx.lineTo(ex,o.cy); ctx.stroke();
    var mz=rot(SK[o.z.joint])[2];
    el.classList.toggle('dim', mz<chestZ-0.06);
  });
}
size();
requestAnimationFrame(frame);
})();
