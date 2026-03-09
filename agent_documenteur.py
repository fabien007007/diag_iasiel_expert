from groq import Groq

def documenter_solution(diagnostic: str, description_panne: str) -> str:
    """Génère documentation complète pour solution électrique (tous produits, toutes marques)"""

    client = Groq()

    prompt_system = (
        "Tu es expert technique en documentation électrique. "
        "Rédige documentation professionnelle pour solutions électriques. "
        "Tous produits: tableaux, appareillage, motorisation, domotique, éclairage. "
        "Tous fabricants: Legrand, Griesser, Came, BTF, Hager, Yoki, Schneider, Siemens, autres. "
        "Format: instructions claires, étapes numérotées, références normes, schémas textuels. "
        "Langue: Français technique."
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
        model="openai/gpt-oss-120b",
        temperature=0.3,
        max_tokens=2000,
    )

    return response.choices[0].message.content
