// ═══════════════════════════════════════════════════════════════
//  VIBE — chats/main.js
//  Handles: WebSocket messaging, typing, stickers, images,
//           replies, delete, lightbox, real WebRTC calls
// ═══════════════════════════════════════════════════════════════

// ── Helpers ──────────────────────────────────────────────────────
function getCookie(name) {
  return document.cookie.split(';')
    .map(c => c.trim())
    .find(c => c.startsWith(name + '='))
    ?.split('=')[1] ?? '';
}

// ── Lightbox ─────────────────────────────────────────────────────
function openLightbox(src) {
  const lb = document.getElementById('lightbox');
  if (!lb) return;
  document.getElementById('lightboxImg').src = src;
  lb.style.display = 'flex';
}
document.getElementById('lightbox')?.addEventListener('click', function (e) {
  if (e.target === this || e.target.classList.contains('lightbox-close')) {
    this.style.display = 'none';
  }
});

// ── Reply ─────────────────────────────────────────────────────────
let replyId = null;

function setReply(id, sender, body) {
  replyId = id;
  document.getElementById('replyToId').value = id;
  document.getElementById('rbSender').textContent = sender;
  document.getElementById('rbBody').textContent   = body;
  document.getElementById('replyBar').style.display = 'flex';
  document.getElementById('msgInput').focus();
}

function cancelReply() {
  replyId = null;
  document.getElementById('replyToId').value = '';
  document.getElementById('replyBar').style.display = 'none';
}

// ── Image pick ────────────────────────────────────────────────────
let pendingImageFile = null;

document.getElementById('imgFileInput')?.addEventListener('change', function () {
  const file = this.files[0];
  if (!file) return;
  pendingImageFile = file;
  const reader = new FileReader();
  reader.onload = e => {
    document.getElementById('imgPreviewThumb').src = e.target.result;
    document.getElementById('imgPreviewName').textContent = file.name;
    document.getElementById('imgPreviewBar').style.display = 'flex';
  };
  reader.readAsDataURL(file);
});

function cancelImage() {
  pendingImageFile = null;
  const input = document.getElementById('imgFileInput');
  if (input) input.value = '';
  document.getElementById('imgPreviewBar').style.display = 'none';
}

// ── Sticker picker ────────────────────────────────────────────────
document.getElementById('stickerToggle')?.addEventListener('click', function () {
  const p = document.getElementById('stickerPicker');
  if (!p) return;
  p.style.display = p.style.display === 'none' ? 'block' : 'none';
});

// ── Delete message ────────────────────────────────────────────────
async function deleteMsg(btn, id) {
  if (!confirm('Delete this message?')) return;
  const res = await fetch(btn.dataset.url, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrftoken') }
  });
  const d = await res.json();
  if (d.deleted) {
    const bubble = document.querySelector(`#msg-${id} .msg-bubble`);
    if (bubble) {
      bubble.classList.add('deleted');
      bubble.innerHTML = '<em class="msg-deleted">🚫 Message deleted</em>';
    }
    const meta = document.querySelector(`#msg-${id} .msg-meta-row`);
    if (meta) meta.innerHTML = '';
  }
}

