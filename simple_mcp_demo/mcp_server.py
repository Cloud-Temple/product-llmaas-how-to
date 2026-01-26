# -*- coding: utf-8 -*-
"""
Serveur MCP HTTP Sécurisé - Exemple Pédagogique
================================================

Ce script implémente un serveur MCP (Model Context Protocol) via HTTP/SSE
en utilisant FastMCP et un middleware d'authentification.

Sécurité :
----------
Ce serveur est protégé par une clé API (Bearer Token).
Le client doit fournir le header : `Authorization: Bearer <votre_clé>`

Architecture :
--------------
1. FastMCP : Gère la logique MCP, les outils et créé l'application Starlette sous-jacente.
2. Middleware : Intercepte les requêtes HTTP pour vérifier le token et logger (si debug).
3. Uvicorn : Lance l'application sécurisée.
"""

import os
import sys
import json
import uvicorn
from dotenv import load_dotenv

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("❌ Erreur : Dépendances manquantes.")
    print("Installez-le avec : pip install -r requirements.txt")
    sys.exit(1)

# ============================================================================
# SECTION 1 : Configuration et Initialisation
# ============================================================================

load_dotenv()

# Initialisation de FastMCP
mcp = FastMCP("time-server")

# ============================================================================
# SECTION 2 : Définition des Outils
# ============================================================================

@mcp.tool()
def get_current_time() -> str:
    """
    Retourne la date et l'heure actuelles.
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo
    
    now = datetime.now(ZoneInfo("Europe/Paris"))
    formatted_time = now.strftime("%d/%m/%Y %H:%M:%S")
    timezone = "Europe/Paris"
    
    # Note: Ce print est déjà un log d'exécution de l'outil
    print(f"⏰ [MCP Server] Outil exécuté : {formatted_time}", file=sys.stderr)
    return f"{formatted_time} ({timezone})"

# ============================================================================
# SECTION 3 : Sécurité et Logging (Middlewares ASGI Purs)
# ============================================================================

class LoggingASGIMiddleware:
    """
    Middleware pour logger les requêtes et réponses JSON-RPC en mode debug.
    """
    def __init__(self, app, debug=False):
        self.app = app
        self.debug = debug

    async def __call__(self, scope, receive, send):
        if not self.debug or scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path")
        method = scope.get("method")
        query_string = scope.get("query_string", b"").decode()
        
        # Log plus détaillé avec query params (ex: session_id)
        full_path = f"{path}?{query_string}" if query_string else path
        print(f"📥 [HTTP] {method} {full_path}", file=sys.stderr)
        
        # Détection et explication pédagogique du session_id
        if "session_id=" in query_string:
            session_id = query_string.split("session_id=")[1].split("&")[0]
            print(f"🔑 [DEBUG] Session ID détecté : {session_id} (Fourni par le serveur lors du handshake SSE)", file=sys.stderr)

        # Interception pour logger le body de la requête
        async def wrapped_receive():
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                if body:
                    try:
                        # Essayer de formater le JSON pour la lisibilité
                        json_body = json.loads(body)
                        # Ne logger que si c'est du JSON-RPC ou intéressant
                        if "jsonrpc" in json_body or "method" in json_body:
                            print(f"🔍 [DEBUG] Reçu JSON-RPC : {json.dumps(json_body, indent=2)}", file=sys.stderr)
                    except:
                        pass # Ce n'est pas du JSON, on ignore
            return message

        # Interception pour logger le body de la réponse
        async def wrapped_send(message):
            if message["type"] == "http.response.body":
                body = message.get("body", b"")
                if body:
                    try:
                        # Essayer de décoder pour voir si c'est du JSON
                        text_body = body.decode()
                        if "jsonrpc" in text_body:
                             print(f"📤 [DEBUG] Réponse JSON-RPC : {text_body}", file=sys.stderr)
                    except:
                        pass
            await send(message)

        await self.app(scope, wrapped_receive, wrapped_send)


class APIKeyASGIMiddleware:
    """
    Middleware ASGI pur pour vérifier la clé d'API.
    Plus robuste que BaseHTTPMiddleware pour le streaming (SSE).
    """
    def __init__(self, app, debug=False):
        self.app = app
        self.debug = debug
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            auth_key = os.getenv("MCP_SERVER_AUTH_KEY")
            
            if auth_key:
                if self.debug:
                    print("🔒 [Auth] Vérification de la clé API...", file=sys.stderr)
                
                # Récupération des headers (liste de tuples bytes)
                headers = dict(scope.get("headers", []))
                
                # Le header Authorization peut être en minuscules (standard ASGI)
                auth_header_bytes = headers.get(b"authorization")
                auth_header = auth_header_bytes.decode("utf-8") if auth_header_bytes else None
                
                expected = f"Bearer {auth_key}"
                
                if not auth_header:
                    if self.debug:
                        print("❌ [Auth] Header Authorization manquant", file=sys.stderr)
                    return await self._send_403(send, "Unauthorized: Missing Authorization Header")
                
                if auth_header != expected:
                    if self.debug:
                        print("❌ [Auth] Clé API invalide", file=sys.stderr)
                    return await self._send_403(send, "Unauthorized: Invalid API Key")
                
                if self.debug:
                    print("✅ [Auth] Authentification réussie", file=sys.stderr)

        # Si tout est OK (ou pas de clé configurée), on passe la requête à l'app
        await self.app(scope, receive, send)
    
    async def _send_403(self, send, message):
        await send({
            "type": "http.response.start",
            "status": 403,
            "headers": [(b"content-type", b"text/plain")],
        })
        await send({
            "type": "http.response.body",
            "body": message.encode(),
        })

# ============================================================================
# SECTION 4 : Démarrage du Serveur
# ============================================================================

if __name__ == "__main__":
    import argparse
    import uvicorn
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--auth-key", type=str, help="Surcharge la clé d'auth du .env")
    parser.add_argument("--debug", action="store_true", help="Active les logs détaillés")
    args = parser.parse_args()
    
    if args.auth_key:
        os.environ["MCP_SERVER_AUTH_KEY"] = args.auth_key
    
    # Récupérer l'application ASGI générée par FastMCP
    base_app = mcp.sse_app()
    
    # Empiler les middlewares (L'ordre d'exécution est inversé par rapport à l'encapsulation)
    # 1. Logging (Extérieur) -> voit tout passer
    # 2. Auth (Milieu) -> bloque si pas auth
    # 3. App (Centre)
    
    # Wrapper avec Auth
    secure_app = APIKeyASGIMiddleware(base_app, debug=args.debug)
    
    # Wrapper avec Logging
    final_app = LoggingASGIMiddleware(secure_app, debug=args.debug)
        
    print("=" * 70, file=sys.stderr)
    print("🚀 Serveur MCP HTTP Sécurisé - Démarrage", file=sys.stderr)
    print(f"📡 Écoute sur http://0.0.0.0:{args.port}", file=sys.stderr)
    print(f"🔒 Authentification : {'ACTIVÉE' if os.getenv('MCP_SERVER_AUTH_KEY') else 'DÉSACTIVÉE (Mode ouvert)'}", file=sys.stderr)
    print(f"🐛 Mode Debug       : {'ACTIVÉ' if args.debug else 'Désactivé'}", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    
    uvicorn.run(final_app, host="0.0.0.0", port=args.port)
