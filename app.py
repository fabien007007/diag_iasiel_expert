#!/usr/bin/env python3

import os
import re
import base64
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

NOM_PROJET = "DIAG ELEC IASIEL"

app = FastAPI(title=NOM_PROJET, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/manifest.json")
async def get_manifest():
    return FileResponse("manifest.json")

@app.get("/sw.js")
async def get_sw():
    return FileResponse("sw.js", media_type="application/javascript")


async def search_perplexity(query: str) -> str:
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        return ""

    url = "https://api.perplexity.ai/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Tu es un expert technique électricien certifié avec 20+ ans d'expérience. "
                    "Diagnostic précis et factuel UNIQUEMENT sur base de normes officielles et données avérées. "
                    "ZÉRO improvisation, ZÉRO créativité. "
                    "Domaines : appareillage électrique, motorisation, domotique, tableaux électriques, câblage, variateurs, éclairage, automatismes. "
                    "Tous fabricants maîtrisés : Legrand, Griesser, Came, BTF, Hager, Yoki, Schneider Electric, Siemens, ABB, Merlin Gerin. "
                    "Respect strict : NF C 15-100, IEC 60364, réglementations sécurité électrique, efficacité énergétique EU. "
                    "Structure réponse OBLIGATOIRE en Markdown avec ## : identification produit, analyse technique, solutions étape par étape, compatibilité marques, normes sécurité. "
                    "Sources : documentation constructeurs, normes NF/IEC officielles, retour terrain vérifiable. "
                    "Pas de vague, pas d'approximation, pas de 'peut-être'."
                ),
            },
            {"role": "user", "content": query},
        ],
    }

    try:
        res = requests.post(url, json=data, headers=headers, timeout=25.0)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        return f"Erreur Perplexity: {res.status_code}"
    except Exception:
        return "Recherche web indisponible."


def format_html_output(text: str, web_info: str = "") -> str:
    clean = text.replace("**", "").replace("###", "##")
    sections = re.split(r"##", clean)
    html_res = ""

    for s in sections:
        c = s.strip()
        if not c:
            continue
        lines = c.split("\n")
        title = lines[0].strip()
        body = "<br>".join(lines[1:]).strip()

        css = "diag-section"
        icon = "⚙️"
        if "Identification" in title:
            icon, css = "🆔", "diag-section s-id"
        elif "Analyse" in title:
            icon, css = "🔍", "diag-section s-analyse"
        elif "Correction" in title or "Solution" in title:
            icon, css = "🛠️", "diag-section s-fix"
        elif "Compatibilité" in title:
            icon, css = "📦", "diag-section s-fix"
        elif "Sécurité" in title or "Norme" in title:
            icon, css = "⚡", "diag-section s-secu"

        html_res += (
            f"<div class='{css}'>"
            f"<div class='section-header'>{icon} {title}</div>"
            f"<div class='section-body'>{body}</div>"
            f"</div>"
        )

    if web_info:
        web_body = web_info.replace("**", "<b>").replace("\n", "<br>")
        html_res += (
            "<div class='diag-section s-web'>"
            "<div class='section-header'>🌐 SOLUTIONS WEB TEMPS RÉEL</div>"
            f"<div class='section-body'>{web_body}</div>"
            "</div>"
        )

    return html_res


async def analyze_with_groq(description: str, images_b64: list) -> str:
    from groq import Groq

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "## ⚠️ Erreur\nGROQ_API_KEY manquante dans .env"

    client = Groq(api_key=api_key)

    prompt_systeme = (
        "Tu es un expert électricien expert certifié avec 20+ ans d'expérience. "
        "Diagnostic précis et factuel UNIQUEMENT sur base de normes officielles et données avérées. "
        "ZÉRO improvisation, ZÉRO créativité. "
        "Domaines : appareillage électrique, motorisation, domotique, tableaux électriques, câblage, variateurs, éclairage, automatismes. "
        "Tous fabricants : Legrand, Griesser, Came, BTF, Hager, Yoki, Schneider Electric, Siemens, ABB, Merlin Gerin. "
        "Respect strict : NF C 15-100, IEC 60364, réglementations sécurité, efficacité énergétique. "
        "STRUCTURE OBLIGATOIRE (Markdown avec ##):\n"
        "## 🆔 Identification précise\n"
        "## 🔍 Analyse visuelle et technique\n"
        "## 🛠️ Correction étape par étape\n"
        "## 📦 Compatibilité produits / marques\n"
        "## ⚡ Sécurité / Normes\n"
        "Sources : documentation constructeurs, normes NF/IEC officielles. "
        "Pas de vague, pas d'approximation, pas de 'peut-être'."
    )

    messages = [{"role": "system", "content": prompt_systeme}]

    user_content = [{"type": "text", "text": f"PROBLÈME DÉCRIT : {description}"}]
    for img_b64 in images_b64:
        user_content.append(
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
        )

    messages.append({"role": "user", "content": user_content})

    response = client.chat.completions.create(
        messages=messages,
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.2,
        max_tokens=1800,
    )
    return response.choices[0].message.content


