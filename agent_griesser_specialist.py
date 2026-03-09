from groq import Groq

def expertise_electrique(question: str, context: str = None) -> str:
    """Expert électricien polyvalent tous produits, toutes marques"""

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

    user_msg = question
    if context:
        user_msg = f"Contexte: {context}\n\nQuestion: {question}"

    messages = [
        {"role": "system", "content": prompt_systeme},
        {"role": "user", "content": user_msg}
    ]

    response = client.chat.completions.create(
        messages=messages,
        model="openai/gpt-oss-120b",
        temperature=0.2,
        max_tokens=1500,
    )

    return response.choices[0].message.content
