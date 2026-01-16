#!/usr/bin/env python3
"""
GRIESSER EXPERT AI - Application FastAPI
Motorisation | Automatisation KNX/DALI | Appareillage
Basé sur architecture Somfy - Adapté pour Griesser
"""

import os
import re
import base64
import httpx
from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
try:
    import griesser_database as db
    BASE_TECHNIQUE = str(db.GRIESSER_PRODUCTS)
    NOM_PROJET = "Griesser Expert AI"
except Exception as e:
    BASE_TECHNIQUE = "{}"
    NOM_PROJET = "Griesser Diagnostic Pro"

app = FastAPI(title=NOM_PROJET, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTES PWA ---
@app.get("/manifest.json")
async def get_manifest():
    return FileResponse("manifest.json")

@app.get("/sw.js")
async def get_sw():
    return FileResponse("sw.js", media_type="application/javascript")

# --- MOTEUR DE RECHERCHE WEB (Perplexity) ---
async def search_perplexity(query: str) -> str:
    """Recherche web temps réel via Perplexity"""
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        return "❌ Perplexity non configuré"
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": "Expert technique Griesser certifié. Fournis solutions précises, schémas de câblage, codes erreurs, normes NF C 15-100. Sois concis et utilise le gras pour l'important."
            },
            {
                "role": "user",
                "content": query
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=data, headers=headers, timeout=25.0)
            return res.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"⚠️ Recherche web indisponible: {str(e)}"

# --- FORMATAGE HTML ---
def format_html_output(text: str, web_info: str = "") -> str:
    """Formate réponse en sections HTML stylisées"""
    clean = text.replace("**", "").replace("###", "##")
    sections = re.split(r'##', clean)
    html_res = ""
    
    for s in sections:
        c = s.strip()
        if not c:
            continue
        
        lines = c.split('\n')
        title = lines[0].strip()
        body = "<br>".join(lines[1:]).strip()
        
        # Détection type section
        css = "diag-section"
        icon = "⚙️"
        
        if "Identification" in title:
            icon, css = "🆔", "diag-section s-id"
        elif "Analyse" in title or "visuelle" in title.lower():
            icon, css = "🔍", "diag-section s-analyse"
        elif "Correction" in title or "Solution" in title:
            icon, css = "🛠️", "diag-section s-fix"
        elif "Base" in title or "Enrichissement" in title:
            icon, css = "💾", "diag-section s-data"
        elif "Norme" in title or "Sécurité" in title:
            icon, css = "🔐", "diag-section s-secu"
        
        html_res += f"""<div class='{css}'>
            <div class='section-header'>{icon} {title}</div>
            <div class='section-body'>{body}</div>
        </div>"""
    
    # Ajouter recherche web
    if web_info:
        web_body = web_info.replace("**", "<b>").replace("\n", "<br>")
        html_res += f"""<div class='diag-section s-web'>
            <div class='section-header'>🌐 SOLUTIONS WEB TEMPS RÉEL</div>
            <div class='section-body'>{web_body}</div>
        </div>"""
    
    return html_res

