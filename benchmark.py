#!/usr/bin/env python3
"""
Benchmark TinyInsta avec Locust.

Usage:
    python benchmark.py --url https://APP.appspot.com --test conc --output out
    python benchmark.py --url https://APP.appspot.com --test post --posts 100 --output out
    python benchmark.py --url https://APP.appspot.com --test fanout --followers 50 --output out
"""

import subprocess
import re
import csv
import os
import argparse
import time
import sys


# Configuration
NB_USERS = 1000
NB_RUNS = 3
CONCURRENCE_FIXE = 50
TEST_DURATION = 60


def run_locust(url: str, num_users: int, duration: int = 60) -> dict:
    spawn_rate = min(num_users, 10)
    
    cmd = [
        "locust",
        "-f", "locustfile.py",
        "--headless",
        "--host", url,
        "-u", str(num_users),
        "-r", str(spawn_rate),
        "--run-time", f"{duration}s",
        "--only-summary",
        "--stop-timeout", "10"
    ]
    
    try:
        print(f"  Locust: {num_users} users, {duration}s...", end=" ", flush=True)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 30)
        output = result.stdout + result.stderr
        
        temps_moyen = 0
        echecs = 0
        
        # Parser statistiques sortie Locust
        lines = output.split('\n')
        for line in lines:
            if '/api/timeline' in line and 'GET' in line:
                parts = line.split()
                try:
                    if len(parts) >= 7:
                        echecs = int(parts[3])
                        temps_moyen = float(parts[4])
                        break
                except (ValueError, IndexError):
                    continue
        
        # gérer échecs
        if temps_moyen == 0:
            match = re.search(r'Average.*?(\d+\.?\d*)\s*ms', output, re.IGNORECASE)
            if match:
                temps_moyen = float(match.group(1))
            match = re.search(r'(\d+)\s+failed', output, re.IGNORECASE)
            if match:
                echecs = int(match.group(1))
        
        print(f"Avg={temps_moyen}ms, Échecs={echecs}")
        return {"temps_moyen": round(temps_moyen, 2), "echecs": echecs}
        
    except subprocess.TimeoutExpired:
        print("TIMEOUT!")
        return {"temps_moyen": -1, "echecs": -1}
    except FileNotFoundError:
        print("\n❌ Locust non installé! Installez: pip install locust")
        sys.exit(1)
    except Exception as e:
        print(f"Erreur: {e}")
        return {"temps_moyen": -1, "echecs": -1}


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
    """Écrit les résultats dans un fichier CSV """
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["PARAM", "AVG_TIME", "RUN", "FAILED"])
        writer.writeheader()
        writer.writerows(results)
    print(f"  Résultats sauvegardés: {csv_path}")


# =============================================================================
# TEST CONCURRENCE
# =============================================================================

def test_conc(url: str, output_dir: str, prefix: str = "user"):
    print("\n" + "=" * 60)
    print("TEST CONCURRENCE ")
    print("=" * 60)
    
    concurrences = [1, 10, 20, 50, 100, 1000]
    results = []
    
    for conc in concurrences:
        print(f"\n--- {conc} utilisateurs simultanés ---")
        
        for run in range(1, NB_RUNS + 1):
            print(f"  Run {run}/{NB_RUNS}:", end=" ", flush=True)
            
            duration = 60 if conc >= 50 else 30
            metrics = run_locust(url, conc, duration)
            
            results.append({
                "PARAM": conc,
                "AVG_TIME": f"{metrics['temps_moyen']}ms",
                "RUN": run,
                "FAILED": 1 if metrics['echecs'] > 0 else 0
            })
            
            time.sleep(5)
    
    write_csv(results, os.path.join(output_dir, "conc.csv"))
    return results


# =============================================================================
# TEST POSTS
# =============================================================================

def test_post_single(url: str, output_dir: str, posts_per_user: int, prefix: str = "user"):
    """Test pour une configuration de posts donnée."""
    print(f"\n--- Config: {posts_per_user} posts/user ---")
    
    results = []
    
    for run in range(1, NB_RUNS + 1):
        print(f"  Run {run}/{NB_RUNS}:", end=" ", flush=True)
        
        metrics = run_locust(url, CONCURRENCE_FIXE, TEST_DURATION)
        
        results.append({
            "PARAM": posts_per_user,
            "AVG_TIME": f"{metrics['temps_moyen']}ms",
            "RUN": run,
            "FAILED": 1 if metrics['echecs'] > 0 else 0
        })
        
        time.sleep(5)
    
    csv_path = os.path.join(output_dir, "post.csv")
    append_csv(results, csv_path)
    print(f"  Résultats ajoutés: {csv_path}")
    
    return results


# =============================================================================
# TEST FANOUT
# =============================================================================

def test_fanout_single(url: str, output_dir: str, followers: int, prefix: str = "user"):
    """Test pour une configuration de followers donnée."""
    print(f"\n--- Config: {followers} followers ---")
    
    results = []
    
    for run in range(1, NB_RUNS + 1):
        print(f"  Run {run}/{NB_RUNS}:", end=" ", flush=True)
        
        metrics = run_locust(url, CONCURRENCE_FIXE, TEST_DURATION)
        
        results.append({
            "PARAM": followers,
            "AVG_TIME": f"{metrics['temps_moyen']}ms",
            "RUN": run,
            "FAILED": 1 if metrics['echecs'] > 0 else 0
        })
        
        time.sleep(5)
    
    csv_path = os.path.join(output_dir, "fanout.csv")
    append_csv(results, csv_path)
    print(f"  Résultats ajoutés: {csv_path}")
    
    return results


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Benchmark TinyInsta avec Locust")
    parser.add_argument("--url", required=True, help="URL de l'app")
    parser.add_argument("--test", choices=["conc", "post", "fanout", "all"], default="all")
    parser.add_argument("--output", default="out", help="Dossier de sortie")
    parser.add_argument("--posts", type=int, help="Nb posts/user (pour test post)")
    parser.add_argument("--followers", type=int, help="Nb followers (pour test fanout)")
    parser.add_argument("--prefix", default="user", help="Préfixe des users")
    
    args = parser.parse_args()
    
    os.makedirs(args.output, exist_ok=True)
    
    print("=" * 60)
    print("BENCHMARK TINYINSTA")
    print(f"URL: {args.url}")
    print(f"Test: {args.test}")
    print("=" * 60)
    
    # Vérifier locustfile.py
    if not os.path.exists("locustfile.py"):
        print("\n❌ ERREUR: locustfile.py introuvable!")
        sys.exit(1)
    
    if args.test == "conc":
        test_conc(args.url, args.output, args.prefix)
    elif args.test == "post":
        if not args.posts:
            print("❌ ERREUR: --posts requis")
            sys.exit(1)
        test_post_single(args.url, args.output, args.posts, args.prefix)
    elif args.test == "fanout":
        if not args.followers:
            print("❌ ERREUR: --followers requis")
            sys.exit(1)
        test_fanout_single(args.url, args.output, args.followers, args.prefix)
    elif args.test == "all":
        print("\nPour lancer tous les tests, utilisez: snakemake -j1")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("TERMINÉ!")
    print("=" * 60)


if __name__ == "__main__":
    main()
