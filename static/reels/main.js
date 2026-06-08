// ═══════════════════════════════════════════════════════════════
//  VIBE — reels/main.js
//  Vertical snap feed · autoplay · view count · like/save/repost
//  Ratio-aware playback · keyboard nav · double-tap like
// ═══════════════════════════════════════════════════════════════

function getCookie(n) {
  return document.cookie.split(';').map(c => c.trim())
    .find(c => c.startsWith(n + '='))?.split('=')[1] ?? '';
}

// ── Apply reel ratio to .reel-video ──────────────────────────────
function applyRatioToCard(card) {
  const ratio = card.dataset.ratio || '9:16';
  const video = card.querySelector('.reel-video');
  if (!video) return;
  const map = { '9:16': 'cover', '4:5': 'cover', '1:1': 'cover' };
  // All ratios use object-fit:cover; the card container clips it
  video.style.objectFit = 'cover';
  // Adjust the card's inner video aspect for 1:1 and 4:5
  if (ratio === '1:1') {
    video.style.width  = '56.25vh';   // square inside the 9:16 viewport
    video.style.height = '56.25vh';
    video.style.margin = 'auto';
  } else if (ratio === '4:5') {
    video.style.width  = '80%';
    video.style.height = '100%';
    video.style.margin = 'auto';
  } else {
    video.style.width  = '100%';
    video.style.height = '100%';
    video.style.margin = '0';
  }
}

// ── Track whether we've already counted a view per card ──────────
const viewedCards = new Set();

function recordView(card) {
  const id  = card.dataset.id;
  const url = card.dataset.viewUrl;
  if (!url || viewedCards.has(id)) return;
  viewedCards.add(id);

  fetch(url, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrftoken') },
  })
    .then(r => r.json())
    .then(d => {
      const el = document.getElementById(`views-${id}`);
      if (el) el.textContent = d.views;
    })
    .catch(() => {});
}

// ── Progress bar helpers ─────────────────────────────────────────
const progressIntervals = new Map();

function startProgress(card, video) {
  const bar = document.getElementById(`prog-${card.dataset.id}`);
  if (!bar) return;
  stopProgress(card);
  const id = setInterval(() => {
    if (!video.duration) return;
    const pct = (video.currentTime / video.duration) * 100;
    bar.style.width = pct + '%';
  }, 100);
  progressIntervals.set(card.dataset.id, id);
}

function stopProgress(card) {
  const id = progressIntervals.get(card.dataset.id);
  if (id) { clearInterval(id); progressIntervals.delete(card.dataset.id); }
  const bar = document.getElementById(`prog-${card.dataset.id}`);
  if (bar) bar.style.width = '0';
}

// ── IntersectionObserver — autoplay / pause ──────────────────────
let viewTimers = new Map();

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    const card  = entry.target;
    const video = card.querySelector('.reel-video');
    if (!video) return;

    if (entry.isIntersecting) {
      // Lazy-load src
      if (!video.src && video.dataset.src) {
        video.src = video.dataset.src;
      }
      applyRatioToCard(card);
      video.play().catch(() => {});
      startProgress(card, video);

      // Count a view after 2 seconds of watching
      const t = setTimeout(() => recordView(card), 2000);
      viewTimers.set(card.dataset.id, t);

    } else {
      video.pause();
      video.currentTime = 0;
      stopProgress(card);
      // Cancel pending view timer if user scrolled away quickly
      const t = viewTimers.get(card.dataset.id);
      if (t) { clearTimeout(t); viewTimers.delete(card.dataset.id); }
    }
  });
}, { threshold: 0.75 });

document.querySelectorAll('.reel-card').forEach(card => observer.observe(card));

