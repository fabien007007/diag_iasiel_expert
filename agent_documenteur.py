from groq import Groq

def documenter_solution(diagnostic: str, description_panne: str) -> str:
    """Génère documentation complète pour solution électrique (tous produits, toutes marques)"""
    
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
    
    messages = [
        {"role": "system", "content": prompt_system},
        {
            "role": "user",
            "content": f"Diagnostic: {diagnostic}\n\nProblème initial: {description_panne}\n\nGénère documentation d'installation/correction complète."
        }
    ]
    
    response = client.chat.completions.create(
        messages=messages,
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.3,
        max_tokens=2000,
    )
    
    return response.choices[0].message.content