# --- DIAGNOSTIC PRINCIPAL (Groq Llama 4 Scout) ---
@app.post("/diagnostic")
async def diagnostic(image: UploadFile = File(None), panne_description: str = Form("")):
    """Endpoint diagnostic complet Griesser"""
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    prompt_systeme = f"""Tu es l'Expert Technique Griesser Ultime.
Tu as accès à cette BASE DE DONNÉES PRIVÉE : {BASE_TECHNIQUE}

TA MISSION :
1. Si une image est fournie : ANALYSE-LA visuellement avec extrême précision
   - Identifie produit Griesser (motorisation, KNX, DALI, appareillage)
   - Examine borniers, câblage, état LEDs, références produit
   - Détecte défauts visuels (corrosion, dégâts, usure, connecteurs)
   
2. Compare à la BASE DE DONNÉES fournie
3. Ne sois jamais générique. Sois précis et technique.
4. Utilise les normes NF C 15-100, EN 60335, EN 50090

STRUCTURE OBLIGATOIRE (utilise ##) :
## 🆔 Identification Produit Précise
## 🔍 Analyse Visuelle et Technique
## 🛠️ Correction Étape par Étape
## 💾 Enrichissement Base de Données & Documentation"""

    messages = [{"role": "system", "content": prompt_systeme}]
    user_content = [
        {
            "type": "text",
            "text": f"PROBLÈME DÉCRIT : {panne_description if panne_description else 'Pas de description fournie'}"
        }
    ]
    
    # Ajouter image si présente
    if image and image.filename:
        try:
            img_b64 = base64.b64encode(await image.read()).decode('utf-8')
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
            })
        except Exception as e:
            pass
    
    messages.append({"role": "user", "content": user_content})

    # Appel Groq avec Llama 4 Scout
    try:
        response = client.chat.completions.create(
            messages=messages,
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.1,
            max_tokens=2000
        )
        analysis = response.choices[0].message.content
    except Exception as e:
        analysis = f"## ⚠️ Erreur Llama 4 Scout ## Problème analyse: {str(e)}"

    # Recherche web Perplexity pour contexte
    web_query = f"Solution technique Griesser précise pour : {panne_description[:100]}. Normes NF C 15-100, EN 60335."
    web_info = await search_perplexity(web_query)
    
    return HTMLResponse(content=format_html_output(analysis, web_info))

