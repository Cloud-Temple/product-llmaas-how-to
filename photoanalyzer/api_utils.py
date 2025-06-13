#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module API pour PhotoAnalyzer.

Fournit des fonctions pour interagir avec l'API LLMaaS pour l'analyse d'images multimodales.
"""

import httpx
import json
import time
from typing import Optional, Dict, Any
from cli_ui import print_message, print_debug_data

def analyze_image_ollama(
    ollama_url: str,
    model: str,
    image_base64: str,
    prompt: str,
    silent: bool = False,
    debug_mode: bool = False,
    timeout: int = 120
) -> Optional[str]:
    """
    Analyse une image via une API Ollama directe.
    """
    if not ollama_url.endswith('/'):
        ollama_url += '/'
    
    full_url = f"{ollama_url}api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False
    }
    
    headers = {"Content-Type": "application/json"}
    
    if debug_mode and not silent:
        print_debug_data("Requête API Ollama", {
            "URL": full_url,
            "Modèle": model,
            "Prompt": prompt,
        }, silent=silent, debug_mode=debug_mode)

    start_time = time.time()
    
    try:
        with httpx.Client(timeout=timeout) as client:
            print_message(f"Envoi de la requête à l'API Ollama sur {ollama_url}...", style="info", silent=silent, debug_mode=debug_mode)
            response = client.post(full_url, headers=headers, json=payload)
            request_duration = time.time() - start_time
            
            if response.status_code != 200:
                print_message(f"Erreur API Ollama (HTTP {response.status_code}): {response.text[:200]}", style="error", silent=silent, debug_mode=debug_mode)
                return None
            
            try:
                response_data = response.json()
                analysis_result = response_data.get("response")
                if not analysis_result:
                    print_message("Réponse API Ollama invalide: champ 'response' manquant.", style="error", silent=silent, debug_mode=debug_mode)
                    return None
                
                print_message(f"Analyse via Ollama terminée avec succès en {request_duration:.2f}s.", style="success", silent=silent, debug_mode=debug_mode)
                return analysis_result

            except json.JSONDecodeError:
                print_message("Erreur lors du décodage de la réponse JSON de Ollama.", style="error", silent=silent, debug_mode=debug_mode)
                return None

    except httpx.TimeoutException:
        print_message(f"Timeout de la requête API Ollama ({timeout}s).", style="error", silent=silent, debug_mode=debug_mode)
        return None
    except httpx.ConnectError:
        print_message("Erreur de connexion à l'API Ollama. Vérifiez l'URL et votre connexion réseau.", style="error", silent=silent, debug_mode=debug_mode)
        return None
    except Exception as e:
        print_message(f"Erreur inattendue lors de l'appel API Ollama: {e}", style="error", silent=silent, debug_mode=debug_mode)
        return None

def analyze_image_api(
    api_url: str,
    api_key: str,
    model: str,
    image_base64: str,
    prompt: str,
    max_tokens: int = 1000,
    temperature: float = 0.3,
    silent: bool = False,
    debug_mode: bool = False,
    timeout: int = 120,
    min_pixels: Optional[int] = None,
    max_pixels: Optional[int] = None,
    image_format: str = "jpeg"
) -> Optional[str]:
    """
    Analyse une image via l'API LLMaaS en utilisant un modèle multimodal.
    """
    
    if not api_url.endswith('/'):
        api_url += '/'
    
    full_url = f"{api_url}v1/chat/completions"
    
    image_content: Dict[str, Any] = {
        "type": "image",
        "image": f"data:image/{image_format};base64,{image_base64}"
    }
    
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": [
                image_content,
                {"type": "text", "text": prompt}
            ]
        }
    ]
    
    payload = {
        "model": model,
        "messages": messages
        # "max_tokens" and "temperature" are removed as they might interfere
        # with how the LLMaaS proxy handles multimodal requests.
        # The proxy is expected to apply default values.
    }
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    if debug_mode and not silent:
        import copy
        debug_payload = copy.deepcopy(payload)
        try:
            debug_payload["messages"][1]["content"][0]["image"] = f"data:image/{image_format};base64,<BASE64_DATA_{len(image_base64)}_CHARS>"
        except (IndexError, KeyError):
            pass
        
        print_debug_data("Requête API", {
            "URL": full_url,
            "Headers": {k: (v[:10] + "..." if k == "Authorization" else v) for k, v in headers.items()},
            "Body": debug_payload
        }, silent=silent, debug_mode=debug_mode)

    start_time = time.time()
    
    try:
        with httpx.Client(timeout=timeout) as client:
            print_message("Envoi de la requête à l'API...", style="info", silent=silent, debug_mode=debug_mode)
            
            response = client.post(
                full_url,
                headers=headers,
                json=payload
            )
            
            request_duration = time.time() - start_time
            
            if response.status_code != 200:
                error_msg = f"Erreur API (HTTP {response.status_code})"
                try:
                    error_detail = response.json()
                    if 'error' in error_detail:
                        error_msg += f": {error_detail['error'].get('message', 'Erreur inconnue')}"
                except:
                    error_msg += f": {response.text[:200]}"
                
                print_message(error_msg, style="error", silent=silent, debug_mode=debug_mode)
                if debug_mode and not silent:
                    print_debug_data("Payload Réponse (Erreur)", {
                        "Status Code": response.status_code,
                        "Headers": dict(response.headers),
                        "Body (text)": response.text
                    }, silent=silent, debug_mode=debug_mode)
                return None
            
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                print_message("Erreur lors du décodage de la réponse JSON.", style="error", silent=silent, debug_mode=debug_mode)
                return None
            
            if 'choices' not in response_data or not response_data['choices']:
                print_message("Réponse API invalide: aucun choix trouvé.", style="error", silent=silent, debug_mode=debug_mode)
                return None
            
            choice = response_data['choices'][0]
            if 'message' not in choice or 'content' not in choice['message']:
                print_message("Réponse API invalide: contenu manquant.", style="error", silent=silent, debug_mode=debug_mode)
                return None
            
            analysis_result = choice['message']['content']
            
            if debug_mode and not silent:
                usage = response_data.get('usage', {})
                print_debug_data("Réponse API", {
                    "Durée requête": f"{request_duration:.2f}s",
                    "Tokens prompt": usage.get('prompt_tokens', 'N/A'),
                    "Tokens completion": usage.get('completion_tokens', 'N/A'),
                    "Tokens total": usage.get('total_tokens', 'N/A'),
                    "Longueur réponse": f"{len(analysis_result):,} caractères",
                    "Finish reason": choice.get('finish_reason', 'N/A')
                }, silent=silent, debug_mode=debug_mode)
                
                print_debug_data("Payload Réponse", {
                    "Status Code": response.status_code,
                    "Headers": dict(response.headers),
                    "Body": response_data
                }, silent=silent, debug_mode=debug_mode)
            
            print_message(f"Analyse terminée avec succès en {request_duration:.2f}s.", style="success", silent=silent, debug_mode=debug_mode)
            return analysis_result
            
    except httpx.TimeoutException:
        print_message(f"Timeout de la requête API ({timeout}s).", style="error", silent=silent, debug_mode=debug_mode)
        return None
    except httpx.ConnectError:
        print_message("Erreur de connexion à l'API. Vérifiez l'URL et votre connexion réseau.", style="error", silent=silent, debug_mode=debug_mode)
        return None
    except Exception as e:
        print_message(f"Erreur inattendue lors de l'appel API: {e}", style="error", silent=silent, debug_mode=debug_mode)
        return None

def test_api_connection(
    api_url: str,
    api_key: str,
    silent: bool = False,
    debug_mode: bool = False,
    timeout: int = 30
) -> bool:
    """
    Teste la connexion à l'API LLMaaS.
    """
    if not api_url.endswith('/'):
        api_url += '/'
    
    test_url = f"{api_url}v1/models"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        with httpx.Client(timeout=timeout) as client:
            print_message("Test de connexion à l'API...", style="info", silent=silent, debug_mode=debug_mode)
            
            response = client.get(test_url, headers=headers)
            
            if response.status_code == 200:
                print_message("Connexion API réussie.", style="success", silent=silent, debug_mode=debug_mode)
                
                if debug_mode and not silent:
                    try:
                        models_data = response.json()
                        models_count = len(models_data.get('data', []))
                        print_debug_data("Test API", {
                            "URL": test_url,
                            "Status": response.status_code,
                            "Modèles disponibles": models_count
                        }, silent=silent, debug_mode=debug_mode)
                    except:
                        pass
                
                return True
            else:
                print_message(f"Échec du test de connexion API (HTTP {response.status_code}).", style="error", silent=silent, debug_mode=debug_mode)
                return False
                
    except httpx.TimeoutException:
        print_message(f"Timeout du test de connexion API ({timeout}s).", style="error", silent=silent, debug_mode=debug_mode)
        return False
    except httpx.ConnectError:
        print_message("Erreur de connexion lors du test API. Vérifiez l'URL et votre connexion réseau.", style="error", silent=silent, debug_mode=debug_mode)
        return False
    except Exception as e:
        print_message(f"Erreur inattendue lors du test API: {e}", style="error", silent=silent, debug_mode=debug_mode)
        return False

def get_available_models(
    api_url: str,
    api_key: str,
    silent: bool = False,
    debug_mode: bool = False,
    timeout: int = 30
) -> Optional[list]:
    """
    Récupère la liste des modèles disponibles via l'API.
    """
    if not api_url.endswith('/'):
        api_url += '/'
    
    models_url = f"{api_url}v1/models"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        with httpx.Client(timeout=timeout) as client:
            print_message("Récupération de la liste des modèles...", style="info", silent=silent, debug_mode=debug_mode)
            
            response = client.get(models_url, headers=headers)
            
            if response.status_code == 200:
                models_data = response.json()
                models_list = models_data.get('data', [])
                
                multimodal_models = [
                    model for model in models_list
                    if model.get('capabilities', {}).get('multimodal', False)
                ]
                
                print_message(f"Trouvé {len(multimodal_models)} modèle(s) multimodal(ux) sur {len(models_list)} total.", 
                             style="success", silent=silent, debug_mode=debug_mode)
                
                if debug_mode and not silent and multimodal_models:
                    print_debug_data("Modèles Multimodaux", {
                        "Modèles": [model.get('id', 'N/A') for model in multimodal_models]
                    }, silent=silent, debug_mode=debug_mode)
                
                return multimodal_models
            else:
                print_message(f"Erreur lors de la récupération des modèles (HTTP {response.status_code}).", 
                             style="error", silent=silent, debug_mode=debug_mode)
                return None
                
    except Exception as e:
        print_message(f"Erreur lors de la récupération des modèles: {e}", style="error", silent=silent, debug_mode=debug_mode)
        return None
