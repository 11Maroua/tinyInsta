# =============================================================================
# SNAKEFILE - Benchmark TinyInsta avec LOCUST
# =============================================================================

APP_URL = "https://tinyinsta-480307.lm.r.appspot.com"
NB_USERS = 1000

rule all:
    input:
        "out/conc.png",
        "out/post.png",
        "out/fanout.png"

# =============================================================================
# TEST 1: CONCURRENCE
# =============================================================================

rule test_conc:
    output:
        "out/conc.csv"
    shell:
        """
        mkdir -p out
        echo ">>> TEST CONCURRENCE"
        python clear_datastore.py
        python seed.py --users 1000 --posts 50000 --follows 20
        sleep 30
        python benchmark.py --url {APP_URL} --test conc --output out
        """

rule plot_conc:
    input: "out/conc.csv"
    output: "out/conc.png"
    shell: "python generate_plots.py --input out --output out --only conc"

# =============================================================================
# TEST 2: NOMBRE DE POSTS
# =============================================================================

rule test_post:
    output:
        "out/post.csv"
    shell:
        """
        mkdir -p out
        echo "PARAM,AVG_TIME,RUN,FAILED" > out/post.csv
        
        echo ">>> [1/3] Config: 10 posts/user"
        python clear_datastore.py
        python seed.py --users 1000 --posts 10000 --follows 20
        sleep 30
        python benchmark.py --url {APP_URL} --test post --posts 10 --output out
        
        echo ">>> [2/3] Config: 100 posts/user"
        python clear_datastore.py
        python seed.py --users 1000 --posts 100000 --follows 20
        sleep 30
        python benchmark.py --url {APP_URL} --test post --posts 100 --output out
        
        echo ">>> [3/3] Config: 1000 posts/user"
        python clear_datastore.py
        python seed.py --users 1000 --posts 1000000 --follows 20
        sleep 60
        python benchmark.py --url {APP_URL} --test post --posts 1000 --output out
        """

rule plot_post:
    input: "out/post.csv"
    output: "out/post.png"
    shell: "python generate_plots.py --input out --output out --only post"

# =============================================================================
# TEST 3: FANOUT
# =============================================================================

rule test_fanout:
    output:
        "out/fanout.csv"
    shell:
        """
        mkdir -p out
        echo "PARAM,AVG_TIME,RUN,FAILED" > out/fanout.csv
        
        echo ">>> [1/3] Config: 10 followers"
        python clear_datastore.py
        python seed.py --users 1000 --posts 100000 --follows 10
        sleep 30
        python benchmark.py --url {APP_URL} --test fanout --followers 10 --output out
        
        echo ">>> [2/3] Config: 50 followers"
        python clear_datastore.py
        python seed.py --users 1000 --posts 100000 --follows 50
        sleep 30
        python benchmark.py --url {APP_URL} --test fanout --followers 50 --output out
        
        echo ">>> [3/3] Config: 100 followers"
        python clear_datastore.py
        python seed.py --users 1000 --posts 100000 --follows 100
        sleep 30
        python benchmark.py --url {APP_URL} --test fanout --followers 100 --output out
        """

rule plot_fanout:
    input: "out/fanout.csv"
    output: "out/fanout.png"
    shell: "python generate_plots.py --input out --output out --only fanout"

rule clean:
    shell: "rm -rf out/ && mkdir -p out"