# --- INTERFACE FRONTALE ---
@app.get("/", response_class=HTMLResponse)
def home():
    """Page d'accueil PWA"""
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#1a5490">
    <meta name="description" content="Expert technique Griesser - Motorisation, KNX/DALI, Appareillage">
    <script src="https://unpkg.com/html5-qrcode"></script>
    <title>{NOM_PROJET}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #e2e8f0;
            min-height: 100vh;
            padding: 15px;
        }}
        
        .container {{
            max-width: 700px;
            margin: 0 auto;
        }}
        
        .card {{
            background: #1e293b;
            border-radius: 20px;
            border: 1px solid #334155;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
            padding: 25px;
            margin-bottom: 20px;
        }}
        
        h1 {{
            color: #38bdf8;
            text-align: center;
            font-size: 1.4rem;
            text-transform: uppercase;
            margin-bottom: 10px;
            letter-spacing: 1px;
        }}
        
        .subtitle {{
            text-align: center;
            color: #94a3b8;
            font-size: 0.85rem;
            margin-bottom: 25px;
        }}
        
        /* BOUTONS */
        .btn {{
            width: 100%;
            padding: 16px;
            border-radius: 12px;
            border: none;
            font-weight: 600;
            cursor: pointer;
            margin-top: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            font-size: 1rem;
            transition: all 0.3s ease;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
        }}
        
        .btn-main {{
            background: linear-gradient(135deg, #1a5490 0%, #0f3a60 100%);
            color: white;
        }}
        
        .btn-main:active {{
            transform: translateY(0);
        }}
        
        .btn-scan {{
            background: #475569;
            color: white;
        }}
        
        .btn-photo {{
            background: #334155;
            color: white;
            border: 2px dashed #64748b;
        }}
        
        .btn-share {{
            background: #10b981;
            color: white;
            display: none;
        }}
        
        .btn-reset {{
            background: #ef4444;
            color: white;
            display: none;
        }}
        
        /* INPUT */
        .input-box {{
            position: relative;
            margin-top: 20px;
        }}
        
        textarea {{
            width: 100%;
            height: 120px;
            background: #0f172a;
            border: 2px solid #334155;
            border-radius: 12px;
            color: #e2e8f0;
            padding: 12px;
            font-family: inherit;
            font-size: 1rem;
            resize: vertical;
            transition: border-color 0.3s;
        }}
        
        textarea:focus {{
            outline: none;
            border-color: #1a5490;
        }}
        
        .mic {{
            position: absolute;
            right: 10px;
            bottom: 10px;
            background: #1e293b;
            border: 2px solid #334155;
            color: #38bdf8;
            border-radius: 50%;
            width: 44px;
            height: 44px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            transition: all 0.3s;
        }}
        
        .mic:hover {{
            border-color: #38bdf8;
        }}
        
        .mic-on {{
            background: #ef4444;
            color: white;
            border-color: #ef4444;
            animation: pulse 1.5s infinite;
        }}
        
        /* SECTIONS RÉSULTATS */
        .diag-section {{
            background: #334155;
            border-radius: 12px;
            margin-top: 15px;
            border-left: 5px solid #94a3b8;
            overflow: hidden;
            transition: all 0.3s;
        }}
        
        .diag-section:hover {{
            border-left-color: #38bdf8;
        }}
        
        .s-id {{ border-left-color: #38bdf8; }}
        .s-analyse {{ border-left-color: #fbbf24; }}
        .s-fix {{ border-left-color: #22c55e; }}
        .s-data {{ border-left-color: #8b5cf6; }}
        .s-secu {{ border-left-color: #ef4444; }}
        .s-web {{ border-left-color: #f472b6; background: #2c2e3e; }}
        
        .section-header {{
            padding: 12px 15px;
            font-weight: 700;
            background: rgba(0, 0, 0, 0.2);
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 1rem;
        }}
        
        .section-body {{
            padding: 15px;
            line-height: 1.7;
            font-size: 0.95rem;
            color: #cbd5e1;
        }}
        
        #reader {{
            width: 100%;
            border-radius: 12px;
            overflow: hidden;
            display: none;
            margin: 15px 0;
            border: 2px solid #38bdf8;
        }}
        
        #preview {{
            width: 100%;
            border-radius: 12px;
            display: none;
            margin: 15px 0;
            border: 2px solid #38bdf8;
            max-height: 300px;
            object-fit: cover;
        }}
        
        #loading {{
            display: none;
            text-align: center;
            color: #38bdf8;
            font-weight: 700;
            padding: 30px;
            font-size: 1.1rem;
        }}
        
        #result {{
            margin-top: 20px;
        }}
        
        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }}
            70% {{ box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }}
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .diag-section {{
            animation: fadeIn 0.4s ease-out;
        }}
        
        input[type="file"] {{
            display: none;
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <h1>⚙️ {NOM_PROJET}</h1>
        <p class="subtitle">Expert Motorisation • KNX/DALI • Appareillage</p>
        
        <!-- SCANNER QR -->
        <div id="reader"></div>
        <button id="btnScan" class="btn btn-scan" onclick="startScan()">🔍 SCANNER CODE-BARRES</button>
        
        <!-- APERÇU IMAGE -->
        <img id="preview" alt="Aperçu photo">
        <button class="btn btn-photo" onclick="document.getElementById('in').click()">📷 PHOTO PRODUIT / PANNE</button>
        <input type="file" id="in" accept="image/*" capture="environment" onchange="pv(this)">
        
        <!-- DESCRIPTION -->
        <div class="input-box">
            <textarea id="desc" placeholder="Décrivez le problème technique, le type de produit, les codes erreurs..."></textarea>
            <button id="m" class="mic" onclick="tk()" title="Appuyer pour dicter">🎙️</button>
        </div>
        
        <!-- ACTIONS -->
        <button id="go" class="btn btn-main" onclick="run()">⚡ LANCER DIAGNOSTIC</button>
        <button id="sh" class="btn btn-share" onclick="share()">📤 PARTAGER RAPPORT</button>
        <button id="rs" class="btn btn-reset" onclick="reset()">🔄 NOUVEAU DIAGNOSTIC</button>
        
        <!-- CHARGEMENT -->
        <div id="loading">📡 Analyse Groq Vision + Recherche Web Perplexity...</div>
        
        <!-- RÉSULTATS -->
        <div id="result"></div>
    </div>
</div>

<script>
    // PWA Service Worker
    if ('serviceWorker' in navigator) {{
        navigator.serviceWorker.register('/sw.js').catch(e => console.log('SW error:', e));
    }}
    
    // Charger diagnostic sauvegardé
    window.onload = () => {{
        const saved = localStorage.getItem('lastDiag');
        if (saved) {{
            document.getElementById('result').innerHTML = saved;
            document.getElementById('rs').style.display = 'flex';
            document.getElementById('sh').style.display = 'flex';
        }}
    }};
    
    // SCANNER QR
    let scanner = null;
    function startScan() {{
        document.getElementById('reader').style.display = 'block';
        document.getElementById('btnScan').style.display = 'none';
        scanner = new Html5Qrcode("reader");
        scanner.start(
            {{ facingMode: "environment" }},
            {{ fps: 10, qrbox: 250 }},
            (txt) => {{
                document.getElementById('desc').value = "Référence scannée : " + txt;
                stopScan();
                run();
            }}
        ).catch(e => alert("Caméra bloquée ou non disponible"));
    }}
    
    function stopScan() {{
        if (scanner) {{
            scanner.stop().then(() => {{
                document.getElementById('reader').style.display = 'none';
                document.getElementById('btnScan').style.display = 'flex';
            }});
        }}
    }}
    
    // MICRO (Speech Recognition)
    let rec = null;
    function tk() {{
        const S = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!S) {{
            alert("Microphone non supporté sur ce navigateur");
            return;
        }}
        
        if (!rec) {{
            rec = new S();
            rec.lang = 'fr-FR';
            rec.onresult = (e) => {{
                const transcript = e.results[0][0].transcript;
                document.getElementById('desc').value += (document.getElementById('desc').value ? " " : "") + transcript;
            }};
            rec.onstart = () => document.getElementById('m').classList.add('mic-on');
            rec.onend = () => document.getElementById('m').classList.remove('mic-on');
        }}
        
        try {{
            rec.start();
        }} catch (e) {{
            rec.stop();
        }}
    }}
    
    // PHOTO
    let file = null;
    function pv(i) {{
        file = i.files[0];
        const r = new FileReader();
        r.onload = (e) => {{
            const p = document.getElementById('preview');
            p.src = e.target.result;
            p.style.display = 'block';
        }};
        r.readAsDataURL(file);
    }}
    
    // LANCER DIAGNOSTIC
    async function run() {{
        const res = document.getElementById('result');
        const load = document.getElementById('loading');
        const go = document.getElementById('go');
        
        go.style.display = 'none';
        load.style.display = 'block';
        res.innerHTML = "";
        
        const fd = new FormData();
        if (file) fd.append('image', file);
        fd.append('panne_description', document.getElementById('desc').value || "Diagnostic sans description");
        
        try {{
            const r = await fetch('/diagnostic', {{ method: 'POST', body: fd }});
            const html = await r.text();
            res.innerHTML = html;
            localStorage.setItem('lastDiag', html);
            document.getElementById('sh').style.display = 'flex';
            document.getElementById('rs').style.display = 'flex';
        }} catch (e) {{
            res.innerHTML = '<div class="diag-section s-secu"><div class="section-header">❌ Erreur Serveur</div><div class="section-body">' + e.message + '</div></div>';
            go.style.display = 'flex';
        }} finally {{
            load.style.display = 'none';
        }}
    }}
    
    // PARTAGER
    function share() {{
        const t = document.getElementById('result').innerText;
        if (navigator.share) {{
            navigator.share({{
                title: '{NOM_PROJET}',
                text: t
            }});
        }} else {{
            navigator.clipboard.writeText(t);
            alert("✅ Rapport copié dans le presse-papiers !");
        }}
    }}
    
    // RÉINITIALISER
    function reset() {{
        localStorage.removeItem('lastDiag');
        location.reload();
    }}
</script>
</body>
</html>"""

if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print(f"🚀 {NOM_PROJET} - DÉMARRAGE")
    print("=" * 70)
    print("📍 Accès : http://localhost:8000")
    print("🔧 Diagnostic Vision : Groq Llama 4 Scout")
    print("🌐 Recherche Web : Perplexity API")
    print("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
