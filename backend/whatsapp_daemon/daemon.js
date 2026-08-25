/**
 * Native 24/7 WhatsApp Web Daemon for Jarvis powered by Baileys.
 * 
 * Implements the WAHA REST API specification:
 * - Serves pairing Dashboard & QR code on http://localhost:3000/dashboard
 * - Endpoints:
 *     GET  /api/sessions/default
 *     POST /api/sessions/default/start
 *     POST /api/sendText
 *     POST /api/sendImage
 * - Forwards incoming WhatsApp messages to Jarvis webhook:
 *     POST http://127.0.0.1:8000/api/v1/webhooks/whatsapp
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const QRCode = require('qrcode');
const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion
} = require('@whiskeysockets/baileys');
const pino = require('pino');

const app = express();
app.use(cors());
app.use(express.json({ limit: '50mb' }));

const PORT = process.env.PORT || 3005;
const WEBHOOK_URL = process.env.WHATSAPP_HOOK_URL || 'http://127.0.0.1:8000/api/v1/webhooks/whatsapp';
const AUTH_DIR = path.resolve(__dirname, '..', 'data', 'waha_auth');

if (!fs.existsSync(AUTH_DIR)) {
  fs.mkdirSync(AUTH_DIR, { recursive: true });
}

let sock = null;
let currentQR = null;
let currentQRDataUrl = null;
let connectionState = 'DISCONNECTED';
let userMe = null;

async function startWhatsAppSocket() {
  connectionState = 'STARTING';
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
  const { version } = await fetchLatestBaileysVersion();

  sock = makeWASocket({
    version,
    auth: state,
    logger: pino({ level: 'silent' }),
    printQRInTerminal: true,
    browser: ['Jarvis OS', 'Chrome', '120.0.0']
  });

  sock.ev.on('creds.update', saveCreds);

  sock.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      currentQR = qr;
      connectionState = 'SCAN_QR_CODE';
      try {
        currentQRDataUrl = await QRCode.toDataURL(qr);
      } catch (err) {
        console.error('Failed to generate QR data URL:', err);
      }
      console.log('\n[WhatsApp Daemon] Scan the QR code in terminal or open http://localhost:3000/dashboard\n');
    }

    if (connection === 'close') {
      const shouldReconnect = (lastDisconnect?.error)?.output?.statusCode !== DisconnectReason.loggedOut;
      connectionState = 'DISCONNECTED';
      currentQR = null;
      currentQRDataUrl = null;
      console.log('[WhatsApp Daemon] Connection closed. Reconnecting:', shouldReconnect);
      if (shouldReconnect) {
        setTimeout(startWhatsAppSocket, 3000);
      }
    } else if (connection === 'open') {
      connectionState = 'WORKING';
      currentQR = null;
      currentQRDataUrl = null;
      userMe = sock.user;
      console.log('[WhatsApp Daemon] Connected successfully as:', sock.user?.id || 'Connected');
    }
  });

  // Handle incoming messages
  sock.ev.on('messages.upsert', async (m) => {
    try {
      if (m.type !== 'notify') return;

      for (const msg of m.messages) {
        if (!msg.message) continue;

        const isFromMe = msg.key.fromMe || false;
        const sender = msg.key.remoteJid;
        const text = msg.message.conversation ||
                     msg.message.extendedTextMessage?.text ||
                     msg.message.imageMessage?.caption ||
                     '';

        if (!text) continue;

        // Dispatch to Jarvis Webhook
        fetch(WEBHOOK_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            event: 'message',
            session: 'default',
            payload: {
              id: msg.key.id,
              from: sender,
              body: text,
              fromMe: isFromMe,
              pushName: msg.pushName || 'Client'
            }
          })
        }).catch(err => {
          console.warn('[WhatsApp Daemon] Webhook dispatch error:', err.message);
        });
      }
    } catch (err) {
      console.error('[WhatsApp Daemon] Error processing message:', err);
    }
  });
}

// REST API Endpoints

// 1. Session Status
app.get('/api/sessions/default', (req, res) => {
  res.json({
    name: 'default',
    status: connectionState,
    qr: currentQRDataUrl || currentQR,
    me: userMe
  });
});

app.get('/api/sessions', (req, res) => {
  res.json([{
    name: 'default',
    status: connectionState,
    qr: currentQRDataUrl || currentQR,
    me: userMe
  }]);
});

// 2. Start Session
app.post('/api/sessions/default/start', async (req, res) => {
  if (!sock || connectionState === 'DISCONNECTED') {
    await startWhatsAppSocket();
  }
  res.json({
    name: 'default',
    status: connectionState,
    qr: currentQRDataUrl || currentQR
  });
});

// 3. Send Text Message
app.post('/api/sendText', async (req, res) => {
  const { chatId, text } = req.body;
  if (!sock || connectionState !== 'WORKING') {
    return res.status(503).json({ error: 'WhatsApp session is not connected' });
  }

  try {
    const rawNumber = chatId.replace('@c.us', '').replace('@s.whatsapp.net', '').replace(/[^0-9]/g, '');
    const jid = `${rawNumber}@s.whatsapp.net`;
    const result = await sock.sendMessage(jid, { text });
    console.log(`[WhatsApp Daemon] Outgoing text message sent to ${jid}: ${text.slice(0, 60)}...`);
    res.json({ status: 'success', id: result.key.id });
  } catch (err) {
    console.error('[WhatsApp Daemon] Failed to send text message:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// 4. Send Image
app.post('/api/sendImage', async (req, res) => {
  const { chatId, file, caption } = req.body;
  if (!sock || connectionState !== 'WORKING') {
    return res.status(503).json({ error: 'WhatsApp session is not connected' });
  }

  try {
    const rawNumber = chatId.replace('@c.us', '').replace('@s.whatsapp.net', '').replace(/[^0-9]/g, '');
    const jid = `${rawNumber}@s.whatsapp.net`;
    const url = file?.url || file;
    const result = await sock.sendMessage(jid, {
      image: { url },
      caption: caption || ''
    });
    console.log(`[WhatsApp Daemon] Outgoing image message sent to ${jid}`);
    res.json({ status: 'success', id: result.key.id });
  } catch (err) {
    console.error('[WhatsApp Daemon] Failed to send image message:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// 5. Visual Dashboard & Pairing UI
app.get('/dashboard', (req, res) => {
  const qrHtml = currentQRDataUrl
    ? '<div class="qr-box"><img id="qr-img" src="' + currentQRDataUrl + '" alt="WhatsApp QR Code"></div>'
    : '<div id="qr-loading" style="padding: 40px; color: #94a3b8;">Initializing QR code...</div>';

  res.send(`
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Jarvis WhatsApp 24/7 Gateway</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b0f19; color: #fff; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }
    .card { background: #151d2f; border: 1px solid rgba(255,255,255,0.1); padding: 40px; border-radius: 24px; text-align: center; max-width: 440px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }
    h1 { font-size: 24px; margin-bottom: 8px; font-weight: 600; }
    p { color: #94a3b8; font-size: 14px; line-height: 1.5; margin-bottom: 24px; }
    .badge { display: inline-block; padding: 6px 14px; border-radius: 9999px; font-size: 12px; font-family: monospace; text-transform: uppercase; margin-bottom: 20px; }
    .badge-working { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }
    .badge-scan { background: rgba(234, 179, 8, 0.15); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.3); }
    .badge-off { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .qr-box { background: white; padding: 16px; border-radius: 16px; display: inline-block; margin-bottom: 24px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
    .qr-box img { display: block; width: 240px; height: 240px; }
    .footer-note { font-size: 12px; color: #64748b; }
  </style>
  <script>
    setInterval(() => {
      fetch('/api/sessions/default')
        .then(r => r.json())
        .then(data => {
          if (data.status === 'WORKING') {
            document.getElementById('status-badge').className = 'badge badge-working';
            document.getElementById('status-badge').innerText = 'Connected: ' + (data.me?.id || 'Online');
            document.getElementById('qr-container').innerHTML = '<div style="color: #4ade80; padding: 40px 0; font-size: 16px; font-weight: bold;">WhatsApp Connected & Listening 24/7</div>';
          } else if (data.status === 'SCAN_QR_CODE' && data.qr) {
            document.getElementById('status-badge').className = 'badge badge-scan';
            document.getElementById('status-badge').innerText = 'Scan QR to Pair';
            const img = document.getElementById('qr-img');
            if (img) {
              img.src = data.qr;
            } else {
              document.getElementById('qr-container').innerHTML = '<div class="qr-box"><img id="qr-img" src="' + data.qr + '" alt="WhatsApp QR Code"></div>';
            }
          }
        });
    }, 1500);
  </script>
</head>
<body>
  <div class="card">
    <div id="status-badge" class="badge ${connectionState === 'WORKING' ? 'badge-working' : (connectionState === 'SCAN_QR_CODE' ? 'badge-scan' : 'badge-off')}">
      ${connectionState === 'WORKING' ? 'Connected' : (connectionState === 'SCAN_QR_CODE' ? 'Scan QR to Pair' : 'Starting Session...')}
    </div>
    <h1>Jarvis WhatsApp Gateway</h1>
    <p>Scan the QR code with WhatsApp on your phone (<strong>Settings &rarr; Linked Devices &rarr; Link a Device</strong>) to activate 24/7 AI auto-replying.</p>

    <div id="qr-container">
      ${qrHtml}
    </div>

    <div class="footer-note">Webhook Destination: <code>${WEBHOOK_URL}</code></div>
  </div>
</body>
</html>
  `);
});

app.listen(PORT, () => {
  console.log(`[WhatsApp Daemon] Server running on http://localhost:${PORT}`);
  console.log(`[WhatsApp Daemon] Dashboard & Pairing URL: http://localhost:${PORT}/dashboard`);
  startWhatsAppSocket();
});
