# TinyInsta Benchmark

Projet de benchmark pour l'application TinyInsta déployée sur Google App Engine.

## Application déployée

🔗 **https://tinyints.ew.r.appspot.com**

## Résultats des benchmarks

### Test 1 : Passage à l'échelle sur la concurrence

Configuration : 1000 utilisateurs, 50 posts/utilisateur, 20 followers/utilisateur

![Concurrence](out/conc.png)

### Test 2 : Passage à l'échelle sur le nombre de posts

Configuration : 1000 utilisateurs, 50 requêtes simultanées, 20 followers/utilisateur

![Posts](out/post.png)

### Test 3 : Passage à l'échelle sur le fanout (followers)

Configuration : 1000 utilisateurs, 50 requêtes simultanées, 100 posts/utilisateur

![Fanout](out/fanout.png)

## Exécution des benchmarks

### Prérequis

```bash
# Installer les dépendances
pip install pandas matplotlib requests google-cloud-datastore snakemake

# Installer Apache Bench
sudo apt-get install apache2-utils

# Configurer gcloud
gcloud auth application-default login
```

### Lancer tous les tests

```bash
snakemake -j1
```

### Lancer un test spécifique

```bash
# Test concurrence uniquement
snakemake out/conc.png -j1

# Test posts uniquement
snakemake out/post.png -j1

# Test fanout uniquement
snakemake out/fanout.png -j1
```

### Commandes utiles

```bash
# Voir ce qui sera exécuté (dry-run)
snakemake -n

# Nettoyer les fichiers locaux
snakemake clean

# Vider le Datastore manuellement
python clear_datastore.py
```

## Méthodologie

### Workflow

Pour chaque configuration de test :
1. **Vidage** du Datastore (User + Post)
2. **Seed** des données via l'endpoint `/admin/seed`
3. **Attente** de 30s pour la propagation (eventual consistency)
4. **Benchmark** avec Apache Bench (3 runs par configuration)

### Configurations testées

| Test | Users | Posts/user | Followers | Concurrent | Variable |
|------|-------|------------|-----------|------------|----------|
| Conc | 1000 | 50 | 20 | 1→1000 | Concurrence |
| Post | 1000 | 10→1000 | 20 | 50 | Nb posts |
| Fanout | 1000 | 100 | 10→100 | 50 | Nb followers |

### Mesures

- **Temps moyen** : `Time per request (mean)` de Apache Bench
- **3 runs** par configuration pour calculer la variance
- **Échecs** : comptage des requêtes non-2xx

## Notes techniques

### Pourquoi vider la base entre chaque config ?

- Évite l'accumulation de données qui fausse les résultats
- Garantit des conditions de test reproductibles
- Réduit les coûts de stockage Datastore

### Eventual consistency

Le Datastore utilise un modèle de consistance éventuelle pour les requêtes globales.
Un délai de 30s est ajouté après chaque seed pour laisser les données se propager.

### Limitation seed 1M posts

Le seed de 1 000 000 de posts (test 1000 posts/user) peut prendre plusieurs heures.
Si timeout, utiliser le script `seed.py` en local :

```bash
python seed.py --users 1000 --posts 1000000 --follows-min 20 --follows-max 20
```

