#!/usr/bin/env python3
"""
Génère les graphiques barplot à partir des fichiers CSV de benchmark.

Usage:
    python generate_plots.py                    # Tous les graphiques
    python generate_plots.py --only conc        # Seulement conc.png
    python generate_plots.py --only post        # Seulement post.png
    python generate_plots.py --only fanout      # Seulement fanout.png
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import argparse
import os
import sys


def parse_temps(valeur):
    """Convertit '123.45ms' en float en secondes (0.12345)"""
    if isinstance(valeur, str):
        return float(valeur.replace('ms', '')) / 1000.0  # Conversion ms -> s
    return float(valeur) / 1000.0


def creer_barplot(csv_path: str, output_path: str, titre: str, label_x: str):
    """Crée un barplot avec barres d'erreur à partir d'un CSV."""
    
    # Charger les données
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Erreur lecture {csv_path}: {e}")
        return False
    
    if df.empty:
        print(f"Fichier vide: {csv_path}")
        return False
    
    df['TEMPS_MS'] = df['AVG_TIME'].apply(parse_temps)
    
    # Moyenne et écart-type par PARAM
    stats = df.groupby('PARAM')['TEMPS_MS'].agg(['mean', 'std']).reset_index()
    stats.columns = ['PARAM', 'moyenne', 'ecart_type']
    stats['ecart_type'] = stats['ecart_type'].fillna(0)
    
    # Trier par PARAM
    stats = stats.sort_values('PARAM')
    
    # Figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(stats))
    largeur = 0.6
    
    # Barres avec erreur
    barres = ax.bar(
        x, 
        stats['moyenne'], 
        largeur, 
        yerr=stats['ecart_type'],
        capsize=5,
        color='#4285F4',
        edgecolor='black', 
        linewidth=1.2,
        error_kw={'elinewidth': 2, 'capthick': 2}
    )
    
    # Labels
    ax.set_xlabel(label_x, fontsize=12, fontweight='bold')
    ax.set_ylabel('Temps moyen par requête (s)', fontsize=12, fontweight='bold')
    ax.set_title(titre, fontsize=14, fontweight='bold', pad=20)
    
    ax.set_xticks(x)
    ax.set_xticklabels(stats['PARAM'].astype(int).astype(str), fontsize=11)
    
    ax.yaxis.grid(True, linestyle='--', alpha=0.7)
    ax.set_axisbelow(True)
    
    # Valeurs sur les barres
    for barre, moy, std in zip(barres, stats['moyenne'], stats['ecart_type']):
        hauteur = barre.get_height()
        offset = std + (hauteur * 0.05) if std > 0 else hauteur * 0.05
        ax.annotate(
            f'{moy:.2f}s',
            xy=(barre.get_x() + barre.get_width() / 2, hauteur + offset),
            ha='center', 
            va='bottom', 
            fontsize=10, 
            fontweight='bold'
        )
    
    # Ajuster les marges
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Graphique créé: {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Génère les graphiques de benchmark")
    parser.add_argument("--input", default="out", help="Dossier des CSV")
    parser.add_argument("--output", default="out", help="Dossier de sortie")
    parser.add_argument("--only", choices=["conc", "post", "fanout"], 
                        help="Générer un seul graphique")
    
    args = parser.parse_args()
    
    os.makedirs(args.output, exist_ok=True)
    
    print("=" * 60)
    print("GÉNÉRATION DES GRAPHIQUES")
    print("=" * 60)
    
    success = True
    
    # Graphique Concurrence
    if args.only is None or args.only == "conc":
        conc_csv = os.path.join(args.input, "conc.csv")
        if os.path.exists(conc_csv):
            ok = creer_barplot(
                conc_csv,
                os.path.join(args.output, "conc.png"),
                "Temps moyen par requête selon la concurrence",
                "Nombre d'utilisateurs concurrents"
            )
            success = success and ok
        else:
            print(f"Fichier non trouvé: {conc_csv}")
            success = False
    
    # Graphique Posts
    if args.only is None or args.only == "post":
        post_csv = os.path.join(args.input, "post.csv")
        if os.path.exists(post_csv):
            ok = creer_barplot(
                post_csv,
                os.path.join(args.output, "post.png"),
                "Temps moyen par requête selon le nombre de posts",
                "Nombre de posts par utilisateur"
            )
            success = success and ok
        else:
            print(f"Fichier non trouvé: {post_csv}")
            success = False
    
    # Graphique Fanout
    if args.only is None or args.only == "fanout":
        fanout_csv = os.path.join(args.input, "fanout.csv")
        if os.path.exists(fanout_csv):
            ok = creer_barplot(
                fanout_csv,
                os.path.join(args.output, "fanout.png"),
                "Temps moyen par requête selon le nombre de followers",
                "Nombre de followers par utilisateur"
            )
            success = success and ok
        else:
            print(f"Fichier non trouvé: {fanout_csv}")
            success = False
    
    print("\n" + "=" * 60)
    if success:
        print("TERMINÉ AVEC SUCCÈS!")
    else:
        print("TERMINÉ AVEC DES ERREURS")
    print("=" * 60)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()