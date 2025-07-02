# -*- coding: utf-8 -*-
"""
Utilitaires pour l'interaction avec la base de données vectorielle Qdrant.

Ce module fournit une classe `QdrantManager` pour encapsuler la logique
de connexion, de création de collection, d'ajout de documents vectorisés
et de recherche de similarité dans Qdrant.

Auteur: Cloud Temple - LLMaaS Team
Version: 1.0.0
Date: 2025-06-30
"""

import uuid
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient, models
from rich.console import Console

console = Console()

class QdrantManager:
    """Gère les interactions avec une instance Qdrant."""

    def __init__(self, host: str = "localhost", port: int = 6333, collection_name: str = "minichat_rag"):
        """
        Initialise le client Qdrant.
        
        Args:
            host: L'hôte du serveur Qdrant.
            port: Le port du serveur Qdrant.
            collection_name: Le nom de la collection à utiliser.
        """
        try:
            self.client = QdrantClient(host=host, port=port)
            self.collection_name = collection_name
            console.print(f"[info]Connecté à Qdrant sur {host}:{port}[/info]")
        except Exception as e:
            console.print(f"[bold red]Erreur de connexion à Qdrant: {e}[/bold red]")
            self.client = None

    def check_collection_exists(self) -> bool:
        """Vérifie si la collection configurée existe."""
        if not self.client:
            return False
        try:
            collections_response = self.client.get_collections()
            existing_collections = [c.name for c in collections_response.collections]
            return self.collection_name in existing_collections
        except Exception as e:
            console.print(f"[bold red]Impossible de vérifier les collections Qdrant: {e}[/bold red]")
            return False

    def create_collection_if_not_exists(self, vector_size: int):
        """
        Crée la collection dans Qdrant si elle n'existe pas déjà.

        Args:
            vector_size: La dimension des vecteurs qui seront stockés.
        """
        if not self.client:
            return
        try:
            collections_response = self.client.get_collections()
            existing_collections = [c.name for c in collections_response.collections]
            if self.collection_name not in existing_collections:
                self.client.recreate_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
                )
                console.print(f"[green]Collection '{self.collection_name}' créée avec des vecteurs de taille {vector_size}.[/green]")
            else:
                console.print(f"[info]Collection '{self.collection_name}' déjà existante.[/info]")
        except Exception as e:
            console.print(f"[bold red]Erreur lors de la vérification/création de la collection Qdrant: {e}[/bold red]")

    def upsert_points(self, vectors: List[List[float]], payloads: List[Dict[str, Any]]):
        """
        Ajoute ou met à jour des points (vecteurs et leurs métadonnées) dans la collection.

        Args:
            vectors: Une liste de vecteurs (embeddings).
            payloads: Une liste de dictionnaires contenant les métadonnées (ex: le texte original).
        """
        if not self.client:
            return
        if len(vectors) != len(payloads):
            console.print("[bold red]Erreur: Le nombre de vecteurs ne correspond pas au nombre de payloads.[/bold red]")
            return

        points = [
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=payload
            )
            for vector, payload in zip(vectors, payloads)
        ]

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True
            )
            console.print(f"[green]{len(points)} points ont été ajoutés/mis à jour dans la collection '{self.collection_name}'.[/green]")
        except Exception as e:
            console.print(f"[bold red]Erreur lors de l'upsert des points dans Qdrant: {e}[/bold red]")

    def search(self, vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recherche les points les plus similaires à un vecteur donné.

        Args:
            vector: Le vecteur de requête.
            limit: Le nombre maximum de résultats à retourner.

        Returns:
            Une liste de dictionnaires, chaque dictionnaire représentant un point trouvé.
        """
        if not self.client:
            return []
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=vector,
                limit=limit
            )
            return [hit.model_dump() for hit in search_result]
        except Exception as e:
            console.print(f"[bold red]Erreur lors de la recherche dans Qdrant: {e}[/bold red]")
            return []

    def list_points(self, limit: int = 100, offset: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Liste les points stockés dans la collection.

        Args:
            limit: Le nombre maximum de points à retourner.
            offset: L'offset pour la pagination (ID du dernier point de la page précédente).

        Returns:
            Une liste de dictionnaires représentant les points stockés.
        """
        if not self.client:
            return []
        try:
            scroll_result = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            return [point.model_dump() for point in scroll_result[0]]
        except Exception as e:
            console.print(f"[bold red]Erreur lors de la liste des points Qdrant: {e}[/bold red]")
            return []

    def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations sur la collection.

        Returns:
            Un dictionnaire avec les informations de la collection ou None en cas d'erreur.
        """
        if not self.client:
            return None
        try:
            collection_info = self.client.get_collection(collection_name=self.collection_name)
            return collection_info.model_dump()
        except Exception as e:
            console.print(f"[bold red]Erreur lors de la récupération des infos de collection: {e}[/bold red]")
            return None

    def delete_point(self, point_id: str) -> bool:
        """
        Supprime un point spécifique de la collection.

        Args:
            point_id: L'ID du point à supprimer.

        Returns:
            True si la suppression a réussi, False sinon.
        """
        if not self.client:
            return False
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(points=[point_id])
            )
            console.print(f"[green]Point '{point_id}' supprimé avec succès.[/green]")
            return True
        except Exception as e:
            console.print(f"[bold red]Erreur lors de la suppression du point '{point_id}': {e}[/bold red]")
            return False

    def delete_collection(self) -> bool:
        """
        Supprime complètement la collection.

        Returns:
            True si la suppression a réussi, False sinon.
        """
        if not self.client:
            return False
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            console.print(f"[green]Collection '{self.collection_name}' supprimée avec succès.[/green]")
            return True
        except Exception as e:
            console.print(f"[bold red]Erreur lors de la suppression de la collection '{self.collection_name}': {e}[/bold red]")
            return False

    def clear_collection(self) -> bool:
        """
        Vide la collection (supprime tous les points mais garde la collection).

        Returns:
            True si l'opération a réussi, False sinon.
        """
        if not self.client:
            return False
        try:
            # Supprimer tous les points en utilisant un filtre vide
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(filter=models.Filter())
            )
            console.print(f"[green]Collection '{self.collection_name}' vidée avec succès.[/green]")
            return True
        except Exception as e:
            console.print(f"[bold red]Erreur lors du vidage de la collection '{self.collection_name}': {e}[/bold red]")
            return False