// ── Tap to play / pause ──────────────────────────────────────────
document.querySelectorAll('.reel-tap-overlay').forEach(overlay => {
  let lastTap = 0;

  overlay.addEventListener('click', function (e) {
    const now  = Date.now();
    const card = this.closest('.reel-card');
    const id   = card.dataset.id;

    if (now - lastTap < 280) {
      // ── Double tap → like ─────────────────────────────────────
      const likeBtn = card.querySelector('.reel-like');
      if (likeBtn && !likeBtn.classList.contains('liked')) {
        likeBtn.click();
        showHeartBurst(card);
      }
    } else {
      // ── Single tap → play / pause ─────────────────────────────
      const video = card.querySelector('.reel-video');
      const icon  = document.getElementById(`playicon-${id}`);
      if (!video) return;

      if (video.paused) {
        video.play();
        if (icon) { icon.style.display = 'none'; }
      } else {
        video.pause();
        if (icon) {
          icon.style.display = 'flex';
          // Re-trigger CSS animation
          icon.style.animation = 'none';
          void icon.offsetHeight;
          icon.style.animation = '';
        }
      }
    }
    lastTap = now;
  });
});

// ── Heart burst animation ────────────────────────────────────────
function showHeartBurst(card) {
  const h = document.createElement('div');
  h.className = 'heart-burst-anim';
  h.textContent = '♥';
  card.appendChild(h);
  setTimeout(() => h.remove(), 800);
}

// Inject keyframes once
if (!document.getElementById('reelKeyframes')) {
  const s = document.createElement('style');
  s.id = 'reelKeyframes';
  s.textContent = `
    .heart-burst-anim {
      position:absolute; top:50%; left:50%;
      transform: translate(-50%,-50%) scale(0);
      font-size:90px; color:#fff;
      pointer-events:none; z-index:20;
      text-shadow:0 2px 20px rgba(0,0,0,.3);
      animation: hburst .75s ease forwards;
    }
    @keyframes hburst {
      0%  { opacity:1; transform:translate(-50%,-50%) scale(0); }
      40% { opacity:1; transform:translate(-50%,-50%) scale(1.3); }
      100%{ opacity:0; transform:translate(-50%,-50%) scale(1.7); }
    }
  `;
  document.head.appendChild(s);
}

// ── Like ─────────────────────────────────────────────────────────
document.querySelectorAll('.reel-like').forEach(btn => {
  btn.addEventListener('click', async function (e) {
    e.stopPropagation();
    const res  = await fetch(this.dataset.url, {
      method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    const d   = await res.json();
    const svg = this.querySelector('.heart-svg');
    this.classList.toggle('liked', d.liked);
    this.classList.add('pop');
    setTimeout(() => this.classList.remove('pop'), 300);
    if (svg) svg.setAttribute('fill', d.liked ? 'currentColor' : 'none');
    const countEl = this.querySelector('.like-count');
    if (countEl) countEl.textContent = d.count;
  });
});

// ── Save ─────────────────────────────────────────────────────────
document.querySelectorAll('.reel-save').forEach(btn => {
  btn.addEventListener('click', async function (e) {
    e.stopPropagation();
    const res = await fetch(this.dataset.url, {
      method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    const d   = await res.json();
    const svg = this.querySelector('.save-svg');
    this.classList.toggle('saved', d.saved);
    if (svg) svg.setAttribute('fill', d.saved ? 'currentColor' : 'none');
  });
});

// ── Repost ───────────────────────────────────────────────────────
document.querySelectorAll('.reel-repost').forEach(btn => {
  btn.addEventListener('click', async function (e) {
    e.stopPropagation();
    const res = await fetch(this.dataset.url, {
      method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    const d = await res.json();
    this.classList.toggle('reposted', d.reposted);
  });
});

// ── Follow from feed ─────────────────────────────────────────────
document.querySelectorAll('.reel-follow-btn').forEach(btn => {
  btn.addEventListener('click', async function (e) {
    e.preventDefault(); e.stopPropagation();
    const res = await fetch(this.dataset.url, {
      method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    const d = await res.json();
    if (d.action === 'followed' || d.action === 'requested') {
      this.textContent = d.action === 'followed' ? 'Following' : 'Requested';
      this.style.opacity = '0.6';
      this.disabled = true;
    }
  });
});

// ── Keyboard nav ─────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  const feed = document.getElementById('reelsFeed');
  if (!feed) return;
  if (e.key === 'ArrowDown' || e.key === ' ') {
    e.preventDefault();
    feed.scrollBy({ top: window.innerHeight, behavior: 'smooth' });
  }
  if (e.key === 'ArrowUp') {
    e.preventDefault();
    feed.scrollBy({ top: -window.innerHeight, behavior: 'smooth' });
  }
});