"""
Agent 1: DIAGNOSTIQUEUR - Analyse photo + diagnostic panne
Utilise Llama 4 Scout (local) + Perplexity (cloud)
"""

import os
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

async def analyze_photo_llama_scout(image_path: str) -> dict:
    """Analyse photo Griesser via Llama 4 Scout (local)"""
    try:
        if not Path(image_path).exists():
            return {
                "product_identified": False,
                "error": "Photo introuvable",
                "visual_state": "Erreur",
                "defects_detected": []
            }
        
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        payload = {
            "model": "llama4:scout",
            "prompt": """Analysez cette photo de produit électrotechnique Griesser (motorisation, KNX, DALI, appareillage).

Identifiez:
1. Type de produit exact (marque, catégorie, fonction)
2. État visuel (bon/acceptable/dégradé/endommagé)
3. Défauts visuels détectés (corrosion, dégâts, usure, connecteurs défectueux)
4. Composants visibles et leurs états

Répondez en JSON strict avec keys: product_type, visual_state, defects_list, components_visible""",
            "stream": False,
            "temperature": 0.3
        }
        
        response = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "product_identified": True,
                "visual_state": "Analysé",
                "analysis_text": result.get("response", ""),
                "defects_detected": [],
                "model_used": "llama4:scout"
            }
        else:
            return {
                "product_identified": False,
                "error": f"Ollama error {response.status_code}",
                "visual_state": "Non analysé",
                "defects_detected": []
            }
    
    except Exception as e:
        return {
            "product_identified": False,
            "error": str(e),
            "visual_state": "Erreur",
            "defects_detected": []
        }

async def agent_diagnostiqueur(panne: str, image_path: str = None) -> dict:
    """Diagnostic complet Griesser: photo + panne"""
    
    result = {
        "panne": panne,
        "vision_analysis": {},
        "diagnostic": "",
        "recommendations": []
    }
    
    # Analyse visuelle si photo
    if image_path:
        result["vision_analysis"] = await analyze_photo_llama_scout(image_path)
    
    # Diagnostic via Perplexity
    if PERPLEXITY_API_KEY:
        try:
            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }
            
            photo_context = f"Photo analysée: {result['vision_analysis'].get('analysis_text', 'Pas d\'analyse visuelle')}" if image_path else "Pas de photo"
            
            payload = {
                "model": "sonar-pro",
                "messages": [
                    {
                        "role": "system",
                        "content": "Expert technique Griesser certifié. Fournis diagnostics précis pour motorisation, KNX/DALI, appareillage. Respecte normes NF C 15-100."
                    },
                    {
                        "role": "user",
                        "content": f"""Diagnostic Griesser requis:

Contexte photo: {photo_context}
Panne signalée: {panne}

Fournis:
1. Identification produit détaillée
2. Causes probables de la panne
3. Procédure diagnostic étape-par-étape
4. Solutions recommandées
5. Pièces de remplacement éventuelles
6. Normes applicables

Sois précis et technique."""
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
                result["diagnostic"] = response.json()["choices"][0]["message"]["content"]
            else:
                result["diagnostic"] = f"Erreur Perplexity: {response.status_code}"
        
        except Exception as e:
            result["diagnostic"] = f"Erreur diagnostic: {str(e)}"
    else:
        result["diagnostic"] = "⚠️ PERPLEXITY_API_KEY non configurée dans .env"
    
    return result
