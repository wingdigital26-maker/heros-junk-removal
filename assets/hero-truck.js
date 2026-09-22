(function(){
  var stage=document.getElementById('heroStage');
  if(!stage) return;
  var reduce=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(reduce) return;

  var tiltX=0,tiltY=0,curX=0,curY=0,raf=null;

  function loop(){
    curX+=(tiltX-curX)*0.08;
    curY+=(tiltY-curY)*0.08;
    stage.style.setProperty('--tx',curX.toFixed(2)+'deg');
    stage.style.setProperty('--ty',curY.toFixed(2)+'deg');
    if(Math.abs(tiltX-curX)>0.01||Math.abs(tiltY-curY)>0.01){
      raf=requestAnimationFrame(loop);
    }else{
      raf=null;
    }
  }

  function onMove(e){
    var r=stage.getBoundingClientRect();
    var cx=r.left+r.width/2, cy=r.top+r.height/2;
    var dx=(e.clientX-cx)/(r.width/2||1);
    var dy=(e.clientY-cy)/(r.height/2||1);
    tiltY=Math.max(-1,Math.min(1,dx))*5;
    tiltX=Math.max(-1,Math.min(1,-dy))*4;
    if(!raf) raf=requestAnimationFrame(loop);
  }
  function onLeave(){
    tiltX=0;tiltY=0;
    if(!raf) raf=requestAnimationFrame(loop);
  }

  if(window.matchMedia('(min-width:821px)').matches && matchMedia('(hover:hover)').matches){
    window.addEventListener('mousemove',onMove,{passive:true});
    window.addEventListener('mouseleave',onLeave,{passive:true});
  }
})();
