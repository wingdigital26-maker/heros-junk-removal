(function(){
  document.documentElement.classList.add('js');

  var burger = document.querySelector('.t-burger');
  var menu = document.querySelector('.t-mobile-menu');
  if(burger && menu){
    burger.addEventListener('click', function(){
      menu.classList.toggle('open');
    });
    menu.querySelectorAll('a').forEach(function(a){
      a.addEventListener('click', function(){ menu.classList.remove('open'); });
    });
  }

  var els = Array.prototype.slice.call(document.querySelectorAll('.rise'));

  function reveal(el){ el.classList.add('in'); }

  if('IntersectionObserver' in window){
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(entry){
        if(entry.isIntersecting){
          reveal(entry.target);
          io.unobserve(entry.target);
        }
      });
    }, {threshold:0.15, rootMargin:'0px 0px -60px 0px'});
    els.forEach(function(el){ io.observe(el); });
  } else {
    els.forEach(reveal);
  }

  // Failsafe: nothing should stay hidden forever.
  setTimeout(function(){
    els.forEach(reveal);
  }, 2500);
})();