// ── Append a new message to the DOM ──────────────────────────────
function appendMessage(d, isGroup, deleteUrlBase) {
  const area = document.getElementById('msgArea');
  if (!area) return;

  const wrap = document.createElement('div');
  wrap.id = `msg-${d.id}`;
  wrap.dataset.id = d.id;
  wrap.className = `msg-wrap ${d.is_mine ? 'mine' : 'theirs'}`;

  // Avatar (only for other people's messages)
  let avatarHtml = '';
  if (!d.is_mine) {
    avatarHtml = d.sender_av
      ? `<div class="msg-av-wrap"><img src="${d.sender_av}" class="msg-av" title="${d.sender}" /></div>`
      : `<div class="msg-av-wrap"><div class="msg-av-ph" title="${d.sender}">${d.sender[0].toUpperCase()}</div></div>`;
  }

  // Reply preview
  let replyHtml = '';
  if (d.reply_to && d.reply_to.sender) {
    replyHtml = `
      <div class="msg-reply-preview">
        <span class="mrp-bar"></span>
        <div>
          <span class="mrp-sender">${d.reply_to.sender}</span>
          <span class="mrp-body">${d.reply_to.body || '📷 Photo'}</span>
        </div>
      </div>`;
  }

  // Bubble content
  let bubbleContent = '';
  if (d.msg_type === 'image' && d.image_url) {
    bubbleContent = `<img src="${d.image_url}" class="msg-image" onclick="openLightbox('${d.image_url}')" />`;
  } else if (d.msg_type === 'sticker') {
    bubbleContent = `<span class="msg-sticker">${d.body}</span>`;
  } else if (d.msg_type === 'call') {
    bubbleContent = `<span class="msg-call-badge">${d.body.includes('video') ? '📹 Video call' : '📞 Audio call'}</span>`;
  } else {
    // Escape HTML to prevent XSS
    const escaped = d.body.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    bubbleContent = escaped;
  }

  // Sender name for groups
  const senderName = (isGroup && !d.is_mine)
    ? `<span class="msg-sender-name">${d.sender}</span>` : '';

  // Action buttons
  const deleteUrl = deleteUrlBase ? deleteUrlBase.replace('MSG_ID', d.id) : '';
  const deleteBtnHtml = (d.is_mine && deleteUrl)
    ? `<button class="msg-action-btn msg-del-btn" data-url="${deleteUrl}" onclick="deleteMsg(this,'${d.id}')">Delete</button>`
    : '';

  wrap.innerHTML = `
    ${avatarHtml}
    <div class="msg-content">
      ${senderName}
      ${replyHtml}
      <div class="msg-bubble">${bubbleContent}</div>
      <div class="msg-meta-row">
        <span class="msg-time">${d.created_at}</span>
        <button class="msg-action-btn" onclick="setReply('${d.id}','${d.sender}','${(d.body||'').replace(/'/g,"\\'").replace(/\n/g,' ')}')">Reply</button>
        ${deleteBtnHtml}
      </div>
    </div>`;

  // Insert before typing indicator
  const typing = document.getElementById('typingIndicator');
  if (typing) area.insertBefore(wrap, typing);
  else area.appendChild(wrap);

  area.scrollTop = area.scrollHeight;
}

// ═══════════════════════════════════════════════════════════════
//  MAIN initChat — called from room.html
// ═══════════════════════════════════════════════════════════════
function initChat({ chatId, myUser, myAvatar, sendUrl, csrf, isGroup }) {

  const form          = document.getElementById('msgForm');
  const msgInput      = document.getElementById('msgInput');
  const area          = document.getElementById('msgArea');
  const typingEl      = document.getElementById('typingIndicator');
  const typingLabel   = document.getElementById('typingLabel');

  if (!form || !msgInput || !area) {
    console.error('VIBE Chat: required DOM elements missing');
    return;
  }

  // Scroll to bottom on load
  area.scrollTop = area.scrollHeight;

  // Delete URL template — room.html must set window.DELETE_URL_BASE
  const deleteUrlBase = `/chats/${chatId}/msg/MSG_ID/delete/`;

  // ── WebSocket connection ───────────────────────────────────────
  const wsProto = location.protocol === 'https:' ? 'wss' : 'ws';
  const wsUrl   = `${wsProto}://${location.host}/ws/chat/${chatId}/`;
  let ws        = null;
  let wsReady   = false;

  function connectWS() {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      wsReady = true;
      console.log('VIBE Chat: WebSocket connected ✓');
      updateStatus('Online', true);
    };

    ws.onclose = (e) => {
      wsReady = false;
      console.warn('VIBE Chat: WebSocket closed, reconnecting in 3s…', e.code);
      updateStatus('Reconnecting…', false);
      setTimeout(connectWS, 3000);
    };

    ws.onerror = (e) => {
      console.error('VIBE Chat: WebSocket error', e);
    };

    ws.onmessage = (event) => {
      let data;
      try { data = JSON.parse(event.data); }
      catch { return; }

      switch (data.type) {
        case 'message':
          appendMessage(data, isGroup, deleteUrlBase);
          cancelReply();
          cancelImage();
          break;

        case 'typing':
          if (typingEl && typingLabel) {
            typingLabel.textContent = `${data.username} is typing…`;
            typingEl.style.display  = data.typing ? 'flex' : 'none';
            area.scrollTop = area.scrollHeight;
          }
          break;

        case 'status':
          updateStatus(data.online ? 'Online' : 'Active recently', data.online);
          break;

        case 'read':
          // Could show double-tick here
          break;

        case 'call_signal':
          handleCallSignal(data);
          break;
      }
    };
  }

  connectWS();

  function updateStatus(text, online) {
    const el = document.getElementById('roomStatus');
    if (!el) return;
    el.textContent = text;
    el.style.color = online ? '#4aff7a' : '';
  }

  // ── Typing indicator ───────────────────────────────────────────
  let typingTimer = null;

  msgInput.addEventListener('input', () => {
    if (!wsReady) return;
    ws.send(JSON.stringify({ type: 'typing', typing: true }));
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => {
      if (wsReady) ws.send(JSON.stringify({ type: 'typing', typing: false }));
    }, 1500);
  });

  // ── Stickers ───────────────────────────────────────────────────
  document.querySelectorAll('.sticker-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const sticker = btn.dataset.sticker;
      document.getElementById('stickerPicker').style.display = 'none';

      // Save to DB first
      const fd = new FormData();
      fd.append('body', sticker);
      fd.append('msg_type', 'sticker');
      if (replyId) fd.append('reply_to', replyId);

      try {
        const res  = await fetch(sendUrl, { method: 'POST', headers: { 'X-CSRFToken': csrf }, body: fd });
        const data = await res.json();
        if (data.id && wsReady) {
          ws.send(JSON.stringify({
            type:      'message',
            id:        data.id,
            body:      data.body,
            msg_type:  'sticker',
            sender:    myUser,
            sender_av: myAvatar,
            created_at: data.created_at,
            reply_to:  data.reply_to,
            image_url: null,
          }));
        }
      } catch (err) {
        console.error('Sticker send error:', err);
      }
    });
  });

  // ── Form submit (text + image) ─────────────────────────────────
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const body    = msgInput.value.trim();
    const hasImg  = !!pendingImageFile;

    if (!body && !hasImg) return;

    // Build FormData for the HTTP save
    const fd = new FormData();
    if (hasImg) {
      fd.append('image', pendingImageFile);
    } else {
      fd.append('body', body);
    }
    if (replyId) fd.append('reply_to', replyId);

    // Optimistically clear input immediately
    msgInput.value = '';
    if (wsReady) ws.send(JSON.stringify({ type: 'typing', typing: false }));
    clearTimeout(typingTimer);

    try {
      const res  = await fetch(sendUrl, { method: 'POST', headers: { 'X-CSRFToken': csrf }, body: fd });
      const data = await res.json();

      if (data.error) {
        console.error('Send error:', data.error);
        return;
      }

      if (data.id) {
        // Broadcast via WebSocket so other users see it in real-time
        if (wsReady) {
          ws.send(JSON.stringify({
            type:      'message',
            id:        data.id,
            body:      data.body,
            msg_type:  data.msg_type,
            sender:    myUser,
            sender_av: myAvatar,
            created_at: data.created_at,
            image_url: data.image_url,
            reply_to:  data.reply_to,
          }));
        } else {
          // WebSocket not ready — append locally so sender sees it
          appendMessage({
            ...data,
            is_mine: true,
            sender:  myUser,
            sender_av: myAvatar,
          }, isGroup, deleteUrlBase);
          cancelReply();
          cancelImage();
        }
      }
    } catch (err) {
      console.error('Message send error:', err);
    }
  });

  // Mark read when tab visible
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && wsReady) {
      ws.send(JSON.stringify({ type: 'read' }));
    }
  });
}


