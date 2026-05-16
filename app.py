import base64
import io
import itertools
import math
import os
import random
import time
import json
import concurrent.futures
import datetime
import hashlib

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from PIL import Image

st.set_page_config(page_title="СР1 — Розподілене ранжування", layout="wide")

DOMAIN_1 = {
    "name": "Астрономічні об'єкти",
    "objects": [
        {"name": "Sirius",      "img": "images/sirius.jpg"},
        {"name": "Black Hole",  "img": "images/blackhole.jpg"},
        {"name": "Mercury",     "img": "images/mercury.jpg"},
        {"name": "Venus",       "img": "images/venus.jpg"},
        {"name": "Andromeda",   "img": "images/andromeda.jpg"},
        {"name": "Earth",       "img": "images/earth.jpg"},
        {"name": "Mars",        "img": "images/mars.jpg"},
        {"name": "Wormhole",    "img": "images/wormholes.jpg"},
        {"name": "Jupiter",     "img": "images/jupiter.jpg"},
        {"name": "Saturn",      "img": "images/saturn.jpg"},
        {"name": "Uranus",      "img": "images/uranus.jpg"},
        {"name": "Neptune",     "img": "images/neptune.jpg"},
        {"name": "Pluto",       "img": "images/pluto.jpg"},
        {"name": "Moon",        "img": "images/moon.jpg"},
        {"name": "Europa",      "img": "images/europa.jpg"},
        {"name": "Titan",       "img": "images/titan.jpg"},
        {"name": "Milky Way",   "img": "images/milkyway.jpg"},
        {"name": "Callisto",    "img": "images/callisto.jpg"},
        {"name": "Sun",         "img": "images/sun.jpg"},
        {"name": "Comet",       "img": "images/comet.jpg"},
    ]
}

DOMAIN_2 = {
    "name": "Коштовне каміння",
    "objects": [
        {"name": "Діамант", "img": ""}, {"name": "Рубін", "img": ""},
        {"name": "Сапфір", "img": ""}, {"name": "Смарагд", "img": ""},
        {"name": "Аметист", "img": ""}, {"name": "Топаз", "img": ""},
        {"name": "Опал", "img": ""}, {"name": "Аквамарин", "img": ""},
        {"name": "Перлина", "img": ""}, {"name": "Гранат", "img": ""},
        {"name": "Нефрит", "img": ""}, {"name": "Бірюза", "img": ""},
        {"name": "Онікс", "img": ""}, {"name": "Ляпіс-лазур", "img": ""},
        {"name": "Бурштин", "img": ""}, {"name": "Турмалін", "img": ""},
        {"name": "Циркон", "img": ""}, {"name": "Шпінель", "img": ""},
        {"name": "Місячний камінь", "img": ""}, {"name": "Малахіт", "img": ""}
    ]
}

DOMAINS = {"Астрономічні об'єкти": DOMAIN_1, "Коштовне каміння": DOMAIN_2}
CUSTOM_DOMAIN_FILE = "custom_domain.json"
if os.path.exists(CUSTOM_DOMAIN_FILE):
    with open(CUSTOM_DOMAIN_FILE, "r", encoding="utf-8") as f:
        try:
            custom_domain_data = json.load(f)
            DOMAINS[custom_domain_data["name"]] = custom_domain_data
        except Exception as e:
            st.error(f"Помилка читання власної області: {e}")
DOMAINS = {
    "Астрономічні об'єкти": DOMAIN_1,
    "Коштовне каміння": DOMAIN_2
}

EXPERTS = [
    "Вiка","Анна","Іван","Ромчик","Анастасiя","Лiза","Валерiя","Лера","Даша",
    "Настя","Максим","Веронiка","Вiкторiя","Дарина","Марина","Anastasiia",
    "Михайло","Дарiя","хтось","Оскар","Викладач",
]

HEURISTICS = {
    "E1": "Об'єкт обирався 1 раз на 3-му місці",
    "E2": "Об'єкт обирався 1 раз на 2-му місці",
    "E3": "Об'єкт обирався 1 раз на 1-му місці",
    "E4": "Об'єкт обирався 2 рази на 3-му місці",
    "E5": "Об'єкт обирався 2 рази, один раз на 3-му і один раз на 2-му місці",
    "E6": "Сума балів <= 3",
    "E7": "Об'єкт жодного разу не обирався на 1-му місці",
}
CUSTOM_DOMAIN_FILE = "custom_domain.json"
if os.path.exists(CUSTOM_DOMAIN_FILE):
    with open(CUSTOM_DOMAIN_FILE, "r", encoding="utf-8") as f:
        try:
            custom_domain_data = json.load(f)
            DOMAINS[custom_domain_data["name"]] = custom_domain_data
        except:
            pass

ADMIN_PASSWORD = "admin123"

# файли даних
H_VOTES_FILE = "heuristic_votes.csv"
LOG_FILE     = "protocol.log"
DOMAIN_FILE  = "current_domain.json"

# ─────────────────────────────────────────────
# ПРОТОКОЛЮВАННЯ (завдання 3)
# ─────────────────────────────────────────────
def log_action(role: str, action: str):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] [{role}] {action}\n")

# ─────────────────────────────────────────────
# ЗБЕРЕЖЕННЯ / ЗАВАНТАЖЕННЯ ПРЕДМЕТНОЇ ОБЛАСТІ (завдання 1)
# ─────────────────────────────────────────────
def save_domain(domain_name: str):
    with open(DOMAIN_FILE, "w", encoding="utf-8") as f:
        json.dump({"domain": domain_name}, f)

