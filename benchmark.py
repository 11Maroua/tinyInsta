#!/usr/bin/env python3
"""
Benchmark TinyInsta - Mesure les temps de réponse de l'API timeline.

Usage:
    python benchmark.py --url https://APP.appspot.com --test conc --output out
    python benchmark.py --url https://APP.appspot.com --test post --posts 100 --prefix user --output out
    python benchmark.py --url https://APP.appspot.com --test fanout --followers 50 --prefix user --output out
    python benchmark.py --url https://APP.appspot.com --test all --output out
"""

import subprocess
import re
import csv
import os
import argparse
import random
import time
import sys


# Configuration
NB_USERS = 1000
NB_RUNS = 3
CONCURRENCE_FIXE = 50  # Pour tests post et fanout


def run_ab(url: str, num_requests: int, concurrency: int, user: str) -> dict:
    """Lance Apache Bench et parse les résultats."""
    full_url = f"{url}/api/timeline?user={user}&limit=20"
    
    cmd = [
        "ab",
        "-n", str(num_requests),
        "-c", str(concurrency),
        "-q",
        "-l",  # Ignore variation longueur réponse
        full_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        output = result.stdout + result.stderr
        
        temps_moyen = 0
        echecs = 0
        
        # Parse "Time per request" (mean)
        match = re.search(r"Time per request:\s+([\d.]+)\s+\[ms\]\s+\(mean\)", output)
        if match:
            temps_moyen = float(match.group(1))
        
        # Parse "Failed requests"
        match = re.search(r"Failed requests:\s+(\d+)", output)
        if match:
            echecs = int(match.group(1))
        
        # Parse "Non-2xx responses"
        match = re.search(r"Non-2xx responses:\s+(\d+)", output)
        if match:
            echecs += int(match.group(1))
        
        return {"temps_moyen": round(temps_moyen, 2), "echecs": echecs}
        
    except subprocess.TimeoutExpired:
        print("  TIMEOUT!")
        return {"temps_moyen": -1, "echecs": num_requests}
    except FileNotFoundError:
        print("ERREUR: Apache Bench (ab) non installé!")
        print("  Ubuntu/Debian: sudo apt-get install apache2-utils")
        sys.exit(1)
    except Exception as e:
        print(f"  Erreur: {e}")
        return {"temps_moyen": -1, "echecs": num_requests}


def append_csv(results: list, csv_path: str, write_header: bool = False):
    """Ajoute des résultats à un fichier CSV."""
    mode = "w" if write_header else "a"
    file_exists = os.path.exists(csv_path) and os.path.getsize(csv_path) > 0
    
    with open(csv_path, mode, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["PARAM", "AVG_TIME", "RUN", "FAILED"])
        if write_header or (mode == "a" and not file_exists):
            writer.writeheader()
        writer.writerows(results)


def write_csv(results: list, csv_path: str):
    """Écrit les résultats dans un fichier CSV (écrase si existe)."""
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["PARAM", "AVG_TIME", "RUN", "FAILED"])
        writer.writeheader()
        writer.writerows(results)
    print(f"  Résultats sauvegardés: {csv_path}")


# =============================================================================
# TEST CONCURRENCE
# =============================================================================

def test_conc(url: str, output_dir: str, prefix: str = "user"):
    """
    Test de montée en charge sur la concurrence.
    Config: 1000 users, 50 posts/user, 20 followers
    Variable: utilisateurs simultanés (1, 10, 20, 50, 100, 1000)
    """
    print("\n" + "=" * 60)
    print("TEST CONCURRENCE")
    print("=" * 60)
    
    concurrences = [1, 10, 20, 50, 100, 1000]
    results = []
    
    for conc in concurrences:
        print(f"\n--- {conc} utilisateurs simultanés ---")
        
        for run in range(1, NB_RUNS + 1):
            user = f"{prefix}{random.randint(1, NB_USERS)}"
            nb_requetes = max(100, conc * 10)
            
            print(f"  Run {run}/{NB_RUNS}: {nb_requetes} req, user={user}...", end=" ", flush=True)
            
            metrics = run_ab(url, nb_requetes, conc, user)
            
            print(f"Temps={metrics['temps_moyen']}ms, Échecs={metrics['echecs']}")
            
            results.append({
                "PARAM": conc,
                "AVG_TIME": f"{metrics['temps_moyen']}ms",
                "RUN": run,
                "FAILED": 1 if metrics['echecs'] > 0 else 0
            })
            
            time.sleep(2)  # Pause entre les runs
    
    write_csv(results, os.path.join(output_dir, "conc.csv"))
    return results


# =============================================================================
# TEST POSTS
# =============================================================================

