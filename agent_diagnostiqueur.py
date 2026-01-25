from groq import Groq
import base64

def diagnostic_produit_electrique(description: str, image_base64: str = None) -> str:
    """Diagnostic générique pour TOUT produit électrique (Legrand, Griesser, Came, BTF, Hager, Yoki, etc.)"""
    
    client = Groq()
    
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
    
    messages = [{"role": "system", "content": prompt_system}]
    
    user_content = [{"type": "text", "text": f"PROBLÈME: {description}"}]
    if image_base64:
        user_content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
        })
    
    messages.append({"role": "user", "content": user_content})
    
    response = client.chat.completions.create(
        messages=messages,
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.2,
        max_tokens=1800,
    )
    
    return response.choices[0].message.content

