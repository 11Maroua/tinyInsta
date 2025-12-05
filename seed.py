#!/usr/bin/env python3
"""
Script de seed LOCAL pour Tiny Instagram.
Écrit directement dans Datastore (beaucoup plus rapide que l'API HTTP).

Usage:
    python seed.py --users 1000 --posts 50000 --follows 20
"""

from google.cloud import datastore
import argparse
import random
from datetime import datetime, timedelta
import os


os.environ['GOOGLE_CLOUD_PROJECT'] = 'tinyinsta-480307'

def seed_data(users: int, posts: int, follows: int):
    """Crée des utilisateurs et des posts directement dans Datastore."""
    client = datastore.Client()
    
    user_names = [f"user{i}" for i in range(1, users + 1)]
    
    print(f"Création de {users} utilisateurs...")
    created_users = 0
    for name in user_names:
        key = client.key('User', name)
        entity = client.get(key)
        if entity is None:
            entity = datastore.Entity(key)
            entity['follows'] = []
            client.put(entity)
            created_users += 1
    
    print(f"Attribution des follows ({follows} par user)...")
    for name in user_names:
        key = client.key('User', name)
        entity = client.get(key)
        others = [u for u in user_names if u != name]
        if others and follows > 0:
            selection = random.sample(others, min(follows, len(others)))
            entity['follows'] = sorted(set(entity.get('follows', [])).union(selection))
            client.put(entity)
    
    print(f"Création de {posts} posts...")
    created_posts = 0
    base_time = datetime.utcnow()
    batch = []
    
    for i in range(posts):
        author = random.choice(user_names)
        p = datastore.Entity(client.key('Post'))
        p['author'] = author
        p['content'] = f"Post {i+1} by {author}"
        p['created'] = base_time - timedelta(seconds=i)
        batch.append(p)
        
        # Écriture par batch de 500
        if len(batch) >= 500:
            client.put_multi(batch)
            created_posts += len(batch)
            print(f"  {created_posts}/{posts} posts créés...")
            batch = []
    
    # Dernier batch
    if batch:
        client.put_multi(batch)
        created_posts += len(batch)
    
    print(f"✓ Seed terminé: {created_users} users, {created_posts} posts")


def main():
    parser = argparse.ArgumentParser(description="Seed Datastore local")
    parser.add_argument('--users', type=int, required=True)
    parser.add_argument('--posts', type=int, required=True)
    parser.add_argument('--follows', type=int, required=True)
    args = parser.parse_args()
    
    seed_data(args.users, args.posts, args.follows)


if __name__ == '__main__':
    main()
