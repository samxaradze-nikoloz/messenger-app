// ─── CSRF helper ─────────────────────────────────────────────
function getCookie(name) {
  return document.cookie.split(';')
    .map(c => c.trim())
    .find(c => c.startsWith(name + '='))
    ?.split('=')[1] ?? '';
}

// ─── Auto-dismiss toasts ──────────────────────────────────────
document.querySelectorAll('.toast').forEach(t => {
  setTimeout(() => t.style.opacity = '0', 3000);
  setTimeout(() => t.remove(), 3400);
});

// ─── Search: live submit on type ──────────────────────────────
const searchInput = document.querySelector('.search-input');
if (searchInput) {
  let searchTimer;
  searchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => searchInput.closest('form').submit(), 400);
  });
}

// ─── Follow button (list pages) ───────────────────────────────
document.querySelectorAll('.btn-follow-sm').forEach(btn => {
  btn.addEventListener('click', async (e) => {
    e.preventDefault();
    const url = btn.dataset.url;
    if (!url) return;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    const data = await res.json();
    if (data.action === 'followed') {
      btn.textContent = 'Following';
      btn.classList.add('following');
    } else if (data.action === 'requested') {
      btn.textContent = 'Requested';
    } else {
      btn.textContent = 'Follow';
      btn.classList.remove('following');
    }
  });
});