# -*- coding: utf-8 -*-
"""
Exemple simple de Tool Calling avec l'API LLMaaS.

Ce script montre comment définir un outil simple (une calculatrice),
l'envoyer à un modèle compatible, et interpréter la réponse du modèle
pour exécuter l'outil et renvoyer le résultat.
"""
import os
import json
import httpx
import argparse
from dotenv import load_dotenv

# --- Configuration ---
# Charger les variables d'environnement depuis un fichier .env
load_dotenv()

API_URL = os.getenv("API_URL", "https://api.ai.cloud-temple.com/v1")
API_KEY = os.getenv("API_KEY")

# --- Définition de l'outil ---


def calculator(expression: str) -> str:
    """
    Évalue une expression mathématique simple.
    Exemple: "2 + 2 * 10"
    """
    try:
        # Sécurité : ne pas utiliser eval() directement en production sans validation stricte.
        # Pour cet exemple, nous limitons les caractères autorisés.
        allowed_chars = "0123456789+-*/(). "
        if not all(char in allowed_chars for char in expression):
            return "Erreur: L'expression contient des caractères non autorisés."
        # eval() est utilisé ici pour la simplicité de l'exemple.
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Erreur de calcul: {str(e)}"


# Description de l'outil au format attendu par l'API
TOOLS_AVAILABLE = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Évalue une expression mathématique. Par exemple, '2+2*10'.",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "L'expression mathématique à évaluer."}},
                "required": ["expression"],
            },
        },
    }
]

# Mapping entre le nom de l'outil et la fonction Python à appeler
TOOL_FUNCTIONS_MAP = {"calculator": calculator}

# --- Logique principale ---


