
/* DIAL FOR SERVICE - ALL PHASES client enhancements */
(function(){
  window.dfsToast=function(msg){
    var t=document.getElementById('dfsToast');
    if(!t){t=document.createElement('div');t.id='dfsToast';t.className='dfs-toast';document.body.appendChild(t)}
    t.textContent=msg;t.style.display='block';clearTimeout(window._dfsToast);
    window._dfsToast=setTimeout(function(){t.style.display='none'},2600);
  };
  window.dfsFilter=function(inputId, selector){
    var q=(document.getElementById(inputId)?.value||'').toLowerCase().trim();
    document.querySelectorAll(selector).forEach(function(el){
      el.style.display=(!q || (el.innerText||'').toLowerCase().includes(q))?'':'none';
    });
  };
  window.dfsSortCards=function(containerSelector, mode){
    var c=document.querySelector(containerSelector); if(!c)return;
    var items=[...c.children];
    items.sort(function(a,b){
      var A=(a.innerText||'').trim().toLowerCase(),B=(b.innerText||'').trim().toLowerCase();
      return mode==='za'?B.localeCompare(A):A.localeCompare(B);
    }).forEach(function(x){c.appendChild(x)});
  };
})();