def test_post_single(url: str, output_dir: str, posts_per_user: int, prefix: str = "user"):
    """
    Test pour une configuration de posts donnée.
    Ajoute les résultats au fichier post.csv existant.
    """
    print(f"\n--- Config: {posts_per_user} posts/user ---")
    
    results = []
    
    for run in range(1, NB_RUNS + 1):
        user = f"{prefix}{random.randint(1, NB_USERS)}"
        nb_requetes = 500
        
        print(f"  Run {run}/{NB_RUNS}: {nb_requetes} req, conc={CONCURRENCE_FIXE}...", end=" ", flush=True)
        
        metrics = run_ab(url, nb_requetes, CONCURRENCE_FIXE, user)
        
        print(f"Temps={metrics['temps_moyen']}ms, Échecs={metrics['echecs']}")
        
        results.append({
            "PARAM": posts_per_user,
            "AVG_TIME": f"{metrics['temps_moyen']}ms",
            "RUN": run,
            "FAILED": 1 if metrics['echecs'] > 0 else 0
        })
        
        time.sleep(2)
    
    # Append au CSV existant
    csv_path = os.path.join(output_dir, "post.csv")
    append_csv(results, csv_path)
    print(f"  Résultats ajoutés à: {csv_path}")
    
    return results


# =============================================================================
# TEST FANOUT
# =============================================================================

def test_fanout_single(url: str, output_dir: str, followers: int, prefix: str = "user"):
    """
    Test pour une configuration de followers donnée.
    Ajoute les résultats au fichier fanout.csv existant.
    """
    print(f"\n--- Config: {followers} followers ---")
    
    results = []
    
    for run in range(1, NB_RUNS + 1):
        user = f"{prefix}{random.randint(1, NB_USERS)}"
        nb_requetes = 500
        
        print(f"  Run {run}/{NB_RUNS}: {nb_requetes} req, conc={CONCURRENCE_FIXE}...", end=" ", flush=True)
        
        metrics = run_ab(url, nb_requetes, CONCURRENCE_FIXE, user)
        
        print(f"Temps={metrics['temps_moyen']}ms, Échecs={metrics['echecs']}")
        
        results.append({
            "PARAM": followers,
            "AVG_TIME": f"{metrics['temps_moyen']}ms",
            "RUN": run,
            "FAILED": 1 if metrics['echecs'] > 0 else 0
        })
        
        time.sleep(2)
    
    # Append au CSV existant
    csv_path = os.path.join(output_dir, "fanout.csv")
    append_csv(results, csv_path)
    print(f"  Résultats ajoutés à: {csv_path}")
    
    return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Benchmark TinyInsta")
    parser.add_argument("--url", required=True, help="URL de l'app (ex: https://app.appspot.com)")
    parser.add_argument("--test", choices=["conc", "post", "fanout", "all"], default="all",
                        help="Type de test à exécuter")
    parser.add_argument("--output", default="out", help="Dossier de sortie")
    
    # Options pour tests individuels (utilisé par Snakefile)
    parser.add_argument("--posts", type=int, help="Nb posts/user pour test post")
    parser.add_argument("--followers", type=int, help="Nb followers pour test fanout")
    parser.add_argument("--prefix", default="user", help="Préfixe des users")
    
    args = parser.parse_args()
    
    # Créer le dossier de sortie
    os.makedirs(args.output, exist_ok=True)
    
    print("=" * 60)
    print("BENCHMARK TINYINSTA")
    print(f"URL: {args.url}")
    print(f"Test: {args.test}")
    print("=" * 60)
    
    # Vérifier Apache Bench
    try:
        subprocess.run(["ab", "-V"], capture_output=True, check=True)
    except FileNotFoundError:
        print("\nERREUR: Apache Bench (ab) non installé!")
        print("  Ubuntu/Debian: sudo apt-get install apache2-utils")
        print("  MacOS: brew install httpd")
        sys.exit(1)
    
    # Exécuter le test demandé
    if args.test == "conc":
        test_conc(args.url, args.output, args.prefix)
    
    elif args.test == "post":
        if args.posts:
            # Mode single config (appelé par Snakefile)
            test_post_single(args.url, args.output, args.posts, args.prefix)
        else:
            print("ERREUR: --posts requis pour test post")
            sys.exit(1)
    
    elif args.test == "fanout":
        if args.followers:
            # Mode single config (appelé par Snakefile)
            test_fanout_single(args.url, args.output, args.followers, args.prefix)
        else:
            print("ERREUR: --followers requis pour test fanout")
            sys.exit(1)
    
    elif args.test == "all":
        print("\nPour lancer tous les tests, utilisez le Snakefile:")
        print("  snakemake -j1")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("TERMINÉ!")
    print("=" * 60)


if __name__ == "__main__":
    main()