def run_chat_with_tool_calling(args):
    """
    Fonction principale qui exécute le scénario de test.
    """
    if not API_KEY:
        print("❌ Erreur: La variable d'environnement API_KEY n'est pas définie.")
        print("Veuillez créer un fichier .env ou l'exporter dans votre session.")
        return

    model_to_use = args.model if args.model else os.getenv("DEFAULT_MODEL", "qwen3:30b-a3b")

    print(f"🤖 Modèle utilisé : {model_to_use}")
    print(f"⚡ Mode streaming : {'Activé' if args.stream else 'Désactivé'}")
    print(f"🐛 Mode debug    : {'Activé' if args.debug else 'Désactivé'}")
    print("-" * 30)

    # 1. Premier appel à l'API avec la question de l'utilisateur
    # ---------------------------------------------------------
    print("➡️ Étape 1: Envoi de la requête initiale au LLM...")

    # L'historique des messages commence avec la question de l'utilisateur
    messages = [{"role": "user", "content": "Bonjour, peux-tu calculer 15 + (3 * 5) ?"}]

    payload = {
        "model": model_to_use,
        "messages": messages,
        "tools": TOOLS_AVAILABLE,
        "tool_choice": "auto",  # Le modèle décide s'il doit utiliser un outil
        "stream": args.stream,
    }

    if args.debug:
        print("\n--- Payload envoyé (Étape 1) ---")
        print(json.dumps(payload, indent=2))
        print("----------------------------------")

    try:
        with httpx.Client() as client:
            if args.stream:
                with client.stream("POST", f"{API_URL}/chat/completions", headers={"Authorization": f"Bearer {API_KEY}"}, json=payload, timeout=60) as response:
                    response.raise_for_status()

                    # Logique de reconstruction du message de l'assistant
                    assistant_message = {"role": "assistant", "content": None, "tool_calls": []}

                    buffer = ""
                    for chunk in response.iter_bytes():
                        buffer += chunk.decode("utf-8")
                        while "\n\n" in buffer:
                            event_str, buffer = buffer.split("\n\n", 1)
                            if not event_str.startswith("data:"):
                                continue

                            json_data = event_str[len("data: ") :].strip()
                            if json_data == "[DONE]":
                                break

                            try:
                                data = json.loads(json_data)
                                delta = data["choices"][0].get("delta", {})

                                if args.debug:
                                    print(f"DEBUG (Stream Delta): {delta}")

                                # Agréger le contenu textuel
                                if delta.get("content"):
                                    if assistant_message["content"] is None:
                                        assistant_message["content"] = ""
                                    assistant_message["content"] += delta["content"]
                                    print(delta["content"], end="", flush=True)

                                # Agréger les tool_calls
                                if delta.get("tool_calls"):
                                    for tc_delta in delta["tool_calls"]:
                                        index = tc_delta["index"]
                                        # S'assurer que la liste est assez grande
                                        while len(assistant_message["tool_calls"]) <= index:
                                            assistant_message["tool_calls"].append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})

                                        # Mettre à jour l'id, le nom et les arguments
                                        if tc_delta.get("id"):
                                            assistant_message["tool_calls"][index]["id"] = tc_delta["id"]
                                        if tc_delta.get("function", {}).get("name"):
                                            assistant_message["tool_calls"][index]["function"]["name"] = tc_delta["function"]["name"]
                                        if "arguments" in tc_delta.get("function", {}):
                                            new_args = tc_delta["function"]["arguments"]
                                            # Gérer les arguments qui peuvent être un dict (Ollama) ou un str (VLLM)
                                            if isinstance(new_args, dict):
                                                # Si c'est un dictionnaire, on le convertit en chaîne JSON et on remplace
                                                assistant_message["tool_calls"][index]["function"]["arguments"] = json.dumps(new_args)
                                            else:
                                                # Sinon, on concatène la chaîne
                                                if not isinstance(assistant_message["tool_calls"][index]["function"]["arguments"], str):
                                                    assistant_message["tool_calls"][index]["function"]["arguments"] = ""
                                                assistant_message["tool_calls"][index]["function"]["arguments"] += new_args

                            except (json.JSONDecodeError, KeyError) as e:
                                if args.debug:
                                    print(f"DEBUG (JSON Error/KeyError): {e} - Data: {json_data}")
                                continue
                        if json_data == "[DONE]":
                            break
                    print()  # Nouvelle ligne après le stream
                    response_data = {"choices": [{"message": assistant_message}]}
            else:
                response = client.post(
                    f"{API_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    json=payload,
                    timeout=60,
                )
                response.raise_for_status()
                response_data = response.json()

    except httpx.HTTPStatusError as e:
        print(f"❌ Erreur API (HTTP Status) lors de l'étape 1: {e}")
        print(f"Réponse de l'API : {e.response.text}")
        return
    except httpx.RequestError as e:
        print(f"❌ Erreur API (Request) lors de l'étape 1: {e}")
        return

    if args.debug:
        print("\n--- Payload reçu (Étape 1) ---")
        print(json.dumps(response_data, indent=2))
        print("----------------------------------")

    # Le message de l'assistant contient la demande d'appel d'outil
    assistant_message = response_data["choices"][0]["message"]

    # Si le message de l'assistant contient des tool_calls, le contenu doit être nul.
    if assistant_message.get("tool_calls"):
        assistant_message["content"] = None

    messages.append(assistant_message)

    # 2. Vérification et exécution de l'appel d'outil
    # ------------------------------------------------
    print("\n✅ Le LLM a demandé d'utiliser un outil.")

    if "tool_calls" not in assistant_message:
        print("🤔 Le modèle n'a pas demandé d'utiliser un outil. Réponse directe :")
        print(assistant_message.get("content", "Pas de contenu."))
        return

    tool_call = assistant_message["tool_calls"][0]
    function_name = tool_call["function"]["name"]
    function_args_str = tool_call["function"]["arguments"]
    tool_call_id = tool_call["id"]

    print(f"   - Outil à appeler : {function_name}")
    print(f"   - Arguments       : {function_args_str}")

    if function_name in TOOL_FUNCTIONS_MAP:
        function_to_call = TOOL_FUNCTIONS_MAP[function_name]
        try:
            # Les arguments sont une chaîne JSON, il faut les parser
            function_args = json.loads(function_args_str)
            tool_result = function_to_call(**function_args)
            print(f"   - Résultat de l'outil : {tool_result}")
        except Exception as e:
            print(f"❌ Erreur lors de l'exécution de l'outil: {e}")
            tool_result = f"Erreur: {e}"
    else:
        print(f"❌ Outil inconnu : {function_name}")
        tool_result = f"Erreur: Outil '{function_name}' non trouvé."

    # 3. Second appel à l'API avec le résultat de l'outil
    # ----------------------------------------------------
    print("\n➡️ Étape 2: Envoi du résultat de l'outil au LLM...")

    # On ajoute le résultat de l'outil à l'historique des messages
    messages.append({"role": "tool", "tool_call_id": tool_call_id, "content": tool_result})

    # On refait un appel SANS les outils cette fois-ci pour obtenir la réponse finale
    payload_final = {
        "model": model_to_use,
        "messages": messages,
        "stream": args.stream,
    }

    if args.debug:
        print("\n--- Payload envoyé (Étape 2) ---")
        print(json.dumps(payload_final, indent=2))
        print("----------------------------------")

    try:
        with httpx.Client() as client:
            if args.stream:
                with client.stream(
                    "POST", f"{API_URL}/chat/completions", headers={"Authorization": f"Bearer {API_KEY}"}, json=payload_final, timeout=60
                ) as response_final:
                    response_final.raise_for_status()
                    final_answer_stream = ""
                    for chunk in response_final.iter_bytes():
                        try:
                            decoded_chunk = chunk.decode("utf-8")
                            for line in decoded_chunk.splitlines():
                                if line.startswith("data: "):
                                    json_data = line[len("data: ") :]
                                    if json_data.strip() == "[DONE]":
                                        continue

                                    data = json.loads(json_data)
                                    delta = data["choices"][0]["delta"]

                                    if args.debug:
                                        print(f"DEBUG (Stream Delta Final): {delta}")

                                    if "content" in delta and delta["content"]:
                                        final_answer_stream += delta["content"]
                                        print(delta["content"], end="", flush=True)
                        except json.JSONDecodeError as e:
                            if args.debug:
                                print(f"DEBUG (JSON Decode Error Final): {e} - Chunk: {decoded_chunk}")
                            continue
                    print()  # Nouvelle ligne après le stream
                    final_answer = final_answer_stream
            else:
                response_final = client.post(
                    f"{API_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    json=payload_final,
                    timeout=60,
                )
                response_final.raise_for_status()
                final_data = response_final.json()
                final_answer = final_data["choices"][0]["message"]["content"]

    except (httpx.HTTPStatusError, httpx.RequestError) as e:
        print(f"❌ Erreur API lors de l'étape 2: {e}")
        return

    if args.debug and not args.stream:  # Pour le stream, le debug est déjà affiché
        print("\n--- Payload reçu (Étape 2) ---")
        print(json.dumps(final_data, indent=2))
        print("----------------------------------")

    print("\n✅ Réponse finale du LLM :")
    print(f'💬 "{final_answer}"')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exemple simple de Tool Calling avec l'API LLMaaS.")
    parser.add_argument("--stream", action="store_true", help="Activer le mode streaming pour les réponses du LLM.")
    parser.add_argument("--model", type=str, help="Spécifier le modèle LLM à utiliser (ex: qwen3:30b-a3b).")
    parser.add_argument("--debug", action="store_true", help="Afficher les payloads complets envoyés et reçus.")
    args = parser.parse_args()

    run_chat_with_tool_calling(args)
