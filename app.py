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

LLM_CONFIGS = {
    "oss": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "model": "openai/gpt-oss-120b",
        "env_key": "GROQ_API_KEY",
        "timeout": 60,
    }
}
ACTIVE_LLM = "oss"
LLM_CONFIG = LLM_CONFIGS[ACTIVE_LLM]
GROQ_API_KEY = os.getenv(LLM_CONFIG["env_key"])

@app.get("/manifest.json")
async def get_manifest():
    return FileResponse("manifest.json")

@app.get("/sw.js")
async def get_sw():
    return FileResponse("sw.js", media_type="application/javascript")

@app.get("/debug-env")
async def debug_env():
    return {
        "active_llm": ACTIVE_LLM,
        "env_key": LLM_CONFIG["env_key"],
        "groq_api_key_present": bool(GROQ_API_KEY),
        "groq_api_key_prefix": GROQ_API_KEY[:8] if GROQ_API_KEY else None,
    }

async def search_groq(query: str) -> str:
    api_key = GROQ_API_KEY
    if not api_key:
        return "Erreur: GROQ_API_KEY manquante sur le serveur."

    url = LLM_CONFIG["url"]
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": LLM_CONFIG["model"],
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
        res = requests.post(url, json=data, headers=headers, timeout=LLM_CONFIG["timeout"])
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        return f"Erreur Groq: {res.status_code}"
    except Exception:
        return "Service Groq indisponible."

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
        body = "\n".join(lines[1:]).strip()

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
            f"<section class='{css}'>"
            f"<h3><span>{icon}</span>{title}</h3>"
            f"<div>{body.replace(chr(10), '<br>')}</div>"
            f"</section>"
        )

    if web_info.strip():
        html_res += (
            "<section class='diag-section s-web'>"
            "<h3><span>🌐</span>Réponse IA</h3>"
            f"<div>{web_info.replace(chr(10), '<br>')}</div>"
            "</section>"
        )

    return html_res

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DIAG ELEC IASIEL</title>
<style>
:root{
  --bg:#0b1220;
  --card:#131c31;
  --text:#e8eefc;
  --muted:#9fb0d3;
  --line:#263352;
  --acc:#4da3ff;
  --ok:#32d296;
  --warn:#ffb84d;
  --danger:#ff6b6b;
}
*{box-sizing:border-box}
body{
  margin:0;
  font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;
  background:linear-gradient(180deg,#0a1020,#0e1730 40%,#0b1220);
  color:var(--text);
}
.wrap{max-width:1100px;margin:0 auto;padding:24px}
.top{
  display:flex;align-items:center;justify-content:space-between;gap:16px;
  margin-bottom:20px
}
.brand{display:flex;align-items:center;gap:14px}
.logo{
  width:56px;height:56px;border-radius:14px;
  background:linear-gradient(135deg,#4da3ff,#6df0c2);
  display:grid;place-items:center;color:#03111f;font-size:26px;font-weight:800
}
h1{margin:0;font-size:28px}
.sub{color:var(--muted);margin-top:4px}
.grid{display:grid;grid-template-columns:1.2fr .8fr;gap:18px}
.card{
  background:rgba(19,28,49,.88);
  border:1px solid var(--line);
  border-radius:20px;
  box-shadow:0 10px 30px rgba(0,0,0,.25);
}
.pad{padding:18px}
label{display:block;margin:10px 0 8px;color:#c6d4f7;font-weight:600}
textarea,input{
  width:100%;border:1px solid #33456e;background:#0d1630;color:var(--text);
  border-radius:14px;padding:14px 14px;font-size:15px;outline:none
}
textarea{min-height:170px;resize:vertical}
.actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
button{
  border:0;border-radius:14px;padding:12px 16px;font-weight:700;cursor:pointer
}
.btn{
  background:linear-gradient(135deg,#4da3ff,#2b7de9);color:white
}
.btn2{
  background:#182544;color:#dbe7ff;border:1px solid #32456f
}
.muted{color:var(--muted);font-size:13px}
.status{
  margin-top:12px;padding:10px 12px;border-radius:12px;background:#0d1630;border:1px solid #25365b;
  color:#cfe0ff
}
.preview{
  display:flex;align-items:center;justify-content:center;
  min-height:240px;border:1px dashed #355083;border-radius:16px;background:#0d1630;overflow:hidden
}
.preview img{max-width:100%;display:block}
.diag-section{
  background:#0d1630;border:1px solid #263a60;border-radius:16px;padding:14px 14px;margin:12px 0
}
.diag-section h3{
  margin:0 0 8px 0;font-size:18px;display:flex;align-items:center;gap:10px
}
.s-id{border-color:#2e5b98}
.s-analyse{border-color:#7b5cff}
.s-fix{border-color:#17a673}
.s-secu{border-color:#ff9f43}
.s-web{border-color:#4da3ff}
.out{
  line-height:1.55;color:#eaf1ff;white-space:normal;word-break:break-word
}
.badges{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
.badge{
  padding:7px 10px;border-radius:999px;background:#0d1630;border:1px solid #31456f;color:#d9e7ff;font-size:12px
}
@media (max-width:900px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div class="brand">
      <div class="logo">⚡</div>
      <div>
        <h1>DIAG ELEC IASIEL</h1>
        <div class="sub">Diagnostic technique électrique assisté par IA</div>
      </div>
    </div>
    <div class="badges">
      <div class="badge">NF C 15-100</div>
      <div class="badge">IEC 60364</div>
      <div class="badge">Analyse image + texte</div>
    </div>
  </div>

  <div class="grid">
    <div class="card pad">
      <label for="question">Décrivez le problème</label>
      <textarea id="question" placeholder="Ex: Identifier ce variateur, analyser le câblage visible, proposer les corrections conformes et vérifier la compatibilité avec Legrand/Hager..."></textarea>

      <label for="image">Ajoutez une photo</label>
      <input id="image" type="file" accept="image/*">

      <div class="actions">
        <button class="btn" onclick="runDiag()">Lancer le diagnostic</button>
        <button class="btn2" onclick="resetAll()">Réinitialiser</button>
      </div>
      <div class="status" id="status">Prêt.</div>
    </div>

    <div class="card pad">
      <label>Aperçu image</label>
      <div class="preview" id="preview">Aucune image sélectionnée</div>
    </div>
  </div>

  <div class="card pad" style="margin-top:18px">
    <label>Résultat</label>
    <div id="result" class="out"></div>
  </div>
</div>

<script>
const imageInput = document.getElementById('image');
const preview = document.getElementById('preview');
imageInput.addEventListener('change', () => {
  const file = imageInput.files && imageInput.files[0];
  if (!file) {
    preview.innerHTML = 'Aucune image sélectionnée';
    return;
  }
  const reader = new FileReader();
  reader.onload = e => {
    preview.innerHTML = `<img alt="preview" src="${e.target.result}">`;
  };
  reader.readAsDataURL(file);
});

function setStatus(msg){ document.getElementById('status').textContent = msg; }

function resetAll(){
  document.getElementById('question').value = '';
  document.getElementById('image').value = '';
  document.getElementById('result').innerHTML = '';
  preview.innerHTML = 'Aucune image sélectionnée';
  setStatus('Prêt.');
}

async function runDiag(){
  const q = document.getElementById('question').value.trim();
  const file = document.getElementById('image').files[0];
  const result = document.getElementById('result');

  if (!q && !file){
    setStatus('Ajoutez une description ou une image.');
    return;
  }

  const fd = new FormData();
  fd.append('question', q);
  if (file) fd.append('image', file);

  setStatus('Analyse en cours...');
  result.innerHTML = '';

  try{
    const res = await fetch('/diagnostic', { method:'POST', body:fd });
    const html = await res.text();
    result.innerHTML = html;
    setStatus('Diagnostic terminé.');
  }catch(e){
    result.innerHTML = "<div class='diag-section s-secu'><h3><span>⚠️</span>Erreur</h3><div>Impossible d'obtenir le diagnostic.</div></div>";
    setStatus('Erreur réseau.');
  }
}
</script>
</body>
</html>
"""

@app.post("/diagnostic", response_class=HTMLResponse)
async def diagnostic(
    question: str = Form(""),
    image: UploadFile = File(None),
):
    prompt_parts = []
    if question.strip():
        prompt_parts.append(f"Question utilisateur :\n{question.strip()}")

    if image is not None:
        content = await image.read()
        mime = image.content_type or "image/jpeg"
        b64 = base64.b64encode(content).decode("utf-8")
        prompt_parts.append(
            "Image fournie (base64) :\n"
            f"data:{mime};base64,{b64}\n"
            "Analyse cette image en détail pour identifier les éléments techniques visibles."
        )

    final_prompt = "\n\n".join(prompt_parts).strip()
    web_info = await search_groq(final_prompt)
    return format_html_output(web_info)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
