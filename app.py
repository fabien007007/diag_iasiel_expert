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

NOM_PROJET = "Griesser Expert AI"

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
                    "Expert technique Griesser. Donne des solutions précises, schémas de câblage, "
                    "codes erreurs, procédures de contrôle. Réponse en Markdown structuré avec ##."
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


async def analyze_with_groq(description: str, image_b64: str | None) -> str:
    from groq import Groq

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "## ⚠️ Erreur\nGROQ_API_KEY manquante dans .env"

    client = Groq(api_key=api_key)

    prompt_systeme = (
        "Tu es un expert technique Griesser (motorisation, KNX/DALI, appareillage). "
        "Objectif: diagnostic précis et actionnable.\n\n"
        "STRUCTURE OBLIGATOIRE (Markdown avec ##):\n"
        "## 🆔 Identification précise\n"
        "## 🔍 Analyse visuelle et technique\n"
        "## 🛠️ Correction étape par étape\n"
        "## ⚡ Sécurité / Normes\n"
    )

    messages = [{"role": "system", "content": prompt_systeme}]

    user_content = [{"type": "text", "text": f"PROBLÈME DÉCRIT : {description}"}]
    if image_b64:
        user_content.append(
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
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
async def diagnostic(image: UploadFile = File(None), panne_description: str = Form("")):
    image_b64 = None
    if image and image.filename:
        image_b64 = base64.b64encode(await image.read()).decode("utf-8")

    analysis = await analyze_with_groq(panne_description, image_b64)

    web_info = ""
    if panne_description:
        web_info = await search_perplexity(f"Solution technique Griesser pour: {panne_description}")

    return HTMLResponse(content=format_html_output(analysis, web_info))


@app.get("/", response_class=HTMLResponse)
def home():
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{NOM_PROJET}</title>
  <style>
    body {{ font-family: Segoe UI, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 15px; }}
    .card {{ background: #1e293b; max-width: 700px; margin: auto; padding: 20px; border-radius: 20px; border: 1px solid #334155; }}
    h1 {{ color: #38bdf8; text-align: center; font-size: 1.2rem; text-transform: uppercase; margin-bottom: 15px; }}
    .btn {{ width: 100%; padding: 16px; border-radius: 12px; border: none; font-weight: bold; cursor: pointer; margin-top: 12px; }}
    .btn-main {{ background: linear-gradient(135deg, #38bdf8 0%, #2563eb 100%); color: white; }}
    .btn-photo {{ background: #334155; color: white; border: 1px dashed #64748b; }}
    textarea {{ width: 100%; height: 110px; background: #0f172a; border: 1px solid #334155; border-radius: 12px; color: white; padding: 12px; box-sizing: border-box; resize: none; font-size: 1rem; }}
    #preview {{ width: 100%; border-radius: 12px; display: none; margin: 15px 0; border: 2px solid #38bdf8; max-height: 300px; object-fit: cover; }}
    #loading {{ display: none; text-align: center; color: #38bdf8; font-weight: bold; padding: 20px; }}
    .diag-section {{ background: #334155; border-radius: 12px; margin-top: 15px; border-left: 4px solid #94a3b8; overflow: hidden; }}
    .s-id {{ border-left-color: #38bdf8; }} .s-analyse {{ border-left-color: #fbbf24; }}
    .s-fix {{ border-left-color: #22c55e; }} .s-secu {{ border-left-color: #ef4444; }}
    .s-web {{ border-left-color: #f472b6; background: #2c2e3e; }}
    .section-header {{ padding: 12px 15px; font-weight: bold; background: rgba(0,0,0,0.2); }}
    .section-body {{ padding: 15px; line-height: 1.6; font-size: 0.95rem; }}
  </style>
</head>
<body>
<div class="card">
  <h1>{NOM_PROJET}</h1>
  <img id="preview">
  <button class="btn btn-photo" onclick="document.getElementById('in').click()">📷 PHOTO PRODUIT / PANNE</button>
  <input type="file" id="in" accept="image/*" capture="environment" hidden onchange="pv(this)">
  <textarea id="desc" placeholder="Décrivez le problème technique..."></textarea>
  <button id="go" class="btn btn-main" onclick="run()">⚡ LANCER LE DIAGNOSTIC</button>
  <div id="loading">📡 Analyse Groq + Recherche Web...</div>
  <div id="result"></div>
</div>
<script>
  let file = null;
  function pv(i) {{
    file = i.files[0];
    const r = new FileReader();
    r.onload = (e) => {{
      const p = document.getElementById('preview');
      p.src = e.target.result; p.style.display = 'block';
    }};
    r.readAsDataURL(file);
  }}
  async function run() {{
    const res = document.getElementById('result');
    const load = document.getElementById('loading');
    const go = document.getElementById('go');
    go.style.display = 'none'; load.style.display = 'block'; res.innerHTML = "";
    const fd = new FormData();
    if (file) fd.append('image', file);
    fd.append('panne_description', document.getElementById('desc').value);
    try {{
      const r = await fetch('/diagnostic', {{ method: 'POST', body: fd }});
      const html = await r.text();
      res.innerHTML = html;
    }} catch (e) {{
      res.innerHTML = '<div class="diag-section s-secu"><div class="section-header">❌ Erreur serveur</div><div class="section-body">' + e.message + '</div></div>';
    }} finally {{
      load.style.display = 'none'; go.style.display = 'block';
    }}
  }}
</script>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")), workers=1)

