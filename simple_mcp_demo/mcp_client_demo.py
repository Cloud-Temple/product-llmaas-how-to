# -*- coding: utf-8 -*-
"""
Client MCP HTTP + LLMaaS - Exemple Pédagogique
===============================================

Ce script démontre comment se connecter à un serveur MCP via HTTP/SSE
et utiliser ses outils avec l'API LLMaaS en utilisant le client standard MCP.

Architecture HTTP/SSE :
-----------------------
┌─────────────────────────────────────────────────┐
│  CE SCRIPT (mcp_client_demo.py)                 │
│  Rôle : Client et Orchestrateur                 │
│  • Utilise mcp.client.sse.sse_client            │
│  • Se connecte au endpoint /sse                 │
│  • Gère la session automatiquement              │
└─────────────────────────────────────────────────┘
         ↕️ HTTP/SSE
┌──────────────────────┐    ┌──────────────────────┐
│  Serveur MCP         │    │  API LLMaaS          │
│  (mcp_server.py)     │    │  (Cloud Temple)      │
│                      │    │                      │
│  http://localhost    │    │  Modèle :            │
│  :8000               │    │  qwen3-next:80b      │
└──────────────────────┘    └──────────────────────┘
"""

import os
import json
import argparse
import httpx
import asyncio
from dotenv import load_dotenv

# Import du client SSE standard de la librairie MCP
from mcp.client.sse import sse_client
from mcp import ClientSession

# ============================================================================
# SECTION 1 : Configuration
# ============================================================================

load_dotenv()

API_URL = os.getenv("API_URL", "https://api.ai.cloud-temple.com/v1")
API_KEY = os.getenv("API_KEY")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")


# ============================================================================
# SECTION 2 : Conversion des Outils MCP vers Format OpenAI
# ============================================================================

def convert_mcp_tools_to_openai(list_tools_result) -> list:
    """
    Convertit les outils du format MCP vers le format attendu par l'API OpenAI/LLMaaS.
    """
    openai_tools = []
    
    # list_tools_result est un objet ListToolsResult qui contient une liste 'tools'
    for mcp_tool in list_tools_result.tools:
        openai_tool = {
            "type": "function",
            "function": {
                "name": mcp_tool.name,
                "description": mcp_tool.description,
                "parameters": mcp_tool.inputSchema
            }
        }
        openai_tools.append(openai_tool)
    
    return openai_tools


# ============================================================================
# SECTION 3 : Logique Principale Asynchrone
# ============================================================================

