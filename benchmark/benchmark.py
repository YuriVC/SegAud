import requests
import yaml
import os
import re
import subprocess
import time
from collections import defaultdict

import pandas as pd
import matplotlib.pyplot as plt

# =====================================
# BASE DIR
# =====================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =====================================
# CONFIG
# =====================================

OLLAMA_URL = "http://localhost:11434/api/chat"

TIMEOUT = 300

LANGUAGE = "English"

PROMPT = (
    "Detecte vulnerabilidades no código e diga o tipo:"
    if LANGUAGE == "Português (BR)"
    else "Detect vulnerabilities in the code and say the type:"
)

MODELS = [

    "granite4.1:3b",
    "gemma4:latest",
    "falcon3:latest",
    "deepseek-coder:latest",
    "yi-coder:latest",
    "stable-code:latest",
    "laguna-xs.2:latest",
    "exaone-deep:latest"
]

# =====================================
# LOAD TESTS
# =====================================

def load_yaml_tests():

    file = os.path.join(
        BASE_DIR,
        "security_php.yaml"
    )

    if not os.path.exists(file):

        print(f"[ERROR] File not found: {file}")

        return []

    with open(file, "r", encoding="utf-8") as f:

        data = yaml.safe_load(f)

    tests = []

    if isinstance(data, list):

        for item in data:

            tests.append({

                "id": item.get("id", "unknown"),

                "prompt": item.get("prompt", ""),

                "criteria": item.get("criteria", []),

                "must_not": item.get("must_not", [])
            })

    return tests

# =====================================
# UNLOAD MODEL
# =====================================

def unload_model(model):

    try:

        subprocess.run(
            ["ollama", "stop", model],
            capture_output=True
        )

        print(f"[INFO] Unloaded model: {model}")

    except Exception as e:

        print(f"[WARNING] Could not unload {model}: {e}")

# =====================================
# MODEL REQUEST
# =====================================

def call_model(model, code_prompt):

    full_prompt = (
        PROMPT +
        "\n\n" +
        code_prompt
    )

    response = requests.post(

        OLLAMA_URL,

        json={

            "model": model,

            "messages": [
                {
                    "role": "user",
                    "content": full_prompt
                }
            ],

            "stream": False
        },

        timeout=TIMEOUT
    )

    response.raise_for_status()

    data = response.json()

    content = (
        data.get("message", {})
            .get("content", "")
            .strip()
    )

    if not content:
        return "[EMPTY_RESPONSE]"

    return content

# =====================================
# VALIDATION
# =====================================

SOFT_FALSE_POSITIVES = [

    r"\bsafe\b",

    r"whitelist.*function",

    r"allowed.*files"
]

DEFENSIVE_CONTEXT = [

    "safe coding",

    "safe handling",

    "safe implementation",

    "safe practice",

    "safe practices",

    "safe functions",

    "safe method",

    "safe methods"
]

def evaluate_response(response, criteria, must_not=None):

    if not response:

        return False, 0, 0, 1

    response_lower = response.lower()

    tp = 0
    fp = 0
    fn = 0

    # =====================================
    # TRUE POSITIVE / FALSE NEGATIVE
    # =====================================

    for pattern in criteria:

        try:

            if re.search(
                pattern,
                response,
                re.IGNORECASE
            ):

                tp += 1

            else:

                fn += 1

        except:
            pass

    # =====================================
    # FALSE POSITIVE
    # =====================================

    if must_not:

        for pattern in must_not:

            try:

                if re.search(
                    pattern,
                    response,
                    re.IGNORECASE
                ):

                    # =========================
                    # SAFE CONTEXT IGNORE
                    # =========================

                    if pattern == r"\bsafe\b":

                        ignore = False

                        for ctx in DEFENSIVE_CONTEXT:

                            if ctx in response_lower:

                                ignore = True
                                break

                        if ignore:
                            continue

                    # =========================
                    # SOFT FALSE POSITIVE
                    # =========================

                    if pattern in SOFT_FALSE_POSITIVES:

                        fp += 0.25

                    else:

                        fp += 1

            except:
                pass

    # =====================================
    # FINAL SCORE
    # =====================================

        total_criteria = len(criteria)

        coverage = tp / total_criteria

        score = (tp * 2) - fp

        passed = (
            score >= 2
            and coverage >= 0.5
) 
        return passed, tp, fp, fn

