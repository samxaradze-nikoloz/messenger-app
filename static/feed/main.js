// ── CSRF ─────────────────────────────────────────────────────────
function getCookie(name) {
  return document.cookie.split(';')
    .map(c => c.trim())
    .find(c => c.startsWith(name + '='))
    ?.split('=')[1] ?? '';
}

// ── Feed carousels ────────────────────────────────────────────────
document.querySelectorAll('.feed-images').forEach(wrap => {
  const slides = wrap.querySelectorAll('.feed-slide');
  const dots   = wrap.querySelectorAll('.fc-dot');
  if (slides.length < 2) return;
  let cur = 0;

  function go(i) {
    slides[cur].classList.remove('active');
    dots[cur]?.classList.remove('active');
    cur = (i + slides.length) % slides.length;
    slides[cur].classList.add('active');
    dots[cur]?.classList.add('active');
  }

  wrap.querySelector('.fc-prev')?.addEventListener('click', () => go(cur - 1));
  wrap.querySelector('.fc-next')?.addEventListener('click', () => go(cur + 1));
  dots.forEach(d => d.addEventListener('click', () => go(+d.dataset.idx)));

  // Swipe
  let tx = 0;
  wrap.addEventListener('touchstart', e => { tx = e.touches[0].clientX; });
  wrap.addEventListener('touchend',   e => {
    const dx = e.changedTouches[0].clientX - tx;
    if (Math.abs(dx) > 40) go(dx < 0 ? cur + 1 : cur - 1);
  });
});

// ── Like ─────────────────────────────────────────────────────────
document.querySelectorAll('.feed-like').forEach(btn => {
  btn.addEventListener('click', async function () {
    const res  = await fetch(this.dataset.url, { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } });
    const data = await res.json();
    const svg  = this.querySelector('.heart-svg');
    this.classList.toggle('liked', data.liked);
    svg.setAttribute('fill', data.liked ? 'currentColor' : 'none');
    this.closest('.feed-card').querySelector('.lc').textContent = data.count;
    this.classList.add('pop');
    setTimeout(() => this.classList.remove('pop'), 300);
  });

  // Double-tap image
  const card = btn.closest('.feed-card');
  card?.querySelector('.feed-images')?.addEventListener('dblclick', () => {
    if (!btn.classList.contains('liked')) btn.click();
    showHeartBurst(card.querySelector('.feed-images'));
  });
});

function showHeartBurst(target) {
  const h = document.createElement('div');
  h.className = 'heart-burst';
  h.textContent = '♥';
  target.appendChild(h);
  setTimeout(() => h.remove(), 700);
}

// ── Save ─────────────────────────────────────────────────────────
document.querySelectorAll('.feed-save').forEach(btn => {
  btn.addEventListener('click', async function () {
    const res  = await fetch(this.dataset.url, { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } });
    const data = await res.json();
    const svg  = this.querySelector('.save-svg');
    this.classList.toggle('saved', data.saved);
    svg.setAttribute('fill', data.saved ? 'currentColor' : 'none');
  });
});

// ── Quick comment ─────────────────────────────────────────────────
document.querySelectorAll('.quick-comment-form').forEach(form => {
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const input = form.querySelector('.quick-comment-input');
    const body  = input.value.trim();
    if (!body) return;
    const fd = new FormData(form);
    await fetch(form.dataset.url, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken'), 'X-Requested-With': 'XMLHttpRequest' },
      body: fd,
    });
    input.value = '';
    // bump comment count visually
    const link = form.closest('.feed-card').querySelector('.view-comments');
    if (link) {
      const m = link.textContent.match(/\d+/);
      if (m) link.textContent = `View all ${parseInt(m[0]) + 1} comments`;
    }
  });
});