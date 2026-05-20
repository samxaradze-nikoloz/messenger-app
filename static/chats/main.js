// ── CSRF ─────────────────────────────────────────────────────────
function getCookie(name) {
  return document.cookie.split(';')
    .map(c => c.trim())
    .find(c => c.startsWith(name + '='))
    ?.split('=')[1] ?? '';
}

// ── Detail page carousel (multi-image) ──────────────────────────
const slides = document.querySelectorAll('.carousel-slide');
const dots   = document.querySelectorAll('.dot');
let curSlide = 0;

function goToSlide(i) {
  if (!slides.length) return;
  slides[curSlide].classList.remove('active');
  dots[curSlide]?.classList.remove('active');
  curSlide = (i + slides.length) % slides.length;
  slides[curSlide].classList.add('active');
  dots[curSlide]?.classList.add('active');
}

document.getElementById('prevBtn')?.addEventListener('click', () => goToSlide(curSlide - 1));
document.getElementById('nextBtn')?.addEventListener('click', () => goToSlide(curSlide + 1));
dots.forEach(d => d.addEventListener('click', () => goToSlide(+d.dataset.idx)));

// Swipe on detail carousel
let touchStartX = 0;
document.querySelector('.carousel')?.addEventListener('touchstart', e => { touchStartX = e.touches[0].clientX; });
document.querySelector('.carousel')?.addEventListener('touchend', e => {
  const dx = e.changedTouches[0].clientX - touchStartX;
  if (Math.abs(dx) > 40) goToSlide(dx < 0 ? curSlide + 1 : curSlide - 1);
});

// ── Detail: like ─────────────────────────────────────────────────
document.querySelector('.like-btn')?.addEventListener('click', async function () {
  const res  = await fetch(this.dataset.url, { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } });
  const data = await res.json();
  const icon = this.querySelector('.heart-icon');
  this.classList.toggle('liked', data.liked);
  icon.setAttribute('fill', data.liked ? 'currentColor' : 'none');
  document.getElementById('likesCount').textContent = data.count;
  this.classList.add('pop');
  setTimeout(() => this.classList.remove('pop'), 300);
});

// Double-tap image to like on detail page
document.querySelector('.detail-images')?.addEventListener('dblclick', () => {
  document.querySelector('.like-btn')?.click();
});

// ── Detail: save ─────────────────────────────────────────────────
document.querySelector('.save-btn')?.addEventListener('click', async function () {
  const res  = await fetch(this.dataset.url, { method: 'POST', headers: { 'X-CSRFToken': getCookie('csrftoken') } });
  const data = await res.json();
  const icon = this.querySelector('.save-icon');
  this.classList.toggle('saved', data.saved);
  icon.setAttribute('fill', data.saved ? 'currentColor' : 'none');
});

// ── Detail: comment submit ────────────────────────────────────────
const commentForm = document.getElementById('commentForm');
commentForm?.addEventListener('submit', async e => {
  e.preventDefault();
  const body = document.getElementById('commentBody').value.trim();
  if (!body) return;
  const fd  = new FormData(commentForm);
  const res = await fetch(commentForm.dataset.url, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrftoken'), 'X-Requested-With': 'XMLHttpRequest' },
    body: fd,
  });
  const d = await res.json();
  if (d.id) {
    appendComment(d);
    document.getElementById('commentBody').value = '';
    document.getElementById('parentId').value    = '';
    document.getElementById('replyIndicator').style.display = 'none';
  }
});

function appendComment(d) {
  const area = document.getElementById('commentsArea');
  const noComments = area.querySelector('.no-comments');
  if (noComments) noComments.remove();
  const div = document.createElement('div');
  div.className = 'comment-item' + (d.is_reply ? ' reply-item' : '');
  const avHtml = d.avatar
    ? `<img src="${d.avatar}" class="comment-av${d.is_reply?' comment-av-sm':''}" />`
    : `<div class="comment-av-ph${d.is_reply?' comment-av-sm':''}">${d.author[0].toUpperCase()}</div>`;
  div.innerHTML = `
    ${d.is_reply ? '<div class="reply-indent"></div>' : ''}
    <div class="comment-av-wrap">${avHtml}</div>
    <div class="comment-body">
      <span class="comment-un">${d.author}</span> ${d.body}
      <div class="comment-meta"><span class="comment-date">just now</span></div>
    </div>`;
  area.appendChild(div);
  area.scrollTop = area.scrollHeight;
}

// ── Detail: reply buttons ─────────────────────────────────────────
document.querySelectorAll('.reply-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.getElementById('parentId').value     = btn.dataset.id;
    document.getElementById('replyingTo').textContent = '@' + btn.dataset.un;
    document.getElementById('replyIndicator').style.display = 'flex';
    document.getElementById('commentBody').focus();
  });
});
document.getElementById('cancelReply')?.addEventListener('click', () => {
  document.getElementById('parentId').value = '';
  document.getElementById('replyIndicator').style.display = 'none';
});

document.querySelector('.comment-trigger-btn')?.addEventListener('click', () => {
  document.getElementById('commentBody')?.focus();
});