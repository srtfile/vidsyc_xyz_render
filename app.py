from flask import Flask, request, jsonify, render_template_string
import requests
from urllib.parse import quote_plus

app = Flask(__name__)

HEADERS_BASE = {
    "Accept": "*/*",
    "Origin": "https://vidsync.xyz",
    "Referer": "https://vidsync.xyz/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest"
}
API = "https://enc-dec.app/api"
SERVERS = ["cinevault", "cinedub", "cinebox", "cineflix", "cinevip", "cinecloud", "cine4k"]

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VidSync Resolver</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0f0f13; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; min-height: 100vh; padding: 2rem 1rem; }
  h1 { text-align: center; color: #a78bfa; margin-bottom: 2rem; font-size: 1.8rem; letter-spacing: 1px; }
  .card { background: #1a1a24; border: 1px solid #2d2d3d; border-radius: 10px; padding: 1.5rem; max-width: 700px; margin: 0 auto 2rem; }
  label { display: block; margin-bottom: 0.3rem; color: #9ca3af; font-size: 0.85rem; }
  input, select { width: 100%; padding: 0.55rem 0.8rem; background: #0f0f18; border: 1px solid #3d3d55; border-radius: 6px; color: #e0e0e0; font-size: 0.95rem; margin-bottom: 1rem; }
  input:focus, select:focus { outline: none; border-color: #7c3aed; }
  .row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  .type-toggle { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
  .type-btn { flex: 1; padding: 0.5rem; border: 1px solid #3d3d55; border-radius: 6px; background: #0f0f18; color: #9ca3af; cursor: pointer; transition: all 0.2s; }
  .type-btn.active { background: #7c3aed; border-color: #7c3aed; color: #fff; }
  .tv-fields { display: none; }
  .tv-fields.show { display: block; }
  button[type=submit] { width: 100%; padding: 0.7rem; background: #7c3aed; border: none; border-radius: 6px; color: #fff; font-size: 1rem; cursor: pointer; transition: background 0.2s; }
  button[type=submit]:hover { background: #6d28d9; }
  button[type=submit]:disabled { background: #4c1d95; cursor: not-allowed; }
  #result { max-width: 700px; margin: 0 auto; }
  .result-card { background: #1a1a24; border: 1px solid #2d2d3d; border-radius: 10px; padding: 1.2rem; margin-bottom: 1rem; }
  .result-card h3 { color: #a78bfa; margin-bottom: 0.8rem; font-size: 0.95rem; }
  pre { white-space: pre-wrap; word-break: break-all; font-size: 0.82rem; color: #d1d5db; line-height: 1.6; }
  .stream-link { display: block; color: #60a5fa; word-break: break-all; margin-bottom: 0.4rem; font-size: 0.85rem; }
  .error { color: #f87171; background: #1f0a0a; border-color: #7f1d1d; }
  .status { text-align: center; color: #9ca3af; padding: 1rem; }
  .spinner { display: inline-block; width: 18px; height: 18px; border: 2px solid #7c3aed; border-top-color: transparent; border-radius: 50%; animation: spin 0.7s linear infinite; vertical-align: middle; margin-right: 0.5rem; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .badge { display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; background: #1e1b4b; color: #a78bfa; margin-right: 0.3rem; margin-bottom: 0.3rem; }
</style>
</head>
<body>
<h1>⚡ VidSync Resolver</h1>
<div class="card">
  <div>
    <label>Media Type</label>
    <div class="type-toggle">
      <button class="type-btn active" onclick="setType('movie', this)">🎬 Movie</button>
      <button class="type-btn" onclick="setType('tv', this)">📺 TV Show</button>
    </div>
  </div>
  <label>Title</label>
  <input id="title" type="text" placeholder="e.g. Game of Thrones" value="Game of Thrones">
  <div class="row">
    <div>
      <label>TMDB ID</label>
      <input id="tmdb_id" type="text" placeholder="e.g. 1399" value="1399">
    </div>
    <div>
      <label>Release Year</label>
      <input id="year" type="text" placeholder="e.g. 2011" value="2011">
    </div>
  </div>
  <label>Server</label>
  <select id="server">
    {% for s in servers %}<option value="{{ s }}">{{ s }}</option>{% endfor %}
  </select>
  <div class="tv-fields" id="tv-fields">
    <div class="row">
      <div>
        <label>Season</label>
        <input id="season" type="number" placeholder="1" value="1" min="1">
      </div>
      <div>
        <label>Episode</label>
        <input id="episode" type="number" placeholder="1" value="1" min="1">
      </div>
    </div>
  </div>
  <button type="submit" id="btn" onclick="resolve()">Resolve Stream</button>
</div>
<div id="result"></div>

<script>
let mediaType = 'movie';
function setType(t, el) {
  mediaType = t;
  document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('tv-fields').classList.toggle('show', t === 'tv');
}
async function resolve() {
  const btn = document.getElementById('btn');
  const res = document.getElementById('result');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Resolving...';
  res.innerHTML = '<div class="status"><span class="spinner"></span>Fetching stream data...</div>';
  const payload = {
    title: document.getElementById('title').value.trim(),
    tmdb_id: document.getElementById('tmdb_id').value.trim(),
    year: document.getElementById('year').value.trim(),
    server: document.getElementById('server').value,
    type: mediaType,
    season: document.getElementById('season')?.value || '1',
    episode: document.getElementById('episode')?.value || '1'
  };
  try {
    const r = await fetch('/resolve', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
    const data = await r.json();
    if (data.error) {
      res.innerHTML = `<div class="result-card error"><h3>❌ Error</h3><pre>${data.error}</pre></div>`;
    } else {
      let html = `<div class="result-card"><h3>✅ Result for <strong>${payload.title}</strong></h3>`;
      // Try to extract URLs
      const text = typeof data.result === 'string' ? data.result : JSON.stringify(data.result, null, 2);
      const urls = [...text.matchAll(/https?:\/\/[^\s"'<>]+/g)].map(m => m[0]);
      if (urls.length) {
        html += '<div style="margin-bottom:0.8rem;">';
        urls.forEach(u => { html += `<a class="stream-link" href="${u}" target="_blank">▶ ${u}</a>`; });
        html += '</div>';
      }
      html += `<pre>${escHtml(text)}</pre></div>`;
      res.innerHTML = html;
    }
  } catch(e) {
    res.innerHTML = `<div class="result-card error"><h3>❌ Network Error</h3><pre>${e.message}</pre></div>`;
  }
  btn.disabled = false;
  btn.innerHTML = 'Resolve Stream';
}
function escHtml(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
</script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(HTML, servers=SERVERS)

@app.route("/resolve", methods=["POST"])
def resolve():
    body = request.get_json()
    title = body.get("title", "")
    tmdb_id = body.get("tmdb_id", "")
    year = body.get("year", "")
    server = body.get("server", "cinevault")
    media_type = body.get("type", "movie")
    season = body.get("season", "1")
    episode = body.get("episode", "1")

    try:
        # Get turnstile token
        enc_vidsync = f"{API}/enc-vidsync"
        token_resp = requests.get(enc_vidsync, timeout=15).json()
        if token_resp.get("status") != 200:
            return jsonify({"error": f"Token fetch failed: {token_resp.get('error', 'unknown')}"}), 500
        token = token_resp["result"]["token"]

        headers = {**HEADERS_BASE, "X-Cf-Turnstile": token}

        # Build fetch URL
        enc_title = quote_plus(title)
        if media_type == "tv":
            fetch_url = (f"https://vidsync.xyz/api/stream/fetch?title={enc_title}&type=tv"
                         f"&releaseYear={year}&mediaId={tmdb_id}&serverName={server}"
                         f"&season={season}&episode={episode}")
        else:
            fetch_url = (f"https://vidsync.xyz/api/stream/fetch?title={enc_title}&type=movie"
                         f"&releaseYear={year}&mediaId={tmdb_id}&serverName={server}")

        enc_text = requests.get(fetch_url, headers=headers, timeout=15).text

        # Decrypt
        dec_resp = requests.post(f"{API}/dec-vidsync",
                                 json={"text": enc_text, "id": tmdb_id},
                                 timeout=15).json()
        if dec_resp.get("status") != 200:
            return jsonify({"error": f"Decrypt failed: {dec_resp.get('error', 'unknown')}"}), 500

        return jsonify({"result": dec_resp["result"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=False)