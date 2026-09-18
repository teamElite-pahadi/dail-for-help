(function(){
  const key='dial-theme';
  const saved=localStorage.getItem(key);
  if(saved==='dark') document.documentElement.classList.add('dark-mode');
  window.toggleTheme=function(){
    document.documentElement.classList.toggle('dark-mode');
    localStorage.setItem(key,document.documentElement.classList.contains('dark-mode')?'dark':'light');
  };
})();