async def run_mcp_demo(args):
    """
    Fonction principale asynchrone qui exécute la démonstration complète.
    """
    
    # Vérifications préliminaires
    if not API_KEY:
        print("❌ Erreur: La variable d'environnement API_KEY n'est pas définie.")
        return
    
    model_to_use = args.model if args.model else os.getenv("DEFAULT_MODEL", "qwen3-next:80b")
    
    print("=" * 70)
    print("🤖 DÉMONSTRATION MCP HTTP + LLMaaS")
    print("=" * 70)
    print(f"🤖 Modèle utilisé : {model_to_use}")
    print(f"🌐 Serveur MCP    : {MCP_SERVER_URL}")
    print(f"⚡ Mode streaming : {'Activé' if args.stream else 'Désactivé'}")
    print("=" * 70)
    
    # URL du endpoint SSE (par défaut /sse avec FastMCP)
    sse_url = f"{MCP_SERVER_URL}/sse"
    
    # Récupération de la clé d'auth serveur (optionnelle)
    server_auth_key = os.getenv("MCP_SERVER_AUTH_KEY")
    headers = {}
    if server_auth_key:
        headers["Authorization"] = f"Bearer {server_auth_key}"
        print(f"🔒 Authentification activée pour le serveur MCP.")
    
    print(f"\n🔌 Connexion au endpoint SSE : {sse_url}")
    
    try:
        # Utilisation du client context manager 'sse_client' fourni par mcp
        # On passe les headers pour l'authentification
        async with sse_client(sse_url, headers=headers) as (read_stream, write_stream):
            print("✅ Connexion SSE établie.")
            
            # Création de la session MCP sur les flux de lecture/écriture
            async with ClientSession(read_stream, write_stream) as session:
                print("✅ Session MCP initialisée.")
                
                # ÉTAPE 1 : Initialisation et liste des outils
                await session.initialize()
                
                print("\n📋 Récupération de la liste des outils...")
                result = await session.list_tools()
                
                if not result.tools:
                    print("❌ Aucun outil disponible sur le serveur MCP.")
                    return
                
                for tool in result.tools:
                    print(f"   • {tool.name}: {tool.description}")
                
                # Conversion pour LLMaaS
                openai_tools = convert_mcp_tools_to_openai(result)
                
                # ÉTAPE 2 : Appel au LLM
                print("\n" + "─" * 70)
                print("ÉTAPE 2 : Envoi de la question au LLM")
                print("─" * 70)
                
                user_question = "Bonjour, peux-tu me dire quelle heure il est actuellement ?"
                print(f"💬 Question : \"{user_question}\"")
                
                messages = [{"role": "user", "content": user_question}]
                
                payload = {
                    "model": model_to_use,
                    "messages": messages,
                    "tools": openai_tools,
                    "tool_choice": "auto",
                    "stream": args.stream
                }
                
                # Appel API LLMaaS
                # On utilise un bloc try/except spécifique ici car si une erreur survient
                # en dehors du bloc 'async with ClientSession', elle sera mieux gérée
                # qu'une ExceptionGroup issue de la session.
                try:
                    async with httpx.AsyncClient() as client:
                        if args.stream:
                            # Gestion du streaming (simplifiée pour la démo)
                            async with client.stream(
                                "POST",
                                f"{API_URL}/chat/completions",
                                headers={"Authorization": f"Bearer {API_KEY}"},
                                json=payload,
                                timeout=60
                            ) as response:
                                response.raise_for_status()
                                
                                assistant_message = {"role": "assistant", "content": None, "tool_calls": []}
                                
                                async for chunk in response.aiter_bytes():
                                    # Pour simplifier cette démo, on n'affiche pas tout le parsing stream complexe
                                    # mais on assume que le modèle va demander un outil rapidement.
                                    pass 
                                
                                # Note: Pour une vraie implémentation streaming robuste, voir les exemples précédents.
                                pass
                        
                        # Pour assurer le succès de la démo MCP, utilisons le mode non-streaming pour la logique d'appel
                        response = await client.post(
                            f"{API_URL}/chat/completions",
                            headers={"Authorization": f"Bearer {API_KEY}"},
                            json=payload,
                            timeout=60
                        )
                        response.raise_for_status()
                        response_data = response.json()
                    
                    assistant_message = response_data["choices"][0]["message"]
                    messages.append(assistant_message)
                except Exception as llm_error:
                    print(f"❌ Erreur lors de l'appel LLM : {llm_error}")
                    return

                # ÉTAPE 3 : Exécution de l'outil via MCP
                if assistant_message.get("tool_calls"):
                    tool_call = assistant_message["tool_calls"][0]
                    function_name = tool_call["function"]["name"]
                    arguments_str = tool_call["function"]["arguments"]
                    tool_call_id = tool_call["id"]
                    
                    print("\n" + "─" * 70)
                    print("ÉTAPE 3 : Exécution de l'outil via le serveur MCP")
                    print("─" * 70)
                    print(f"✅ Le LLM a demandé d'utiliser l'outil : {function_name}")
                    
                    try:
                        arguments = json.loads(arguments_str) if arguments_str else {}
                    except json.JSONDecodeError:
                        arguments = {}
                    
                    # Appel de l'outil via la session MCP standard
                    print(f"🔧 Appel de l'outil '{function_name}' via session MCP...")
                    tool_result = await session.call_tool(function_name, arguments)
                    
                    # Le résultat peut être une liste de contenus (TextContent, ImageContent)
                    # On extrait le texte du premier contenu s'il est de type texte
                    result_text = ""
                    if tool_result.content:
                        first_content = tool_result.content[0]
                        # Utilisation de getattr pour éviter les erreurs de typage statique
                        result_text = getattr(first_content, 'text', str(first_content))
                    
                    print(f"✅ Résultat de l'outil : {result_text}")
                    
                    # ÉTAPE 4 : Réponse finale
                    print("\n" + "─" * 70)
                    print("ÉTAPE 4 : Envoi du résultat au LLM pour la réponse finale")
                    print("─" * 70)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": result_text
                    })
                    
                    payload_final = {
                        "model": model_to_use,
                        "messages": messages,
                        "stream": args.stream
                    }
                    
                    async with httpx.AsyncClient() as client:
                        if args.stream:
                            async with client.stream(
                                "POST",
                                f"{API_URL}/chat/completions",
                                headers={"Authorization": f"Bearer {API_KEY}"},
                                json=payload_final,
                                timeout=60
                            ) as response_final:
                                response_final.raise_for_status()
                                async for chunk in response_final.aiter_bytes():
                                    try:
                                        decoded_chunk = chunk.decode("utf-8")
                                        for line in decoded_chunk.splitlines():
                                            if line.startswith("data: "):
                                                json_data = line[len("data: "):]
                                                if json_data.strip() == "[DONE]": continue
                                                delta = json.loads(json_data)["choices"][0]["delta"]
                                                if "content" in delta:
                                                    print(delta["content"], end="", flush=True)
                                    except: pass
                                print()
                        else:
                            response_final = await client.post(
                                f"{API_URL}/chat/completions",
                                headers={"Authorization": f"Bearer {API_KEY}"},
                                json=payload_final,
                                timeout=60
                            )
                            print(f"\n💬 {response_final.json()['choices'][0]['message']['content']}")
                else:
                    print("🤔 Le modèle n'a pas demandé d'outil.")
                    print(assistant_message.get("content"))

    except Exception as e:
        print(f"\n❌ Erreur : {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--model", type=str)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    
    asyncio.run(run_mcp_demo(args))
