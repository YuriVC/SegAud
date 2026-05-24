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
# OLLAMA REQUEST
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

def validate_response(response, criteria, must_not=None):

    if not response:
        return False

    response = response.lower()

    positive_score = 0
    negative_score = 0

    # =====================================
    # POSITIVE MATCHES
    # =====================================

    for pattern in criteria:

        try:

            if re.search(
                pattern,
                response,
                re.IGNORECASE
            ):

                positive_score += 1

        except:
            pass

    # =====================================
    # NEGATIVE MATCHES
    # =====================================

    if must_not:

        for pattern in must_not:

            try:

                if re.search(
                    pattern,
                    response,
                    re.IGNORECASE
                ):

                    negative_score += 1

            except:
                pass

    # =====================================
    # FINAL SCORE
    # =====================================

    final_score = (
        positive_score - negative_score
    )

    return final_score >= 1

# =====================================
# BENCHMARK
# =====================================

def run_benchmark():

    tests = load_yaml_tests()

    if not tests:

        print("No tests found")

        return {}

    print(f"Loaded {len(tests)} tests")

    results = {}

    for model in MODELS:

        print(f"\n=== TESTING {model.upper()} ===")

        total = 0

        correct = 0

        category_stats = defaultdict(
            lambda: {
                "total": 0,
                "correct": 0
            }
        )

        for i, test in enumerate(tests):

            prompt = test.get("prompt", "")

            criteria = test.get("criteria", [])

            must_not = test.get("must_not", [])

            category = test.get("id", "unknown")

            if not prompt:
                continue

            total += 1

            category_stats[category]["total"] += 1

            try:

                response = call_model(
                    model,
                    prompt
                )

                print("\n---------------------------")
                print(f"MODEL: {model}")
                print(f"TEST : {category}")
                print("RESPONSE:")
                print(response[:1500])
                print("---------------------------\n")

                ok = validate_response(
                    response,
                    criteria,
                    must_not
                )

                if ok:

                    correct += 1

                    category_stats[category]["correct"] += 1

                print(

                    f"[{i+1}/{len(tests)}] "
                    f"{category} -> "
                    f"{'PASS' if ok else 'FAIL'}"
                )

            except Exception as e:

                print(
                    f"[{i+1}/{len(tests)}] "
                    f"ERROR ({model}): {e}"
                )

        accuracy = (
            correct / total
            if total else 0
        )

        results[model] = {

            "accuracy": accuracy,

            "categories": category_stats
        }

        unload_model(model)

        time.sleep(2)

    return results

# =====================================
# SAVE CSV
# =====================================

def save_csv(results):

    rows = []

    for model, data in results.items():

        rows.append({

            "Model": model,

            "Category": "OVERALL",

            "Accuracy": round(
                data["accuracy"],
                6
            )
        })

        for category, stats in data[
            "categories"
        ].items():

            total = stats["total"]

            correct = stats["correct"]

            acc = (
                correct / total
                if total else 0
            )

            rows.append({

                "Model": model,

                "Category": category,

                "Accuracy": round(acc, 6)
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
# PLOT
# =====================================

def plot_results(results):

    models = []

    accuracy = []

    for model, data in results.items():

        models.append(model)

        accuracy.append(data["accuracy"])

    plt.figure(figsize=(14, 7))

    plt.bar(models, accuracy)

    plt.xticks(rotation=25)

    plt.ylabel("Accuracy")

    plt.title(
        "LLM Security Benchmark - PHP"
    )

    plt.tight_layout()

    output = os.path.join(
        BASE_DIR,
        "benchmark_accuracy.png"
    )

    plt.savefig(output)

    print(f"Graph saved: {output}")

# =====================================
# MAIN
# =====================================

if __name__ == "__main__":

    print(
        "Loading PHP security tests..."
    )

    results = run_benchmark()

    print("\n=== FINAL RESULTS ===")

    for model, data in results.items():

        print(f"\n{model.upper()}")

        print(
            f"Accuracy: "
            f"{data['accuracy']:.6f}"
        )

    save_csv(results)

    plot_results(results)

    print("\nBenchmark finished successfully")