def load_domain_name() -> str:
    if os.path.exists(DOMAIN_FILE):
        with open(DOMAIN_FILE, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("domain", "Астрономічні об'єкти")
    return "Астрономічні об'єкти"

# ─────────────────────────────────────────────
# ПОЧАТКОВІ ДАНІ (насіннєві голоси за евристики)
# ─────────────────────────────────────────────
SEED_H_VOTES = [
    ("Вiка","E7","E6","E1"),("Анна","E6","E7","E2"),("Іван","E7","E1","E4"),
    ("Ромчик","E6","E4","E5"),("Анастасiя","E7","E5","E6"),("Лiза","E1","E6","E7"),
    ("Валерiя","E6","E7","E3"),("Лера","E7","E2","E6"),("Даша","E6","E1","E7"),
    ("Настя","E7","E6","E4"),("Максим","E6","E5","E7"),("Веронiка","E7","E6","E1"),
    ("Вiкторiя","E6","E7","E5"),("Дарина","E7","E4","E6"),("Марина","E6","E7","E2"),
    ("Anastasiia","E7","E6","E3"),("Михайло","E6","E1","E7"),("Дарiя","E7","E6","E5"),
    ("хтось","E6","E7","E4"),("Оскар","E7","E5","E6"),
]

def init_h_votes_file():
    if not os.path.exists(H_VOTES_FILE):
        pd.DataFrame(SEED_H_VOTES, columns=["name","h1","h2","h3"]).to_csv(H_VOTES_FILE, index=False)

init_h_votes_file()

# ─────────────────────────────────────────────
# ФОН
# ─────────────────────────────────────────────
def set_bg(gif_path):
    if not os.path.exists(gif_path):
        return
    with open(gif_path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode()
    st.markdown(f"""<style>
[data-testid="stAppViewContainer"]{{background-image:url("data:image/gif;base64,{b64}");background-size:cover;background-repeat:no-repeat;background-attachment:fixed;}}
.block-container{{background-color:rgba(0,0,0,.68);border-radius:20px;padding:2rem;margin-top:2rem;}}
h1,h2,h3,h4,h5,h6{{color:#00FFFF;}}
.stButton>button{{background:linear-gradient(90deg,#4B0082,#00008B);color:white;font-weight:bold;border-radius:10px;transition:all .3s ease;}}
.stButton>button:hover{{transform:scale(1.05);box-shadow:0 0 6px #8A2BE2,0 0 22px #1E90FF;}}
</style>""", unsafe_allow_html=True)

set_bg("images/starfield.gif")

# ─────────────────────────────────────────────
# ДОПОМІЖНІ ФУНКЦІЇ
# ─────────────────────────────────────────────
def load_scores(votes_file, objects):
    obj_names = [o["name"] for o in objects]
    scores = {o: 0 for o in obj_names}
    counts = {o: {"c1": 0, "c2": 0, "c3": 0} for o in obj_names}
    if not os.path.exists(votes_file):
        return scores, counts
    df = pd.read_csv(votes_file)
    for _, row in df.iterrows():
        for col, pts, key in [("choice1", 3, "c1"), ("choice2", 2, "c2"), ("choice3", 1, "c3")]:
            obj = str(row.get(col, "")).strip()
            if obj in scores:
                scores[obj] += pts
                counts[obj][key] += 1
    return scores, counts

def goodfor_heuristic(obj, key, counts, scores):
    c = counts[obj]; total = c["c1"] + c["c2"] + c["c3"]
    if key == "E1": return total == 1 and c["c3"] == 1
    if key == "E2": return total == 1 and c["c2"] == 1
    if key == "E3": return total == 1 and c["c1"] == 1
    if key == "E4": return total == 2 and c["c3"] == 2
    if key == "E5": return total == 2 and c["c3"] == 1 and c["c2"] == 1 and c["c1"] == 0
    if key == "E6": return scores[obj] <= 3
    if key == "E7": return c["c1"] == 0
    return False

def load_h_votes():
    if not os.path.exists(H_VOTES_FILE):
        return pd.DataFrame(columns=["name", "h1", "h2", "h3"])
    return pd.read_csv(H_VOTES_FILE)

def ranked_heuristics_from_votes(df_h):
    h_scores = {k: 0 for k in HEURISTICS}
    for _, row in df_h.iterrows():
        for col, pts in [("h1", 3), ("h2", 2), ("h3", 1)]:
            k = str(row.get(col, "")).strip()
            if k in h_scores:
                h_scores[k] += pts
    return sorted(h_scores.items(), key=lambda x: -x[1])

def apply_heuristicsStep(objects_list, heuristics_order, counts, scores):
    current = list(objects_list); log = []
    for h_key in heuristics_order:
        if len(current) <= 10:
            break
        removed = [o for o in current if goodfor_heuristic(o, h_key, counts, scores)]
        if removed:
            current = [o for o in current if o not in removed]
            log.append({"Евристика": h_key, "Опис": HEURISTICS[h_key],
                        "Видалено": ", ".join(removed) if removed else "—",
                        "Залишилось": len(current)})
    return current, log

def cook_distance_e1(ranks_vec, triple):
    _, o1, o2, o3 = triple
    pos = {o: i for i, o in enumerate(ranks_vec)}
    chosen = [o for o in [o1, o2, o3] if o in pos]
    if not chosen: return 0
    sorted_chosen = sorted(chosen, key=lambda o: pos[o])
    rel_rank = {o: i + 1 for i, o in enumerate(sorted_chosen)}
    d = 0
    for expert_rank, obj in enumerate([o1, o2, o3], start=1):
        if obj in rel_rank:
            d += abs(expert_rank - rel_rank[obj])
    return d

def cook_distance_e2(ranks_vec, triple):
    _, o1, o2, o3 = triple
    pos = {o: i + 1 for i, o in enumerate(ranks_vec)}
    d = 0
    for ideal_rank, obj in enumerate([o1, o2, o3], start=1):
        if obj in pos:
            d += abs(ideal_rank - pos[obj])
    return d

def brute_force_median(objects_subset, triples, heuristic="E1",
                       pause_event=None, resume_event=None, progress_placeholder=None):
    dist_fn = cook_distance_e1 if heuristic == "E1" else cook_distance_e2
    min_sum = float("inf"); min_max = float("inf")
    best_perms_sum = []; best_perms_max = []
    sample_rows = []
    all_perms = list(itertools.permutations(objects_subset))
    total = len(all_perms)
    for idx, perm in enumerate(all_perms):
        # управління обчисленнями (завдання 7)
        if pause_event and pause_event.is_set():
            if resume_event:
                resume_event.wait()
        p_list = list(perm)
        dists = [dist_fn(p_list, t) for t in triples]
        s = sum(dists); m = max(dists) if dists else 0
        if idx < 50:
            row = {"№": idx + 1, "Перестановка": " > ".join(p_list)}
            for i, d in enumerate(dists): row[f"d{i+1}"] = d
            row["Сума"] = s; row["Макс"] = m
            sample_rows.append(row)
        if s < min_sum: min_sum = s; best_perms_sum = [p_list]
        elif s == min_sum: best_perms_sum.append(p_list)
        if m < min_max: min_max = m; best_perms_max = [p_list]
        elif m == min_max: best_perms_max.append(p_list)
        if progress_placeholder and idx % max(1, total // 100) == 0:
            progress_placeholder.progress((idx + 1) / total)
    return best_perms_sum, best_perms_max, min_sum, min_max, sample_rows

def restore_ranking(perms, objects_subset):
    rows = [{o: i + 1 for i, o in enumerate(perm)} for perm in perms]
    return pd.DataFrame(rows, columns=objects_subset)

def build_preference_matrix(triples, objects_subset):
    idx = {o: i for i, o in enumerate(objects_subset)}
    M = [[0] * len(objects_subset) for _ in range(len(objects_subset))]
    for _, o1, o2, o3 in triples:
        for winner, losers in [(o1, [o2, o3]), (o2, [o3])]:
            if winner in idx:
                for loser in losers:
                    if loser in idx:
                        M[idx[winner]][idx[loser]] += 1
    return pd.DataFrame(M, index=objects_subset, columns=objects_subset)

def build_rank_matrix(triples, objects_subset):
    rows = [{"Експерт": e, "1-й": o1, "2-й": o2, "3-й": o3} for e, o1, o2, o3 in triples]
    return pd.DataFrame(rows)

def build_expert_stats_table(triples, objects_subset):
    stats = pd.DataFrame(0, index=["1", "2", "3", "Сума"], columns=objects_subset)
    for _, o1, o2, o3 in triples:
        if o1 in objects_subset: stats.at["1", o1] += 1
        if o2 in objects_subset: stats.at["2", o2] += 1
        if o3 in objects_subset: stats.at["3", o3] += 1
    stats.loc["Сума"] = stats.iloc[0:3].sum()
    return stats

def load_expert_triples_from_votes(votes_file, objects_subset):
    if not os.path.exists(votes_file): return []
    df = pd.read_csv(votes_file)
    subset_set = set(objects_subset); triples = []
    for _, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        o1 = str(row.get("choice1", "")).strip()
        o2 = str(row.get("choice2", "")).strip()
        o3 = str(row.get("choice3", "")).strip()
        choices = [o for o in [o1, o2, o3] if o in subset_set]
        if len(choices) >= 2:
            while len(choices) < 3: choices.append(choices[-1])
            triples.append((name, choices[0], choices[1], choices[2]))
    return triples

def load_raw_triples(votes_file):
    if not os.path.exists(votes_file): return []
    df = pd.read_csv(votes_file)
    triples = []
    for _, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        o1 = str(row.get("choice1", "")).strip()
        o2 = str(row.get("choice2", "")).strip()
        o3 = str(row.get("choice3", "")).strip()
        triples.append((name, o1, o2, o3))
    return triples

def calculate_satisfaction(raw_triples, consensus_perm):
    n = len(consensus_perm); results = []
    for name, o1, o2, o3 in raw_triples:
        d_j = 0; removed = False
        for r_expert, obj in enumerate([o1, o2, o3], start=1):
            if obj in consensus_perm:
                r_star = consensus_perm.index(obj) + 1
                d_j += abs(r_expert - r_star)
            else:
                removed = True
        if removed: d_j += n - 3
        s_j = (1 - (d_j / ((n - 3) * 3))) * 100 if n > 3 else 100
        s_j = max(0, min(100, s_j))
        results.append({"Експерт": name, "Вибір": f"{o1} > {o2} > {o3}",
                        "Відстань": d_j, "Задоволеність (%)": round(s_j, 2)})
    return pd.DataFrame(results)

def firstdist(perm_a, perm_b):
    return sum(1 for a, b in zip(perm_a, perm_b) if a != b)

def genetic_rank_cook(objects_subset, triples, heuristic="E1",
                      fitness_mode="sum", pop_size=1000, generations=200, mut_rate=0.10):
    n = len(objects_subset)
    dist_fn = cook_distance_e1 if heuristic == "E1" else cook_distance_e2

    def fitness(perm):
        dists = [dist_fn(perm, t) for t in triples]
        return -sum(dists) if fitness_mode == "sum" else -max(dists)

    def crosover(p1, p2):
        a, b = sorted(random.sample(range(n), 2))
        child = [None] * n; child[a:b+1] = p1[a:b+1]
        fill = [x for x in p2 if x not in child]; j = 0
        for i in range(n):
            if child[i] is None: child[i] = fill[j]; j += 1
        return child

    def mutate(perm):
        p = perm[:]
        for i in range(n):
            if random.random() < mut_rate:
                j = random.randint(0, n - 1); p[i], p[j] = p[j], p[i]
        return p

    popul = [random.sample(objects_subset, n) for _ in range(pop_size)]
    best_perm = None; best_fit = float("-inf"); history = []; improve_iters = []; best_solutions = []
    for gen in range(generations):
        ranked_pop = sorted(popul, key=fitness, reverse=True)
        top_fit = fitness(ranked_pop[0])
        if top_fit > best_fit:
            best_fit = top_fit; best_perm = ranked_pop[0][:]
            improve_iters.append(gen + 1); best_solutions = [best_perm[:]]
        elif top_fit == best_fit:
            candidate = ranked_pop[0][:]
            if candidate not in best_solutions: best_solutions.append(candidate)
        history.append(-best_fit)
        survivors = ranked_pop[:pop_size // 2]; new_pop = survivors[:]
        while len(new_pop) < pop_size:
            p1, p2 = random.sample(survivors, 2); new_pop.append(mutate(crosover(p1, p2)))
        popul = new_pop
    return best_perm, -best_fit, history, improve_iters, len(best_solutions)

def generate_mock_data(n_objs=8, n_experts=11, seed=42, objects=None):
    rng = random.Random(seed)
    if objects is None: objects = [o["name"] for o in DOMAIN_1["objects"]]
    test_objs = objects[:n_objs]; test_triples = []
    for i in range(n_experts):
        name = f"Експерт {i+1}"; choice = rng.sample(test_objs, 3)
        test_triples.append((name, choice[0], choice[1], choice[2]))
    return test_objs, test_triples

def process_chunk_global(args):
    chunk, triples = args
    local_min = float("inf"); local_best = []
    for perm in chunk:
        p_list = list(perm)
        s = sum(cook_distance_e2(p_list, t) for t in triples)
        if s < local_min: local_min = s; local_best = [p_list]
        elif s == local_min: local_best.append(p_list)
    return local_min, local_best

def distributed_brute_force_sim(objects_subset, triples, workers=4):
    tasks = []
    for first_obj in objects_subset:
        rem_objs = [o for o in objects_subset if o != first_obj]
        chunk = [(first_obj,) + p for p in itertools.permutations(rem_objs)]
        tasks.append((chunk, triples))
    start = time.time(); results = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        for result in executor.map(process_chunk_global, tasks):
            results.append(result)
    t_dist = time.time() - start
    global_min = float("inf"); global_best = []
    for l_min, l_best in results:
        if l_min < global_min: global_min = l_min; global_best = l_best
        elif l_min == global_min: global_best.extend(l_best)
    return global_best, global_min, t_dist

def genetic_rank(objects_subset, expert_perms, fitness_mode="sum",
                 pop_size=1000, generations=200, mut_rate=0.15):
    n = len(objects_subset)
    if n == 0: return [], 0, [], [], 0

    def fitness(perm):
        dists = [firstdist(perm, exp) for exp in expert_perms]
        return -sum(dists) if fitness_mode == "sum" else -max(dists)

    def crosover(p1, p2):
        a, b = sorted(random.sample(range(n), 2))
        child = [None] * n; child[a:b+1] = p1[a:b+1]
        fill = [x for x in p2 if x not in child]; j = 0
        for i in range(n):
            if child[i] is None: child[i] = fill[j]; j += 1
        return child

    def mutate(perm):
        p = perm[:]
        for i in range(n):
            if random.random() < mut_rate:
                j = random.randint(0, n - 1); p[i], p[j] = p[j], p[i]
        return p

    popul = [random.sample(objects_subset, n) for _ in range(pop_size)]
    best_perm = None; best_fit = float("-inf"); history = []; improve_iters = []; best_solutions = []
    for gen in range(generations):
        ranked_pop = sorted(popul, key=fitness, reverse=True)
        top_fit = fitness(ranked_pop[0])
        if top_fit > best_fit:
            best_fit = top_fit; best_perm = ranked_pop[0][:]
            improve_iters.append(gen + 1); best_solutions = [best_perm[:]]
        elif top_fit == best_fit:
            candidate = ranked_pop[0][:]
            if candidate not in best_solutions: best_solutions.append(candidate)
        history.append(-best_fit)
        survivors = ranked_pop[:pop_size // 2]; new_pop = survivors[:]
        while len(new_pop) < pop_size:
            p1, p2 = random.sample(survivors, 2); new_pop.append(mutate(crosover(p1, p2)))
        popul = new_pop
    return best_perm, -best_fit, history, improve_iters, len(best_solutions)

# ─────────────────────────────────────────────
# СЕСІЙНИЙ СТАН (для управління обчисленнями та конфіденційності)
# ─────────────────────────────────────────────
if "paused" not in st.session_state: st.session_state["paused"] = False
if "conf_mode" not in st.session_state: st.session_state["conf_mode"] = True
if "lr3_results" not in st.session_state: st.session_state["lr3_results"] = None
if "domain_name" not in st.session_state: st.session_state["domain_name"] = load_domain_name()

# ─────────────────────────────────────────────
# ПОТОЧНА ПРЕДМЕТНА ОБЛАСТЬ
# ─────────────────────────────────────────────
current_domain = DOMAINS[st.session_state["domain_name"]]
OBJECTS = current_domain["objects"]
OBJECT_NAMES = [o["name"] for o in OBJECTS]

safe_domain_name = st.session_state["domain_name"].replace(" ", "_").replace("'", "")
CURRENT_VOTES_FILE = f"votes_{safe_domain_name}.csv"
scores, counts = load_scores(CURRENT_VOTES_FILE, OBJECTS)
# ─────────────────────────────────────────────
# БІЧНА ПАНЕЛЬ
# ─────────────────────────────────────────────
st.sidebar.title("Навігація")

# перемикач предметної області (завдання 1)
st.sidebar.subheader("Предметна область")
domain_choice = st.sidebar.selectbox(
    "Оберіть предметну область",
    list(DOMAINS.keys()),
    index=list(DOMAINS.keys()).index(st.session_state["domain_name"])
)
if domain_choice != st.session_state["domain_name"]:
    st.session_state["domain_name"] = domain_choice
    save_domain(domain_choice)
    log_action("Користувач", f"Змінено предметну область на: {domain_choice}")
    st.rerun()

st.sidebar.subheader("Власна предметна область")
uploaded_domain = st.sidebar.file_uploader("Завантажте .txt файл (по 1 об'єкту в рядку)", type=["txt"])

if uploaded_domain is not None:
    if st.session_state.get("last_uploaded_file") != uploaded_domain.name:

        content = uploaded_domain.read().decode("utf-8").splitlines()
        custom_objects = [{"name": line.strip(), "img": ""} for line in content if line.strip()]

        if len(custom_objects) >= 3:
            custom_domain_name = "Власна область"
            custom_domain_dict = {"name": custom_domain_name, "objects": custom_objects}

            with open(CUSTOM_DOMAIN_FILE, "w", encoding="utf-8") as f:
                json.dump(custom_domain_dict, f, ensure_ascii=False)

            st.session_state["domain_name"] = custom_domain_name
            st.session_state["last_uploaded_file"] = uploaded_domain.name

            st.sidebar.success("Успішно завантажено")
            st.rerun()
        else:
            st.sidebar.error("У файлі має бути щонайменше 3 об'єкти")

# конфіденційний / відкритий режим (завдання 5)
st.sidebar.subheader("Режим голосування")
conf_toggle = st.sidebar.toggle(
    "Конфіденційний режим",
    value=st.session_state["conf_mode"]
)
st.session_state["conf_mode"] = conf_toggle
mode_label = "Конфіденційний" if conf_toggle else "Відкритий"
st.sidebar.caption(f"Поточний режим: **{mode_label}**")

tab = st.sidebar.selectbox("Розділ", [
    "Голосування (ЛР1)",
    "Результати ЛР1",
    "Голосування за евристики",
    "Застосування евристик",
    "Генетичний алгоритм",
    "ЛР3",
    "ЛР4",
    "Зміна ранжувань",
    "Допомога",
    "Адмін",
])

# ─────────────────────────────────────────────
# ПІДСИСТЕМА ДОПОМОГИ (завдання 2)
# ─────────────────────────────────────────────
HELP_TEXT = {
    "Голосування (ЛР1)": (
        "**Як голосувати?**\n\n"
        "1. Введіть своє ім'я у поле «Ваше ім'я».\n"
        "2. У конфіденційному режимі ім'я буде приховане в протоколі.\n"
        "3. Оберіть 3 різних об'єкти у порядку пріоритету (1-й — найважливіший).\n"
        "4. Натисніть **Проголосувати**.\n"
        "5. Зображення об'єктів відображаються внизу для зручності вибору."
    ),
    "Результати ЛР1": (
        "**Результати голосування (ЛР1)**\n\n"
        "Тут відображається таблиця з підсумками голосування:\n"
        "- 1-е місце = 3 бали, 2-е = 2, 3-є = 1.\n"
        "- Графік показує розподіл балів між об'єктами.\n"
        "- Дані використовуються в подальших лабораторних роботах."
    ),
    "Голосування за евристики": (
        "**Евристики** — правила для відсіювання найменш популярних об'єктів.\n\n"
        "Оберіть **3 різні** евристики у порядку пріоритету (1-й — найважливіший).\n"
        "Результати голосування визначать, які евристики застосовувати першими."
    ),
    "Застосування евристик": (
        "**Покрокове звуження підмножини об'єктів.**\n\n"
        "Евристики застосовуються послідовно у порядку їх пріоритетності,\n"
        "поки кількість об'єктів не зменшиться до 10."
    ),
    "Генетичний алгоритм": (
        "**Генетичний алгоритм (ГА)** знаходить компромісне ранжування.\n\n"
        "- **К1** мінімізує суму відстаней Кука до всіх ранжувань.\n"
        "- **К2** мінімізує максимальну відстань.\n"
        "Натисніть «Запустити ГА» для запуску."
    ),
    "ЛР3": (
        "**Повний перебір перестановок.**\n\n"
        "Знаходить медіанне ранжування за критерієм мінімуму суми або максимуму відстаней Кука.\n"
        "- Підтримується зупинка та відновлення обчислень.\n"
        "- Прогрес відображається у реальному часі."
    ),
    "ЛР4": (
        "**Розподілені обчислення та індекси задоволеності.**\n\n"
        "Ситуація А: обчислення індексу задоволеності кожного експерта.\n"
        "Ситуація Б: порівняння централізованих і розподілених обчислень."
    ),
    "Зміна ранжувань": (
        "**Незначна зміна індивідуальних ранжувань (завдання 10-11)**\n\n"
        "Оберіть голос конкретного експерта та змініть порядок обраних об'єктів.\n"
        "Система автоматично перераховує медіану та показує, як змінився результат."
    ),
    "Допомога": "Оберіть потрібний розділ у навігаційному меню для перегляду підказок.",
    "Адмін": (
        "**Адміністративна панель**\n\n"
        "Доступ захищений паролем.\n"
        "Адміністратор може:\n"
        "- Переглядати всі протоколи голосування.\n"
        "- Завантажувати дані для подальшої обробки.\n"
        "- Переглядати журнал дій користувачів.\n"
        "- Очищати голоси при потребі."
    ),
}

# ─────────────────────────────────────────────
# ГОЛОСУВАННЯ (ЛР1) — завдання 4, 5, 6, 7
# ─────────────────────────────────────────────
if tab == "Голосування (ЛР1)":
    with st.expander("Допомога"):
        st.markdown(HELP_TEXT["Голосування (ЛР1)"])

    st.title("Система експертного голосування — ЛР1")
    st.markdown(f"**Предметна область:** {current_domain['name']}")
    mode_badge = "🔒 Конфіденційний режим" if st.session_state["conf_mode"] else "🔓 Відкритий режим"
    st.info(mode_badge)

    st.write("Введіть ім'я та оберіть **3 об'єкти** у порядку пріоритету")
    name = st.text_input("Ваше ім'я")

    st.subheader("Виберіть 3 об'єкти (порядок важливий)")
    choice1 = st.selectbox("1-й пріоритет", OBJECT_NAMES, key="c1")
    choice2 = st.selectbox("2-й пріоритет", OBJECT_NAMES, key="c2")
    choice3 = st.selectbox("3-й пріоритет", OBJECT_NAMES, key="c3")

    if st.button("Проголосувати"):
        if name.strip() == "":
            st.error("Введіть ім'я")
        elif len({choice1, choice2, choice3}) < 3:
            st.error("Оберіть 3 різні об'єкти")
        else:
            # конфіденційний режим: хешуємо ім'я (завдання 5)
            if st.session_state["conf_mode"]:
                saved_name = hashlib.sha256(name.strip().encode()).hexdigest()[:10]
                st.success(f"Ваш голос збережено (конфіденційно). Ваш код: `{saved_name}`")
            else:
                saved_name = name.strip()
                st.success(f"Ваш голос збережено. Ви обрали: {choice1}, {choice2}, {choice3}")

            new_vote = pd.DataFrame(
                [[saved_name, choice1, choice2, choice3]],
                columns=["name", "choice1", "choice2", "choice3"]
            )
            if os.path.exists(CURRENT_VOTES_FILE):
                df = pd.read_csv(CURRENT_VOTES_FILE)
            else:
                df = pd.DataFrame(columns=["name", "choice1", "choice2", "choice3"])
            df = pd.concat([df, new_vote], ignore_index=True)
            df.to_csv(CURRENT_VOTES_FILE, index=False)
            log_action("Користувач", f"Голосування: {saved_name} -> {choice1}, {choice2}, {choice3}")
            st.info(f"Обрані об'єкти: **{choice1}** > **{choice2}** > **{choice3}**")

    st.divider()
    st.subheader("Об'єкти предметної області")
    cols = st.columns(4)
    for idx, obj in enumerate(OBJECTS):
        col = cols[idx % 4]
        try:
            image = Image.open(obj["img"])
            col.image(image, caption=obj["name"], use_column_width=True)
        except:
            col.write(obj["name"])

# ─────────────────────────────────────────────
# РЕЗУЛЬТАТИ ЛР1
# ─────────────────────────────────────────────
elif tab == "Результати ЛР1":
    with st.expander("Допомога"):
        st.markdown(HELP_TEXT["Результати ЛР1"])

    st.title("Результати лабораторної роботи №1")
    st.markdown(f"**Предметна область:** {current_domain['name']}")

    rows = []
    for o in OBJECT_NAMES:
        rows.append({
            "Об'єкт": o,
            "1-е місце": counts[o]["c1"],
            "2-е місце": counts[o]["c2"],
            "3-є місце": counts[o]["c3"],
            "Загалом обрано раз": counts[o]["c1"] + counts[o]["c2"] + counts[o]["c3"],
            "Сума балів": scores[o]
        })
    df_res = pd.DataFrame(rows).sort_values("Сума балів", ascending=False).reset_index(drop=True)
    df_res.index += 1
    st.dataframe(df_res, use_container_width=True)

    # графічна ілюстрація (завдання 8)
    fig, ax = plt.subplots(figsize=(7, 3)); fig.patch.set_alpha(0); ax.set_facecolor("none")
    ax.bar(df_res["Об'єкт"].tolist(), df_res["Сума балів"].tolist(), color="white")
    ax.set_xlabel("Об'єкт", color="white"); ax.set_ylabel("Сума балів", color="white")
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.tick_params(colors="white", axis="both", labelrotation=45)
    for sp in ax.spines.values(): sp.set_color("white")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2: st.pyplot(fig)

    # вивід у файл (завдання 9)
    output = io.StringIO()
    output.write(f"Результати ЛР1 — {current_domain['name']}\n\n")
    output.write(df_res.to_string())
    st.download_button("Зберегти результати ЛР1 у .txt",
                       data=output.getvalue().encode("utf-8"),
                       file_name="lr1_results.txt", mime="text/plain")
    log_action("Користувач", "Переглянуто результати ЛР1")

# ─────────────────────────────────────────────
# ГОЛОСУВАННЯ ЗА ЕВРИСТИКИ
# ─────────────────────────────────────────────
elif tab == "Голосування за евристики":
    with st.expander("Допомога"):
        st.markdown(HELP_TEXT["Голосування за евристики"])

    st.title("Голосування за пріоритетність евристик")
    st.subheader("Перелік евристик")
    for k, v in HEURISTICS.items():
        st.markdown(f"**{k}** — {v}")
    st.divider()

    name = st.text_input("Ваше ім'я")
    h_keys = list(HEURISTICS.keys())
    h1 = st.selectbox("1-й пріоритет", h_keys, key="h1")
    h2 = st.selectbox("2-й пріоритет", h_keys, key="h2")
    h3 = st.selectbox("3-й пріоритет", h_keys, key="h3")
    if st.button("Проголосувати"):
        if not name.strip():
            st.error("Введіть ім'я")
        elif len({h1, h2, h3}) < 3:
            st.error("Оберіть 3 різні евристики")
        else:
            df_h = load_h_votes()
            df_h = pd.concat([df_h, pd.DataFrame([[name.strip(), h1, h2, h3]],
                              columns=["name", "h1", "h2", "h3"])], ignore_index=True)
            df_h.to_csv(H_VOTES_FILE, index=False)
            log_action("Користувач", f"Голосування за евристики: {name.strip()} -> {h1}>{h2}>{h3}")
            st.success(f"Голос збережено. Ваш вибір: **{h1}** > **{h2}** > **{h3}**")

# ─────────────────────────────────────────────
# ЗАСТОСУВАННЯ ЕВРИСТИК
# ─────────────────────────────────────────────
elif tab == "Застосування евристик":
    with st.expander("Допомога"):
        st.markdown(HELP_TEXT["Застосування евристик"])

    st.title("Застосування евристик")
    df_h = load_h_votes()
    if len(df_h) == 0:
        st.warning("Ще немає голосів за евристики."); st.stop()
    ranked = ranked_heuristics_from_votes(df_h)
    st.subheader("Ранжування евристик")
    st.dataframe(pd.DataFrame([{"Евристика": k, "Опис": HEURISTICS[k], "Бали": v}
                               for k, v in ranked]), use_container_width=True)

    fig, ax = plt.subplots(figsize=(4.5, 2)); fig.patch.set_alpha(0); ax.set_facecolor("none")
    ax.bar([r[0] for r in ranked], [r[1] for r in ranked], color="white")
    ax.tick_params(colors="white")
    for sp in ax.spines.values(): sp.set_color("white")
    ax.set_xlabel("Евристика", color="white"); ax.set_ylabel("Бали", color="white")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2: st.pyplot(fig)

    st.divider(); st.subheader("Покрокове застосування евристик")
    ordered_keys = [k for k, _ in ranked]
    final_set, step_log = apply_heuristicsStep(OBJECT_NAMES, ordered_keys, counts, scores)
    final_set = sorted(final_set, key=lambda x: scores[x], reverse=True)[:10]
    if step_log:
        st.dataframe(pd.DataFrame(step_log), use_container_width=True)
    st.subheader("Фінальна підмножина")
    final_df = pd.DataFrame([{
        "Об'єкт": o, "1-е місце": counts[o]["c1"],
        "2-е місце": counts[o]["c2"], "3-є місце": counts[o]["c3"],
        "Сума балів": scores[o]
    } for o in final_set])
    final_df = final_df.sort_values("Сума балів", ascending=False).reset_index(drop=True)
    final_df.index += 1
    st.dataframe(final_df, use_container_width=True)
    if len(final_set) <= 10:
        st.success(f"Підмножину звужено до **{len(final_set)} об'єктів**")
    log_action("Користувач", f"Переглянуто застосування евристик. Фінальна підмножина: {', '.join(final_set)}")

# ─────────────────────────────────────────────
# ГЕНЕТИЧНИЙ АЛГОРИТМ
# ─────────────────────────────────────────────
elif tab == "Генетичний алгоритм":
    with st.expander("Допомога"):
        st.markdown(HELP_TEXT["Генетичний алгоритм"])

    st.title("Генетичний алгоритм")
    df_h = load_h_votes()
    if len(df_h) == 0:
        ordered_keys = list(HEURISTICS.keys())
    else:
        ranked = ranked_heuristics_from_votes(df_h)
        ordered_keys = [k for k, _ in ranked]
    final_set, _ = apply_heuristicsStep(OBJECT_NAMES, ordered_keys, counts, scores)
    final_set = sorted(final_set, key=lambda x: scores[x], reverse=True)[:10]

    expert_perms = [random.sample(final_set, len(final_set)) for _ in range(20)]
    pop_size = 80; generations = 200; mut_rate = 0.10

    if st.button("Запустити ГА"):
        log_action("Користувач", "Запущено ГА для оптимізації ранжування")
        with st.spinner("К1: мінімізація суми відстаней"):
            perm1, val1, hist1, iters1, nsol1 = genetic_rank(
                final_set, expert_perms, fitness_mode="sum",
                pop_size=pop_size, generations=generations, mut_rate=mut_rate)
        with st.spinner("К2: мінімізація максимуму відстані"):
            perm2, val2, hist2, iters2, nsol2 = genetic_rank(
                final_set, expert_perms, fitness_mode="max",
                pop_size=pop_size, generations=generations, mut_rate=mut_rate)

        st.divider(); st.subheader("Критерій 1 — мінімізація суми відстаней")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Найкраща сума відстаней", val1)
        col_b.metric("Знайдено нових кращих у поколіннях", str(iters1))
        col_c.metric("Кількість розв'язків", nsol1)
        st.markdown(f"Ранжування (К1): **{' > '.join(perm1)}**")

        st.divider(); st.subheader("Критерій 2 — мінімізація максимуму відстані")
        col_d, col_e, col_f = st.columns(3)
        col_d.metric("Найкращий максимум відстані", val2)
        col_e.metric("Знайдено нових кращих у поколіннях", str(iters2))
        col_f.metric("Кількість розв'язків", nsol2)
        st.markdown(f"Ранжування (К2): **{' > '.join(perm2)}**")

        st.divider(); st.subheader("Порівняння двох критеріїв")
        dists1 = [firstdist(perm1, exp) for exp in expert_perms]
        dists2 = [firstdist(perm2, exp) for exp in expert_perms]
        cmp_df = pd.DataFrame({
            "Критерій": ["Сума відстаней", "Максимум відстані", "Кількість розв'язків"],
            "К1": [sum(dists1), max(dists1), nsol1],
            "К2": [sum(dists2), max(dists2), nsol2],
        })
        st.dataframe(cmp_df, use_container_width=True, hide_index=True)

        # графічна ілюстрація (завдання 8)
        fig, ax = plt.subplots(figsize=(6, 2.5)); fig.patch.set_alpha(0); ax.set_facecolor("none")
        ax.plot(hist1, color="cyan", label="К1 (сума)")
        ax.plot(hist2, color="orange", label="К2 (макс)")
        ax.set_xlabel("Покоління", color="white"); ax.set_ylabel("Відстань", color="white")
        ax.tick_params(colors="white"); ax.legend(facecolor="black", labelcolor="white")
        for sp in ax.spines.values(): sp.set_color("white")
        st.pyplot(fig)

# ─────────────────────────────────────────────
# ЛР3 — з управлінням обчисленнями (завдання 7)
# ─────────────────────────────────────────────
elif tab == "ЛР3":
    with st.expander("Допомога"):
        st.markdown(HELP_TEXT["ЛР3"])

    st.title("ЛР3 — Визначення колективного ранжування")
    data_mode = st.radio(
        "Оберіть набір даних:",
        ["10 об'єктів / реальні голоси", "8 об'єктів / 11 експертів (тест)"],
        horizontal=True
    )
    if data_mode == "10 об'єктів / реальні голоси":
        df_h = load_h_votes()
        if len(df_h) == 0:
            ordered_keys = list(HEURISTICS.keys())
        else:
            ordered_keys = [k for k, _ in ranked_heuristics_from_votes(df_h)]
        winners_full, _ = apply_heuristicsStep(OBJECT_NAMES, ordered_keys, counts, scores)
        winners = sorted(winners_full, key=lambda x: scores[x], reverse=True)[:10]
        triples = load_expert_triples_from_votes(CURRENT_VOTES_FILE, winners)
    else:
        winners, triples = generate_mock_data(n_objs=8, n_experts=11,
                                              objects=OBJECT_NAMES)

    n_winners = len(winners)
    n_fact = math.factorial(n_winners)

    st.header("Множинні порівняння")
    display_data = {}
    for i, (name, o1, o2, o3) in enumerate(triples):
        display_data[f"Е{i+1}"] = [o1, o2, o3]
    df_triples_styled = pd.DataFrame(display_data)
    df_triples_styled.index = ["1-й", "2-й", "3-й"]
    st.dataframe(df_triples_styled, use_container_width=True)

    st.header("Матриця відношень переваги")
    stats_df = build_expert_stats_table(triples, winners)
    st.dataframe(stats_df, use_container_width=True)

    st.header("Матриця рангів")
    rank_matrix_data = pd.DataFrame(0,
        index=[f"Е{i+1}" for i in range(len(triples))], columns=winners)
    for i, (name, o1, o2, o3) in enumerate(triples):
        for r, obj in enumerate([o1, o2, o3], 1):
            if obj in winners: rank_matrix_data.at[f"Е{i+1}", obj] = r
    st.dataframe(rank_matrix_data.head(10), use_container_width=True)

    st.divider()
    st.header("Метрики відстані Кука")
    st.markdown(f"Кількість перестановок = {n_winners}! = {n_fact:,}")
    heuristic_choice = st.radio("Евристика метрики Кука",
        ["E1 — помірна взаємність", "E2 — максимальне задоволення побажань"],
        horizontal=True, key="brute_heuristic")
    heuristic_key = "E1" if "E1" in heuristic_choice else "E2"

    # управління обчисленнями (завдання 7)
    col_run, col_pause = st.columns(2)
    run_btn = col_run.button("Запустити", key="run_brute")
    if col_pause.button("Пауза / Відновити", key="pause_btn"):
        st.session_state["paused"] = not st.session_state["paused"]
        state_str = "призупинено" if st.session_state["paused"] else "відновлено"
        st.info(f"Обчислення {state_str}")

    if run_btn:
        log_action("Користувач", f"Запущено повний перебір ЛР3, евристика: {heuristic_key}")
        progress_bar = st.progress(0)
        dist_fn = cook_distance_e1 if heuristic_key == "E1" else cook_distance_e2
        min_sum = float("inf"); min_max = float("inf")
        best_perms_sum = []; best_perms_max = []; sample_rows = []
        all_perms = list(itertools.permutations(winners))
        total = len(all_perms)

        # ілюстрація динаміки обчислень (завдання 7)
        dyn_placeholder = st.empty()
        dyn_sum_history = []; dyn_max_history = []

        for idx, perm in enumerate(all_perms):
            # пауза
            while st.session_state.get("paused", False):
                time.sleep(0.1)
            p_list = list(perm)
            dists = [dist_fn(p_list, t) for t in triples]
            s = sum(dists); m = max(dists) if dists else 0
            dyn_sum_history.append(s); dyn_max_history.append(m)
            if idx < 50:
                row = {"№": idx+1, "Перестановка": " > ".join(p_list)}
                for i, d in enumerate(dists): row[f"d{i+1}"] = d
                row["Сума"] = s; row["Макс"] = m
                sample_rows.append(row)
            if s < min_sum: min_sum = s; best_perms_sum = [p_list]
            elif s == min_sum: best_perms_sum.append(p_list)
            if m < min_max: min_max = m; best_perms_max = [p_list]
            elif m == min_max: best_perms_max.append(p_list)
            progress_bar.progress((idx+1) / total)

        # зберігаємо результати в сесійний стан (завдання 6)
        st.session_state["lr3_results"] = {
            "winners": winners, "triples": triples,
            "best_sum": best_perms_sum, "best_max": best_perms_max,
            "min_sum": min_sum, "min_max": min_max,
            "heuristic": heuristic_key
        }
        log_action("Користувач", f"ЛР3 завершено. Мін.сума={min_sum}, Мін.макс={min_max}")

        st.subheader("Перші 50 рядків таблиці відстаней")
        st.dataframe(pd.DataFrame(sample_rows), use_container_width=True, hide_index=True)

        st.subheader("Мінімальні значення")
        cm1, cm2 = st.columns(2)
        cm1.metric("Мін. сума відстаней", min_sum)
        cm2.metric("Мін. максимум відстані", min_max)

        st.subheader("Медіани за критерієм мін. суми відстаней")
        st.markdown(f"Знайдено {len(best_perms_sum)} перестановок із сумою = {min_sum}:")
        for p in best_perms_sum[:5]: st.markdown(f"**{' > '.join(p)}**")

        st.subheader("Медіани за критерієм мін. максимуму відстані")
        for p in best_perms_max[:5]: st.markdown(f"{' > '.join(p)}")

        st.subheader("Відновлення ранжувань об'єктів")
        rs = restore_ranking(best_perms_sum[:5], winners)
        rs.index = [f"Медіана {i+1}" for i in range(len(rs))]
        st.dataframe(rs, use_container_width=True)

        # графічна ілюстрація медіан (завдання 8)
        st.subheader("Графік: суми відстаней по перестановках")
        fig, ax = plt.subplots(figsize=(7, 2.5)); fig.patch.set_alpha(0); ax.set_facecolor("none")
        ax.plot(dyn_sum_history[:500], color="cyan", alpha=0.7, linewidth=0.6, label="Сума")
        ax.axhline(min_sum, color="orange", linestyle="--", label=f"Мін={min_sum}")
        ax.set_xlabel("Перестановка", color="white"); ax.set_ylabel("Відстань", color="white")
        ax.tick_params(colors="white"); ax.legend(facecolor="black", labelcolor="white")
        for sp in ax.spines.values(): sp.set_color("white")
        st.pyplot(fig)

        # вивід у файл (завдання 9)
        output = io.StringIO()
        output.write("ЛР3 — Результати\n\n")
        output.write(f"Евристика: {heuristic_key}\nОб'єкти: {', '.join(winners)}\n\n")
        output.write(f"Мін. сума: {min_sum}\nМедіани (сума):\n")
        for p in best_perms_sum: output.write("  " + " > ".join(p) + "\n")
        output.write(f"\nМін. макс.: {min_max}\nМедіани (макс.):\n")
        for p in best_perms_max: output.write("  " + " > ".join(p) + "\n")
        st.download_button("Зберегти результати ЛР3 у .txt",
                           data=output.getvalue().encode("utf-8"),
                           file_name="lab3_results.txt", mime="text/plain")

    # ГА для ЛР3
    st.divider(); st.header("Еволюційний алгоритм (ГА)")
    if st.button("Запустити ГА", key="run_ga_lr3"):
        log_action("Користувач", "Запущено ГА в ЛР3")
        results = []
        for ga_fm in ["sum", "max"]:
            label = "сума" if ga_fm == "sum" else "максимум"
            with st.spinner(f"ГА: мін. {label} відстаней"):
                ga_perm, ga_val, ga_hist, ga_iters, ga_nsol = genetic_rank_cook(
                    winners, triples, heuristic=heuristic_key,
                    fitness_mode=ga_fm, pop_size=1000, generations=200, mut_rate=0.10)
            results.append((ga_fm, label, ga_perm, ga_val, ga_iters, ga_nsol))
        for ga_fm, label, ga_perm, ga_val, ga_iters, ga_nsol in results:
            st.subheader(f"Результат ({label})")
            st.markdown(f"Ранжування: {' > '.join(ga_perm)}")
            cg1, cg2, cg3 = st.columns(3)
            cg1.metric(f"Найкраще ({label})", ga_val)
            cg2.metric("Покращень знайдено", len(ga_iters))
            cg3.metric("Кількість розв'язків", ga_nsol)
        st.subheader("Порівняння двох критеріїв")
        res_sum = next(r for r in results if r[0] == "sum")
        res_max = next(r for r in results if r[0] == "max")
        dist_fn = cook_distance_e1 if heuristic_key == "E1" else cook_distance_e2
        d_s = [dist_fn(res_sum[2], t) for t in triples]
        d_m = [dist_fn(res_max[2], t) for t in triples]
        cmp_df = pd.DataFrame([
            {"Критерій": "Сума відстаней (K1)", "Ранжування K1": sum(d_s), "Ранжування K2": sum(d_m)},
            {"Критерій": "Максимум відстані (K2)", "Ранжування K1": max(d_s), "Ранжування K2": max(d_m)},
            {"Критерій": "К-сть розв'язків", "Ранжування K1": res_sum[5], "Ранжування K2": res_max[5]},
        ])
        st.dataframe(cmp_df, use_container_width=True, hide_index=True)

    # ГА для великих масштабів
    st.divider(); st.header("ГА: 20 / 50 / 100 альтернатив")
    if st.button("Запустити", key="run_scale"):
        log_action("Користувач", "Запущено ГА масштабування")
        test_cases = [
            (20, 10), (20, 20), (20, 30),
            (50, 10), (50, 20), (50, 30),
            (100, 10), (100, 20), (100, 30),
        ]
        scale_results = []
        pb = st.progress(0)
        for i, (n_objs, n_exps) in enumerate(test_cases):
            rng = random.Random(42)
            objs = [f"O{j+1}" for j in range(n_objs)]
            perms = [rng.sample(objs, n_objs) for _ in range(n_exps)]
            p_s, v_s, _, it_s, _ = genetic_rank(objs, perms, fitness_mode="sum",
                                                  pop_size=60, generations=200)
            p_m, v_m, _, it_m, _ = genetic_rank(objs, perms, fitness_mode="max",
                                                  pop_size=60, generations=200)
            scale_results.append({
                "Альтернативи": n_objs, "Експерти": n_exps,
                "Мін. сума (К1)": v_s, "Покращень К1": len(it_s),
                "Мін. макс (К2)": v_m, "Покращень К2": len(it_m),
            })
            pb.progress((i+1) / len(test_cases))
        st.dataframe(pd.DataFrame(scale_results), use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────
# ЛР4
# ─────────────────────────────────────────────
elif tab == "ЛР4":
    with st.expander("Допомога"):
        st.markdown(HELP_TEXT["ЛР4"])

    st.title("ЛР4 — Розподілені обчислення та індекси задоволеності")
    df_h = load_h_votes()
    if len(df_h) == 0:
        ordered_keys = list(HEURISTICS.keys())
    else:
        ordered_keys = [k for k, _ in ranked_heuristics_from_votes(df_h)]
    winners_full, _ = apply_heuristicsStep(OBJECT_NAMES, ordered_keys, counts, scores)
    winners = sorted(winners_full, key=lambda x: scores[x], reverse=True)[:10]
    raw_triples = load_raw_triples(CURRENT_VOTES_FILE)
    triples_filtered = load_expert_triples_from_votes(CURRENT_VOTES_FILE, winners)

    consensus_R = []
    df_sat = pd.DataFrame()
    avg_sat = 0.0

    st.header("Ситуація А: індекси задоволеності експертів")
    st.markdown(f"Підмножина об'єктів (n={len(winners)}): {', '.join(winners)}")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Задані експертами порівняння")
        df_raw = pd.DataFrame(raw_triples, columns=["Експерт", "1-й", "2-й", "3-й"])
        st.dataframe(df_raw, use_container_width=True, hide_index=True)
    with col2:
        st.subheader("Визначення компромісу")
        if st.button("Обчислити індекси", key="lr4_calc_a"):
            log_action("Користувач", "ЛР4: обчислення індексів задоволеності")
            with st.spinner("Перебір перестановок..."):
                best_s, best_m, min_s, min_m, _ = brute_force_median(
                    winners, triples_filtered, heuristic="E2")
            consensus_R = best_s[0]
            st.success(f"Ранжування: {' > '.join(consensus_R)}")
            df_sat = calculate_satisfaction(raw_triples, consensus_R)
            st.dataframe(df_sat, use_container_width=True, hide_index=True)
            avg_sat = df_sat["Задоволеність (%)"].mean()
            st.metric("Колективний індекс задоволеності групи", f"{avg_sat:.2f}%")

            # графічна ілюстрація (завдання 8)
            if len(df_sat) > 0:
                fig, ax = plt.subplots(figsize=(6, 2.5)); fig.patch.set_alpha(0); ax.set_facecolor("none")
                ax.bar(df_sat["Експерт"], df_sat["Задоволеність (%)"], color="cyan")
                ax.axhline(avg_sat, color="orange", linestyle="--", label=f"Серед.={avg_sat:.1f}%")
                ax.set_ylabel("Задоволеність %", color="white"); ax.set_xlabel("Експерт", color="white")
                ax.tick_params(colors="white", labelrotation=45)
                ax.legend(facecolor="black", labelcolor="white")
                for sp in ax.spines.values(): sp.set_color("white")
                st.pyplot(fig)

            # вивід у файл (завдання 9)
            output = io.StringIO()
            output.write("ЛР4 — Протокол\n\n")
            output.write(f"Компромісне ранжування: {' > '.join(consensus_R)}\n\n")
            output.write("Індекси задоволеності:\n")
            output.write(df_sat.to_string(index=False))
            output.write(f"\n\nКолективний індекс: {avg_sat:.2f}%\n")
            st.download_button("Зберегти протокол ЛР4 у .txt",
                               data=output.getvalue().encode("utf-8"),
                               file_name="lab4_results.txt", mime="text/plain")

    st.divider()
    st.header("Ситуація Б: Розподілені vs Централізовані обчислення")
    if st.button("Порівняти", key="lr4_brute_dist"):
        log_action("Користувач", "ЛР4: порівняння розподілених обчислень")
        test_winners = winners[:8]; test_triples = triples_filtered
        start_c = time.time()
        best_s, best_m, min_s, min_m, _ = brute_force_median(
            test_winners, test_triples, heuristic="E2")
        t_cent = time.time() - start_c
        dist_best, dist_min, t_dist = distributed_brute_force_sim(
            test_winners, test_triples, workers=4)
        col_c, col_d = st.columns(2)
        with col_c:
            st.markdown("**Централізовано**")
            st.metric("Час (1 потік)", f"{t_cent:.4f} сек")
            st.metric("Мін. сума відстаней", min_s)
            for p in best_s[:3]: st.code(" > ".join(p))
        with col_d:
            st.markdown("**Розподілено (4 потоки)**")
            st.metric("Час (4 потоки)", f"{t_dist:.4f} сек")
            st.metric("Мін. сума відстаней", dist_min)
            for p in dist_best[:3]: st.code(" > ".join(p))
        if dist_min == min_s:
            st.success("Доведено: результати ідентичні!")
        else:
            st.error("Увага: результати не співпали")

    st.divider(); st.subheader("ГА для великих розмірностей (n >> 12)")
    n_sim = st.slider("Кількість альтернатив", 15, 200, 50, step=5)
    n_exp = st.slider("Кількість експертів", 10, 100, 30, step=10)
    if st.button("Запустити ГА", key="lr4_ga"):
        log_action("Користувач", f"ЛР4 ГА: n={n_sim}, exp={n_exp}")
        sim_objs = [f"O{i+1}" for i in range(n_sim)]
        rng = random.Random(42)
        sim_perms = [rng.sample(sim_objs, n_sim) for _ in range(n_exp)]
        start_c = time.time()
        c_perm, c_val, _, _, _ = genetic_rank(sim_objs, sim_perms, fitness_mode="sum",
                                               pop_size=60, generations=100)
        t_cent = time.time() - start_c

        def run_island(seed_offset):
            return genetic_rank(sim_objs, sim_perms, fitness_mode="sum",
                                pop_size=40, generations=100, mut_rate=0.1 + seed_offset * 0.03)

        start_d = time.time(); islands = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(run_island, i) for i in range(4)]
            for f in concurrent.futures.as_completed(futures): islands.append(f.result())
        t_dist = time.time() - start_d
        best_island = min(islands, key=lambda x: x[1])
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Централізовано**\n- Час: `{t_cent:.3f} с`\n- Мін. сума: `{c_val}`")
        with c2:
            st.markdown(f"**Розподілено (4 острови)**\n- Час: `{t_dist:.3f} с`\n- Мін. сума: `{best_island[1]}`")

# ─────────────────────────────────────────────
# ЗМІНА РАНЖУВАНЬ (завдання 10, 11)
# ─────────────────────────────────────────────
elif tab == "Зміна ранжувань":
    with st.expander("Допомога"):
        st.markdown(HELP_TEXT["Зміна ранжувань"])

    st.title("Незначна зміна індивідуальних ранжувань")
    st.markdown("Оберіть голос та змініть порядок об'єктів. Система покаже, як змінюється медіана.")

    if not os.path.exists(CURRENT_VOTES_FILE):
        st.warning("Немає даних голосування."); st.stop()
    df_votes = pd.read_csv(CURRENT_VOTES_FILE)
    if len(df_votes) == 0:
        st.warning("Немає голосів."); st.stop()

    df_h = load_h_votes()
    if len(df_h) == 0:
        ordered_keys = list(HEURISTICS.keys())
    else:
        ordered_keys = [k for k, _ in ranked_heuristics_from_votes(df_h)]
    winners_full, _ = apply_heuristicsStep(OBJECT_NAMES, ordered_keys, counts, scores)
    winners = sorted(winners_full, key=lambda x: scores[x], reverse=True)[:10]

    # оригінальні голоси
    orig_triples = load_expert_triples_from_votes(CURRENT_VOTES_FILE, winners)
    if not orig_triples:
        st.warning("Немає валідних голосів для підмножини переможців."); st.stop()

    expert_names = [t[0] for t in orig_triples]
    selected_expert = st.selectbox("Оберіть голос для зміни", expert_names)
    orig_vote = next(t for t in orig_triples if t[0] == selected_expert)
    st.markdown(f"Поточний вибір: **{orig_vote[1]}** > **{orig_vote[2]}** > **{orig_vote[3]}**")

    new1 = st.selectbox("Новий 1-й пріоритет", winners, index=winners.index(orig_vote[1]) if orig_vote[1] in winners else 0, key="new1")
    new2 = st.selectbox("Новий 2-й пріоритет", winners, index=winners.index(orig_vote[2]) if orig_vote[2] in winners else 1, key="new2")
    new3 = st.selectbox("Новий 3-й пріоритет", winners, index=winners.index(orig_vote[3]) if orig_vote[3] in winners else 2, key="new3")

    if st.button("Перерахувати медіану"):
        if len({new1, new2, new3}) < 3:
            st.error("Оберіть 3 різні об'єкти"); st.stop()

        # модифікований набір трійок
        modified_triples = []
        for t in orig_triples:
            if t[0] == selected_expert:
                modified_triples.append((selected_expert, new1, new2, new3))
            else:
                modified_triples.append(t)

        heuristic_key = "E2"
        with st.spinner("Обчислення оригінальної медіани..."):
            orig_best_s, _, orig_min_s, _, _ = brute_force_median(winners, orig_triples, heuristic_key)
        with st.spinner("Обчислення нової медіани..."):
            new_best_s, _, new_min_s, _, _ = brute_force_median(winners, modified_triples, heuristic_key)

        log_action("Користувач", f"Зміна ранжувань: {selected_expert}: {orig_vote[1]}>{orig_vote[2]}>{orig_vote[3]} -> {new1}>{new2}>{new3}")

        # ілюстрація зміни результатів (завдання 11)
        st.subheader("Порівняння медіан до і після зміни")
        col_o, col_n = st.columns(2)
        with col_o:
            st.markdown("**Оригінальна медіана**")
            st.metric("Мін. сума відстаней", orig_min_s)
            for p in orig_best_s[:3]: st.markdown(f"- {' > '.join(p)}")
        with col_n:
            st.markdown("**Нова медіана**")
            st.metric("Мін. сума відстаней", new_min_s,
                      delta=int(new_min_s) - int(orig_min_s))
            for p in new_best_s[:3]: st.markdown(f"- {' > '.join(p)}")

        # графічна ілюстрація порівняння (завдання 8, 11)
        orig_ranks = {o: i+1 for i, o in enumerate(orig_best_s[0])}
        new_ranks  = {o: i+1 for i, o in enumerate(new_best_s[0])}
        fig, ax = plt.subplots(figsize=(7, 3)); fig.patch.set_alpha(0); ax.set_facecolor("none")
        x = range(len(winners))
        ax.plot(x, [orig_ranks.get(o, 0) for o in winners], "o-", color="cyan",  label="До зміни")
        ax.plot(x, [new_ranks.get(o, 0)  for o in winners], "s-", color="orange", label="Після зміни")
        ax.set_xticks(x); ax.set_xticklabels(winners, rotation=45, color="white")
        ax.set_ylabel("Ранг", color="white"); ax.tick_params(colors="white")
        ax.legend(facecolor="black", labelcolor="white")
        ax.invert_yaxis()
        for sp in ax.spines.values(): sp.set_color("white")
        st.pyplot(fig)

        if orig_best_s[0] == new_best_s[0]:
            st.success("Медіана не змінилась — колективне рішення стійке до незначних змін.")
        else:
            st.warning("Медіана змінилась!")

# ─────────────────────────────────────────────
# ДОПОМОГА (завдання 2)
# ─────────────────────────────────────────────
elif tab == "Допомога":
    st.title("Підсистема допомоги")
    for section, text in HELP_TEXT.items():
        with st.expander(section):
            st.markdown(text)
    st.divider()
    st.subheader("Загальна інформація про систему")
    st.markdown("""
**СР1 — Система розподіленого колективного ранжування**

Система реалізує повний цикл преференційного голосування:

1. **ЛР1** — Збір голосів від експертів. Підтримується конфіденційний та відкритий режими.
2. **ЛР2** — Застосування евристик для звуження підмножини об'єктів до 10.
3. **ЛР3** — Повний перебір перестановок та знаходження медіанного ранжування.
4. **ЛР4** — Розподілені обчислення, індекси задоволеності, порівняння підходів.

**Функції СР1:**
- 2 предметні області, які перемикаються без перезапуску
- Конфіденційний режим (хешування імен)
- Протоколювання всіх дій у файл `protocol.log`
- Управління обчисленнями: пауза / відновлення
- Зміна ранжувань та ілюстрація впливу на медіану
- Вивід результатів на екран та у файли .txt / .csv
    """)

# ─────────────────────────────────────────────
# АДМІН (завдання 3, 6, 9)
# ─────────────────────────────────────────────
elif tab == "Адмін":
    st.title("Адміністративна панель")
    password = st.text_input("Пароль", type="password")
    if password == ADMIN_PASSWORD:
        log_action("Адмін", "Вхід в адміністративну панель")
        st.success("Доступ надано")

        st.subheader("Протокол голосування (ЛР1)")
        if os.path.exists(CURRENT_VOTES_FILE):
            df_v = pd.read_csv(CURRENT_VOTES_FILE)
            if st.session_state["conf_mode"]:
                st.info("Конфіденційний режим: імена зашифровані")
            st.dataframe(df_v, use_container_width=True)
            with open(CURRENT_VOTES_FILE, "rb") as fh:
                st.download_button("Завантажити votes_Астрономічні_обєкти.csv", fh, "votes_Астрономічні_обєкти.csv", "text/csv")
            if st.button("Очистити голоси ЛР1"):
                pd.DataFrame(columns=["name","choice1","choice2","choice3"]).to_csv(CURRENT_VOTES_FILE, index=False)
                log_action("Адмін", "Очищено голоси ЛР1")
                st.success("Голоси видалено.")
        else:
            st.info("Файл votes_Астрономічні_обєкти.csv не знайдено.")

        st.divider()
        st.subheader("Протокол голосування за евристики")
        df_h = load_h_votes()
        if len(df_h) > 0:
            st.dataframe(df_h, use_container_width=True)
            with open(H_VOTES_FILE, "rb") as fh:
                st.download_button("Завантажити heuristic_votes.csv", fh, "heuristic_votes.csv", "text/csv")
            if st.button("Очистити голоси за евристики"):
                pd.DataFrame(columns=["name","h1","h2","h3"]).to_csv(H_VOTES_FILE, index=False)
                log_action("Адмін", "Очищено голоси за евристики")
                st.success("Видалено.")
        else:
            st.info("Голосів за евристики немає.")

        st.divider()
        st.subheader("Журнал дій (протокол адміністратора та користувачів)")
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, encoding="utf-8") as f:
                log_content = f.read()
            st.text_area("Журнал", log_content, height=250)
            st.download_button("Завантажити журнал", log_content.encode("utf-8"),
                               "protocol.log", "text/plain")
            if st.button("Очистити журнал"):
                open(LOG_FILE, "w").close()
                log_action("Адмін", "Журнал очищено")
                st.success("Журнал очищено.")
        else:
            st.info("Журнал порожній.")

        st.divider()
        st.subheader("Збереження / Завантаження архіву даних (завдання 1)")
        if st.button("Зберегти архів (votes + евристики + журнал)"):
            buf = io.BytesIO()
            import zipfile
            with zipfile.ZipFile(buf, "w") as zf:
                for fn in [CURRENT_VOTES_FILE, H_VOTES_FILE, LOG_FILE, DOMAIN_FILE]:
                    if os.path.exists(fn):
                        zf.write(fn)
            buf.seek(0)
            st.download_button("Завантажити архів .zip", buf,
                               "sr1_archive.zip", "application/zip")
            log_action("Адмін", "Збережено архів даних")
    elif password:
        st.error("Невірний пароль")
        log_action("Невідомий", "Невдала спроба входу в адмін-панель")
