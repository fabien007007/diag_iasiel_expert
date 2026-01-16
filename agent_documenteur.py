"""
Agent 3: DOCUMENTEUR - Procédures installation dynamiques
Utilise Perplexity API pour générer procédures étape-par-étape
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

async def agent_documenteur(product_description: str) -> str:
    """Agent 3: Procédures installation dynamiques Griesser"""
    
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
                    "content": "Formateur technique Griesser agréé. Procédures installation complètes pour électriciens professionnels. Format Markdown étape-par-étape, ultra-détaillé."
                },
                {
                    "role": "user",
                    "content": f"""Procédure installation complète produit Griesser:

Produit: {product_description}

Fournis procédure COMPLÈTE en Markdown:

## 📋 PRÉPARATION & SÉCURITÉ

### Matériel Nécessaire
- Liste exhaustive
- Quantités exactes
- Références fournisseur si applicable

### Consignation Sécurité
- Étapes NF C 15-100
- Pictogrammes danger
- Vérification absence de tension (VAT)
- Équipement protection individuelle (EPI)

## ⚡ RACCORDEMENTS ÉLECTRIQUES

### Schéma Détaillé
- ASCII art avec phases/neutre/terre
- Points de connexion exacts
- Câblages auxiliaires si applicable

### Points de Serrage
- Couples de serrage (en Nm)
- Outils requis
- Vérifications visuelles

### Longueurs Maximales Câbles
- Par étage/zone
- Isolations obligatoires
- Gaines requises

## 📐 MESURES ÉLECTRIQUES

### Tension Attendue
- Valeur nominale (AC ou DC)
- Tolérances acceptables (min/max)
- Points de mesure exacts

### Procédure de Mesure
- Voltmètre connecté où
- Gammes correctes
- Actions si tension incorrecte

## ✅ TESTS FONCTIONNEMENT

### Tests Basiques
- Commande/réponse
- LED et signalisation
- Indépendance zones (si applicable)

### Conditions Extrêmes
- Test température basse/haute
- Test humidité
- Test vibrations (si applicable)

## 🚀 MISE EN SERVICE

### Checklist Finale
- Points de vérification (10-15 items)
- Validations avant livraison
- Documentation complète

### Erreurs Fréquentes & Solutions
- Top 5 des erreurs
- Symptômes observés
- Procédure de correction

### Maintenance Recommandée
- Vérifications périodiques
- Fréquence des tests
- Pièces d'usure à surveiller

Format: Précis, étape-par-étape, pour électricien pro. Respecte NF C 15-100 strictement."""
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
        return f"❌ Erreur documenteur: {str(e)}"