# =====================================
# METRICS
# =====================================

def compute_metrics(tp, fp, fn):

    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0 else 0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0 else 0
    )

    f1 = (
        2 * precision * recall /
        (precision + recall)
        if (precision + recall) > 0 else 0
    )

    accuracy = (
        tp / (tp + fp + fn)
        if (tp + fp + fn) > 0 else 0
    )

    return accuracy, precision, recall, f1

# =====================================
# BENCHMARK
# =====================================

def run_benchmark():

    tests = load_yaml_tests()

    if not tests:

        print("No tests found")

        return {}, {}

    print(f"Loaded {len(tests)} tests")

    results = {}

    heatmap_data = defaultdict(dict)

    for model in MODELS:

        print(f"\n=== TESTING {model.upper()} ===")

        total_tp = 0
        total_fp = 0
        total_fn = 0

        for i, test in enumerate(tests):

            prompt = test.get("prompt", "")

            criteria = test.get("criteria", [])

            must_not = test.get("must_not", [])

            category = test.get("id", "unknown")

            if not prompt:
                continue

            try:

                response = call_model(
                    model,
                    prompt
                )

                print("\n---------------------------")
                print(f"MODEL: {model}")
                print(f"TEST : {category}")
                print("RESPONSE:")
                print(response[:1200])
                print("---------------------------\n")

                passed, tp, fp, fn = evaluate_response(
                    response,
                    criteria,
                    must_not
                )

                total_tp += tp
                total_fp += fp
                total_fn += fn

                heatmap_data[model][category] = (
                    1 if passed else 0
                )

                print(
                    f"[{i+1}/{len(tests)}] "
                    f"{category} -> "
                    f"{'PASS' if passed else 'FAIL'}"
                )

                print(
                    f"TP={tp} FP={fp} FN={fn}"
                )

            except Exception as e:

                print(
                    f"[{i+1}/{len(tests)}] "
                    f"ERROR ({model}): {e}"
                )

                heatmap_data[model][category] = 0

        accuracy, precision, recall, f1 = compute_metrics(
            total_tp,
            total_fp,
            total_fn
        )

        results[model] = {

            "accuracy": accuracy,

            "precision": precision,

            "recall": recall,

            "f1": f1,

            "tp": total_tp,

            "fp": total_fp,

            "fn": total_fn
        }

        unload_model(model)

        time.sleep(2)

    return results, heatmap_data

# =====================================
# SAVE CSV
# =====================================

def save_csv(results):

    rows = []

    for model, data in results.items():

        rows.append({

            "Model": model,

            "Accuracy": round(
                data["accuracy"],
                6
            ),

            "Precision": round(
                data["precision"],
                6
            ),

            "Recall": round(
                data["recall"],
                6
            ),

            "F1": round(
                data["f1"],
                6
            ),

            "TP": data["tp"],

            "FP": data["fp"],

            "FN": data["fn"]
        })

    df = pd.DataFrame(rows)

    output = os.path.join(
        BASE_DIR,
        "benchmark_results.csv"
    )

    df.to_csv(
        output,
        index=False
    )

    print(f"\nCSV saved: {output}")

# =====================================
# BAR GRAPH
# =====================================

def plot_f1(results):

    models = []
    f1_scores = []

    for model, data in results.items():

        models.append(model)

        f1_scores.append(data["f1"])

    plt.figure(figsize=(14, 7))

    plt.bar(models, f1_scores)

    plt.xticks(rotation=25)

    plt.ylabel("F1 Score")

    plt.title(
        "LLM Security Benchmark - F1 Score"
    )

    plt.tight_layout()

    output = os.path.join(
        BASE_DIR,
        "benchmark_f1.png"
    )

    plt.savefig(output)

    print(f"Saved: {output}")