@app.post("/diagnostic")
async def diagnostic(panne_description: str = Form(""), images: list = File(None)):
    images_b64 = []
    
    if images:
        for img in images:
            try:
                images_b64.append(base64.b64encode(await img.read()).decode("utf-8"))
            except:
                pass

    analysis = await analyze_with_groq(panne_description, images_b64)

    web_info = ""
    if panne_description:
        web_info = await search_perplexity(f"Solution technique électrique pour: {panne_description}")

    return HTMLResponse(content=format_html_output(analysis, web_info))


@app.get("/", response_class=HTMLResponse)
def home():
    return """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DIAG ELEC IASIEL</title>
  <style>
    body { font-family: Segoe UI, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 15px; }
    .card { background: #1e293b; max-width: 700px; margin: auto; padding: 20px; border-radius: 20px; border: 1px solid #334155; }
    h1 { color: #38bdf8; text-align: center; font-size: 1.2rem; text-transform: uppercase; margin-bottom: 15px; }
    .btn { padding: 16px; border-radius: 12px; border: none; font-weight: bold; cursor: pointer; margin-top: 12px; }
    .btn-main { width: 100%; background: linear-gradient(135deg, #38bdf8 0%, #2563eb 100%); color: white; }
    .btn-row { display: flex; gap: 12px; margin-top: 12px; }
    .btn-row .btn { flex: 1; margin-top: 0; }
    .btn-micro { background: #ec4899; color: white; }
    .btn-qr { background: #10b981; color: white; }
    .btn-photo { width: 100%; background: #334155; color: white; border: 1px dashed #64748b; margin-top: 12px; }
    .photo-gallery { display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
    .photo-item { position: relative; width: 80px; height: 80px; border-radius: 8px; border: 2px solid #38bdf8; overflow: hidden; }
    .photo-item img { width: 100%; height: 100%; object-fit: cover; }
    .photo-item .remove { position: absolute; top: 2px; right: 2px; background: #ef4444; color: white; border: none; border-radius: 50%; width: 20px; height: 20px; cursor: pointer; font-size: 12px; }
    textarea { width: 100%; height: 110px; background: #0f172a; border: 1px solid #334155; border-radius: 12px; color: white; padding: 12px; box-sizing: border-box; resize: none; font-size: 1rem; margin-top: 12px; }
    #loading { display: none; text-align: center; color: #38bdf8; font-weight: bold; padding: 20px; }
    .diag-section { background: #334155; border-radius: 12px; margin-top: 15px; border-left: 4px solid #94a3b8; overflow: hidden; }
    .s-id { border-left-color: #38bdf8; } .s-analyse { border-left-color: #fbbf24; }
    .s-fix { border-left-color: #22c55e; } .s-secu { border-left-color: #ef4444; }
    .s-web { border-left-color: #f472b6; background: #2c2e3e; }
    .section-header { padding: 12px 15px; font-weight: bold; background: rgba(0,0,0,0.2); }
    .section-body { padding: 15px; line-height: 1.6; font-size: 0.95rem; }
    #qr-scanner { display: none; width: 100%; height: 300px; border-radius: 12px; margin: 12px 0; border: 2px solid #38bdf8; background: #0f172a; }
  </style>
</head>
<body>
<div class="card">
  <h1>DIAG ELEC IASIEL</h1>
  <button class="btn btn-photo" onclick="document.getElementById('photo-input').click()">📷 AJOUTER PHOTOS</button>
  <input type="file" id="photo-input" accept="image/*" capture="environment" multiple hidden onchange="handleMultiplePhotos(this)">
  <div class="photo-gallery" id="photo-gallery"></div>
  
  <div class="btn-row">
    <button class="btn btn-micro" onclick="startMicro()">🔤 MICRO</button>
    <button class="btn btn-qr" onclick="toggleQRScanner()">📱 QR CODE</button>
  </div>
  
  <div id="qr-scanner"></div>
  
  <textarea id="desc" placeholder="Décrivez le problème technique..."></textarea>
  <button id="go" class="btn btn-main" onclick="run()">⚡ LANCER LE DIAGNOSTIC</button>
  <div id="loading">📡 Analyse Groq + Recherche Web...</div>
  <div id="result"></div>
</div>

<script src="https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js"></script>
<script>
  let photos = [];
  let recognition = null;
  let isListening = false;
  let qrActive = false;
  let qrStream = null;

  function handleMultiplePhotos(input) {
    const files = Array.from(input.files || []);
    files.forEach(file => {
      const r = new FileReader();
      r.onload = (e) => {
        const photoId = Date.now() + Math.random();
        photos.push({ id: photoId, data: e.target.result });
        renderPhotos();
      };
      r.readAsDataURL(file);
    });
  }

  function renderPhotos() {
    const gallery = document.getElementById('photo-gallery');
    gallery.innerHTML = '';
    photos.forEach(photo => {
      const div = document.createElement('div');
      div.className = 'photo-item';
      div.innerHTML = `<img src="${photo.data}"><button class="remove" onclick="removePhoto(${photo.id})">✕</button>`;
      gallery.appendChild(div);
    });
  }

  function removePhoto(photoId) {
    photos = photos.filter(p => p.id !== photoId);
    renderPhotos();
  }

  function startMicro() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Reconnaissance vocale non supportée');
      return;
    }
    
    if (!recognition) {
      recognition = new SpeechRecognition();
      recognition.lang = 'fr-FR';
      recognition.onstart = () => { isListening = true; };
      recognition.onend = () => { isListening = false; };
      recognition.onresult = (e) => {
        let transcript = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
          transcript += e.results[i][0].transcript;
        }
        document.getElementById('desc').value += (document.getElementById('desc').value ? ' ' : '') + transcript;
      };
      recognition.onerror = () => { alert('Erreur reconnaissance vocale'); };
    }
    
    if (isListening) {
      recognition.stop();
    } else {
      recognition.start();
    }
  }

  function toggleQRScanner() {
    const scanner = document.getElementById('qr-scanner');
    if (qrActive) {
      if (qrStream) {
        qrStream.getTracks().forEach(track => track.stop());
      }
      scanner.style.display = 'none';
      qrActive = false;
    } else {
      scanner.style.display = 'block';
      qrActive = true;
      startQRScanner();
    }
  }

  function startQRScanner() {
    const scanner = document.getElementById('qr-scanner');
    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } }).then(stream => {
      qrStream = stream;
      const video = document.createElement('video');
      video.srcObject = stream;
      video.style.width = '100%';
      video.style.height = '100%';
      video.style.borderRadius = '12px';
      video.play();
      scanner.innerHTML = '';
      scanner.appendChild(video);

      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      function scanQR() {
        if (video.readyState === video.HAVE_ENOUGH_DATA) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          ctx.drawImage(video, 0, 0);
          const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          const code = jsQR(imageData.data, imageData.width, imageData.height);
          if (code) {
            document.getElementById('desc').value += (document.getElementById('desc').value ? ' ' : '') + 'QR: ' + code.data;
            toggleQRScanner();
            return;
          }
        }
        requestAnimationFrame(scanQR);
      }
      scanQR();
    }).catch(err => {
      alert('Accès caméra refusé: ' + err.message);
      qrActive = false;
      scanner.style.display = 'none';
    });
  }

  async function run() {
    const res = document.getElementById('result');
    const load = document.getElementById('loading');
    const go = document.getElementById('go');
    go.style.display = 'none';
    load.style.display = 'block';
    res.innerHTML = "";
    
    const fd = new FormData();
    photos.forEach(photo => {
      const arr = photo.data.split(',');
      const mime = arr[0].match(/:(.*?);/)[1];
      const bstr = atob(arr[1]);
      const n = bstr.length;
      const u8arr = new Uint8Array(n);
      for(let i=0; i<n; i++) u8arr[i] = bstr.charCodeAt(i);
      const blob = new Blob([u8arr], { type: mime });
      fd.append('images', blob, 'photo.jpg');
    });
    fd.append('panne_description', document.getElementById('desc').value);
    
    try {
      const r = await fetch('/diagnostic', { method: 'POST', body: fd });
      const html = await r.text();
      res.innerHTML = html;
    } catch (e) {
      res.innerHTML = '<div class="diag-section s-secu"><div class="section-header">❌ Erreur serveur</div><div class="section-body">' + e.message + '</div></div>';
    } finally {
      load.style.display = 'none';
      go.style.display = 'block';
    }
  }
</script>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("PORT", "8000")), workers=1)