// ═══════════════════════════════════════════════════════════════
//  REAL WebRTC CALLS
//  Uses the call_signal WebSocket event to negotiate peer connection
// ═══════════════════════════════════════════════════════════════

// Shared state used by both call initiator and receiver
window._rtc = {
  pc:          null,   // RTCPeerConnection
  localStream: null,   // MediaStream from getUserMedia
  ws:          null,   // shared reference set by initCall
  myUser:      null,
  chatId:      null,
};

// ── initCall — called from call.html ──────────────────────────────
async function initCall({ chatId, callType, myUser, csrf, chatUrl, callId, isInitiator }) {

  window._rtc.myUser  = myUser;
  window._rtc.chatId  = chatId;

  const statusEl   = document.getElementById('callStatus');
  const timerEl    = document.getElementById('callTimer');
  const localVideo = document.getElementById('localVideo');
  const remoteVideo= document.getElementById('remoteVideo');

  let seconds = 0;
  let timerInterval = null;

  function setStatus(txt) {
    if (statusEl) statusEl.textContent = txt;
  }

  function startTimer() {
    if (timerEl) timerEl.style.display = 'block';
    timerInterval = setInterval(() => {
      seconds++;
      const m = String(Math.floor(seconds / 60)).padStart(2, '0');
      const s = String(seconds % 60).padStart(2, '0');
      if (timerEl) timerEl.textContent = `${m}:${s}`;
    }, 1000);
  }

  // ── Get local media ───────────────────────────────────────────
  try {
    const constraints = callType === 'video'
      ? { video: true, audio: true }
      : { audio: true, video: false };

    window._rtc.localStream = await navigator.mediaDevices.getUserMedia(constraints);

    if (localVideo && callType === 'video') {
      localVideo.srcObject = window._rtc.localStream;
    }
  } catch (err) {
    setStatus('Could not access camera/microphone');
    console.error('getUserMedia error:', err);
    return;
  }

  // ── WebSocket for signaling ───────────────────────────────────
  const wsProto = location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${wsProto}://${location.host}/ws/chat/${chatId}/`);
  window._rtc.ws = ws;

  // ── RTCPeerConnection ─────────────────────────────────────────
  const config = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' },
    ]
  };

  const pc = new RTCPeerConnection(config);
  window._rtc.pc = pc;

  // Add local tracks to peer connection
  window._rtc.localStream.getTracks().forEach(track => {
    pc.addTrack(track, window._rtc.localStream);
  });

  // When we get remote tracks, show them
  pc.ontrack = (event) => {
    if (remoteVideo && event.streams[0]) {
      remoteVideo.srcObject = event.streams[0];
      document.getElementById('remotePlaceholder')?.style.setProperty('display', 'none');
    }
    setStatus('Connected');
    startTimer();
  };

  // ICE candidate → send via WebSocket
  pc.onicecandidate = (event) => {
    if (event.candidate && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type:   'call_signal',
        signal: { type: 'candidate', candidate: event.candidate },
      }));
    }
  };

  pc.onconnectionstatechange = () => {
    const state = pc.connectionState;
    if (state === 'connected')    { setStatus('Connected'); startTimer(); }
    if (state === 'disconnected') { setStatus('Call ended'); }
    if (state === 'failed')       { setStatus('Connection failed'); }
  };

  // ── Handle incoming signals ───────────────────────────────────
  ws.onmessage = async (event) => {
    let data;
    try { data = JSON.parse(event.data); } catch { return; }

    if (data.type !== 'call_signal') return;
    const signal = data.signal;

    if (signal.type === 'offer') {
      await pc.setRemoteDescription(new RTCSessionDescription(signal));
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);
      ws.send(JSON.stringify({
        type:   'call_signal',
        signal: { type: 'answer', sdp: answer.sdp },
      }));
      setStatus('Connected');

    } else if (signal.type === 'answer') {
      await pc.setRemoteDescription(new RTCSessionDescription(signal));

    } else if (signal.type === 'candidate') {
      try { await pc.addIceCandidate(new RTCIceCandidate(signal.candidate)); }
      catch (err) { console.warn('ICE candidate error:', err); }

    } else if (signal.type === 'end') {
      endCallCleanup(chatUrl, callId, csrf);
    }
  };

  ws.onopen = async () => {
    // Initiator creates and sends offer
    if (isInitiator) {
      setStatus('Ringing…');
      try {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        ws.send(JSON.stringify({
          type:   'call_signal',
          signal: { type: 'offer', sdp: offer.sdp },
        }));
      } catch (err) {
        console.error('Offer creation error:', err);
        setStatus('Failed to start call');
      }
    } else {
      setStatus('Connecting…');
    }
  };

  ws.onerror = () => setStatus('Connection error');

  // ── UI controls ───────────────────────────────────────────────
  let micOn = true, camOn = true;

  document.getElementById('toggleMic')?.addEventListener('click', function () {
    micOn = !micOn;
    window._rtc.localStream?.getAudioTracks().forEach(t => t.enabled = micOn);
    this.classList.toggle('ctrl-off', !micOn);
    this.title = micOn ? 'Mute' : 'Unmute';
  });

  document.getElementById('toggleCam')?.addEventListener('click', function () {
    camOn = !camOn;
    window._rtc.localStream?.getVideoTracks().forEach(t => t.enabled = camOn);
    this.classList.toggle('ctrl-off', !camOn);
    this.title = camOn ? 'Turn off camera' : 'Turn on camera';
  });

  document.getElementById('endCallBtn')?.addEventListener('click', () => {
    // Signal other side
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type:   'call_signal',
        signal: { type: 'end' },
      }));
    }
    clearInterval(timerInterval);
    endCallCleanup(chatUrl, callId, csrf);
  });
}

async function endCallCleanup(chatUrl, callId, csrf) {
  // Stop all tracks
  window._rtc.localStream?.getTracks().forEach(t => t.stop());
  window._rtc.pc?.close();

  // Tell Django the call ended
  try {
    await fetch(`/chats/call/${callId}/end/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf, 'Content-Type': 'application/x-www-form-urlencoded' },
      body: 'status=answered',
    });
  } catch (err) { /* ignore */ }

  window.location.href = chatUrl;
}

// Global so call_signal handler in consumer can reach it
function handleCallSignal(data) {
  // Handled inside initCall's ws.onmessage
  // This stub exists so the chat consumer's receive won't crash
}