# =====================================
# METRICS GRAPH
# =====================================

def plot_metrics(results):

    df = pd.DataFrame(results).T

    metrics = [
        "accuracy",
        "precision",
        "recall",
        "f1"
    ]

    plt.figure(figsize=(16, 8))

    for metric in metrics:

        plt.plot(
            df.index,
            df[metric],
            marker="o",
            label=metric.upper()
        )

    plt.xticks(rotation=25)

    plt.ylabel("Score")

    plt.title(
        "LLM Security Benchmark Metrics"
    )

    plt.legend()

    plt.tight_layout()

    output = os.path.join(
        BASE_DIR,
        "benchmark_metrics.png"
    )

    plt.savefig(output)

    print(f"Saved: {output}")

# =====================================
# HEATMAP
# =====================================

def plot_heatmap(heatmap_data):

    df = pd.DataFrame(heatmap_data).T

    plt.figure(figsize=(18, 8))

    plt.imshow(
        df,
        aspect="auto"
    )

    plt.colorbar(label="PASS(1) / FAIL(0)")

    plt.xticks(
        range(len(df.columns)),
        df.columns,
        rotation=90
    )

    plt.yticks(
        range(len(df.index)),
        df.index
    )

    plt.title(
        "Security Vulnerability Detection Heatmap"
    )

    plt.tight_layout()

    output = os.path.join(
        BASE_DIR,
        "benchmark_heatmap.png"
    )

    plt.savefig(output)

    print(f"Saved: {output}")

# =====================================
# RADAR CHART
# =====================================

def plot_radar(results):

    metrics = [
        "accuracy",
        "precision",
        "recall",
        "f1"
    ]

    first_model = list(results.keys())[0]

    values = [
        results[first_model][m]
        for m in metrics
    ]

    values += values[:1]

    angles = [
        n / float(len(metrics)) * 2 * 3.141592
        for n in range(len(metrics))
    ]

    angles += angles[:1]

    plt.figure(figsize=(8, 8))

    ax = plt.subplot(111, polar=True)

    ax.plot(
        angles,
        values,
        linewidth=2
    )

    ax.fill(
        angles,
        values,
        alpha=0.25
    )

    plt.xticks(
        angles[:-1],
        [m.upper() for m in metrics]
    )

    plt.title(
        f"Radar Metrics - {first_model}"
    )

    output = os.path.join(
        BASE_DIR,
        "benchmark_radar.png"
    )

    plt.savefig(output)

    print(f"Saved: {output}")

# =====================================
# RANKING
# =====================================

def print_ranking(results):

    print("\n=== MODEL RANKING ===")

    ranked = sorted(

        results.items(),

        key=lambda x: x[1]["f1"],

        reverse=True
    )

    for i, (model, data) in enumerate(ranked):

        print(

            f"{i+1}. "
            f"{model} "
            f"F1={data['f1']:.6f}"
        )

# =====================================
# MAIN
# =====================================

if __name__ == "__main__":

    print(
        "Loading PHP security tests..."
    )

    results, heatmap_data = run_benchmark()

    print("\n=== FINAL RESULTS ===")

    for model, data in results.items():

        print(f"\n{model.upper()}")

        print(
            f"Accuracy : {data['accuracy']:.6f}"
        )

        print(
            f"Precision: {data['precision']:.6f}"
        )

        print(
            f"Recall   : {data['recall']:.6f}"
        )

        print(
            f"F1 Score : {data['f1']:.6f}"
        )

        print(
            f"TP={data['tp']} "
            f"FP={data['fp']} "
            f"FN={data['fn']}"
        )

    print_ranking(results)

    save_csv(results)

    plot_f1(results)

    plot_metrics(results)

    plot_heatmap(heatmap_data)

    plot_radar(results)

    print("\nBenchmark finished successfully")