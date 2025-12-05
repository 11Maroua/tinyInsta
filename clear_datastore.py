#!/usr/bin/env python3
"""
Script pour vider le Datastore (User et Post) entre chaque configuration.

Usage:
    python clear_datastore.py                    # Vide User et Post
    python clear_datastore.py --kind Post        # Vide seulement Post
    python clear_datastore.py --kind User        # Vide seulement User
    python clear_datastore.py --dry-run          # Affiche sans supprimer
"""

from google.cloud import datastore
import argparse
import time
import os
os.environ['GOOGLE_CLOUD_PROJECT'] = 'tinyinsta-480307'

def delete_all_entities(client: datastore.Client, kind: str, batch_size: int = 500, dry_run: bool = False):
    """Supprime toutes les entités d'un kind donné par batches."""
    total_deleted = 0
    
    while True:
        # Récupérer un batch de clés
        query = client.query(kind=kind)
        query.keys_only()
        keys = list(query.fetch(limit=batch_size))
        
        if not keys:
            break
        
        if dry_run:
            print(f"  [DRY-RUN] Supprimeraient {len(keys)} entités {kind}")
            total_deleted += len(keys)
            # En dry-run, on ne peut pas continuer la boucle car rien n'est supprimé
            # On compte juste le premier batch
            query2 = client.query(kind=kind)
            query2.keys_only()
            all_keys = list(query2.fetch())
            return len(all_keys)
        else:
            client.delete_multi(keys)
            total_deleted += len(keys)
            print(f"  Supprimé {total_deleted} entités {kind}...")
            time.sleep(0.1)  # Petit délai pour ne pas surcharger
    
    return total_deleted


def main():
    parser = argparse.ArgumentParser(description="Vide le Datastore")
    parser.add_argument('--kind', choices=['User', 'Post', 'all'], default='all',
                        help="Kind à supprimer (default: all)")
    parser.add_argument('--dry-run', action='store_true',
                        help="Affiche ce qui serait supprimé sans supprimer")
    parser.add_argument('--batch-size', type=int, default=500,
                        help="Taille des batches de suppression (default: 500)")
    args = parser.parse_args()
    
    client = datastore.Client()
    
    print("=" * 60)
    print("NETTOYAGE DATASTORE")
    if args.dry_run:
        print("[MODE DRY-RUN - Aucune suppression]")
    print("=" * 60)
    
    kinds_to_delete = ['User', 'Post'] if args.kind == 'all' else [args.kind]
    
    for kind in kinds_to_delete:
        print(f"\nSuppression de toutes les entités '{kind}'...")
        start = time.time()
        count = delete_all_entities(client, kind, args.batch_size, args.dry_run)
        elapsed = time.time() - start
        print(f"  -> {count} entités '{kind}' supprimées en {elapsed:.1f}s")
    
    print("\n" + "=" * 60)
    print("NETTOYAGE TERMINÉ")
    print("=" * 60)


if __name__ == '__main__':
    main()
