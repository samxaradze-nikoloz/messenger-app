// Poll unread count every 30s and update nav badge
(function(){
  const badge = document.getElementById('notifBadge');
  if(!badge) return;
  function poll(){
    fetch('/notifications/unread/')
      .then(r=>r.json())
      .then(d=>{
        if(d.count>0){badge.textContent=d.count>99?'99+':d.count;badge.style.display='flex';}
        else badge.style.display='none';
      }).catch(()=>{});
  }
  poll();
  setInterval(poll,30000);
})();