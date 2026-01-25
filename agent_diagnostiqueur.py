from groq import Groq
import base64

def diagnostic_produit_electrique(description: str, image_base64: str = None) -> str:
    """Diagnostic générique pour TOUT produit électrique (Legrand, Griesser, Came, BTF, Hager, Yoki, etc.)"""
    
    client = Groq()
    
    prompt_system = (
        "Tu es un expert électricien généraliste avec expertise multi-marques. "
        "Diagnostic pour TOUS produits électriques: appareillage, motorisation, domotique, tableaux, câblage, variateurs, éclairage. "
        "Marques: Legrand, Griesser, Came, BTF, Hager, Yoki, Schneider, Siemens, autres. "
        "Respecte NF C 15-100, sécurité électrique, efficacité énergétique. "
        "Réponse structurée Markdown avec sections ## claires. "
        "STRUCTURE: ## 🆔 Identification | ## 🔍 Analyse | ## 🛠️ Solution | ## ⚡ Sécurité"
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

