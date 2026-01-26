# -*- coding: utf-8 -*-
"""
Exemple de traduction avec TranslateGemma via l'API LLMaaS.
Ce script montre comment formater correctement le prompt pour obtenir des résultats optimaux.
"""
import os
import requests
import json
from dotenv import load_dotenv

# Chargement de la configuration
load_dotenv()
API_KEY = os.getenv("LLMAAS_API_KEY")
API_URL = os.getenv("LLMAAS_API_URL", "https://api.ai.cloud-temple.com/v1")
MODEL = os.getenv("LLMAAS_MODEL", "translategemma:27b")

def translate_text(text, source_lang="English", source_code="en", target_lang="French", target_code="fr"):
    """
    Traduit un texte en utilisant le format de prompt spécifique à TranslateGemma.
    """
    if not API_KEY:
        print("Erreur: La variable d'environnement LLMAAS_API_KEY n'est pas définie.")
        return None

    # Construction du prompt selon le guide officiel TranslateGemma
    # Notez les deux sauts de ligne avant {text} qui sont importants.
    prompt_template = f"""You are a professional {source_lang} ({source_code}) to {target_lang} ({target_code}) translator. Your goal is to accurately convey the meaning and nuances of the original {source_lang} text while adhering to {target_lang} grammar, vocabulary, and cultural sensitivities.
Produce only the {target_lang} translation, without any additional explanations or commentary. Please translate the following {source_lang} text into {target_lang}:


{text}"""

    print(f"--- Traduction de '{source_lang}' vers '{target_lang}' avec le modèle '{MODEL}' ---")
    
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt_template
            }
        ],
        "temperature": 0.0, # Température à 0 pour une traduction déterministe et fidèle
        "max_tokens": 2048
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        response = requests.post(f"{API_URL}/chat/completions", headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        translation = result['choices'][0]['message']['content'].strip()
        
        return translation
        
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'appel API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Détails: {e.response.text}")
        return None

if __name__ == "__main__":
    # Texte d'exemple (Description de TranslateGemma en anglais)
    text_to_translate = "TranslateGemma is a new collection of open translation models built on Gemma 3, available in 4B, 12B, and 27B parameter sizes."
    
    print(f"Texte original:\n{text_to_translate}\n")
    
    translation = translate_text(
        text_to_translate, 
        source_lang="English", source_code="en", 
        target_lang="French", target_code="fr"
    )
    
    if translation:
        print(f"Traduction:\n{translation}")
