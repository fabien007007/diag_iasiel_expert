from groq import Groq

def expertise_electrique(question: str, context: str = None) -> str:
    """Expert électricien polyvalent tous produits, toutes marques"""
    
    client = Groq()
    
    prompt_system = (
        "Tu es expert électricien polyvalent. "
        "Expertises: NF C 15-100, tous produits électriques, tous fabricants (Legrand, Griesser, Came, BTF, Hager, Yoki, Schneider, Siemens). "
        "Domaines: appareillage, motorisation, domotique, tableaux électriques, câblage, variateurs, éclairage, automatismes, sécurité. "
        "Réponses techniques précises, normes respectées, solutions pratiques."
    )
    
    user_msg = question
    if context:
        user_msg = f"Contexte: {context}\n\nQuestion: {question}"
    
    messages = [
        {"role": "system", "content": prompt_system},
        {"role": "user", "content": user_msg}
    ]
    
    response = client.chat.completions.create(
        messages=messages,
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        temperature=0.2,
        max_tokens=1500,
    )
    
    return response.choices[0].message.content

