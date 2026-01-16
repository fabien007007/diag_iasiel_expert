"""
Agent 2: GRIESSER SPECIALIST - Fiches techniques dynamiques
Utilise Perplexity API pour générer specs techniques détaillées
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

async def agent_griesser_specialist(product_description: str) -> str:
    """Agent 2: Fiche technique dynamique Griesser via Perplexity"""
    
    if not PERPLEXITY_API_KEY:
        return "❌ Erreur: PERPLEXITY_API_KEY manquante dans .env"
    
    try:
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "sonar-pro",
            "messages": [
                {
                    "role": "system",
                    "content": "Expert technique Griesser. Fournis fiches techniques détaillées avec specs, connexions, normes. Format Markdown clair et structuré."
                },
                {
                    "role": "user",
                    "content": f"""Fiche technique complète produit Griesser:

Description produit: {product_description}

Fournis en Markdown:

## 1. Identification Produit
- Marque/Fabricant
- Référence approx
- Catégorie
- Fonction

## 2. Caractéristiques Techniques
- Tension d'alimentation (AC/DC)
- Puissance/Courant nominal
- Dimensions
- Poids

## 3. Schéma de Câblage
- Représentation ASCII du schéma
- Phase, Neutre, Terre
- Connexions sorties
- Points d'attache

## 4. Spécifications Électriques
- Indice de protection (IP)
- Classe d'isolation
- Courant de fuite (si relevant)
- Température de fonctionnement

## 5. Certifications & Normes
- Marques CE
- Normes applicables (NF C 15-100, EN 60335, EN 50090, etc.)
- Directives UE

## 6. Conditions d'Utilisation
- Environnement (interne/externe)
- Humidité relative
- Altitude maximum
- Vibrations/chocs

## 7. Points d'Attention Sécurité
- Dangers principaux
- Consignation requise
- EPI recommandés
- Contrôles avant mise en service

Sois très technique et précis."""
                }
            ]
        }
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"❌ Erreur Perplexity: {response.status_code}"
    
    except Exception as e:
        return f"❌ Erreur agent specialist: {str(e)}"
