import requests
import json
import time
import csv
import os
from collections import defaultdict

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# ==============================
# CONFIG
# ==============================

TIMEOUT = 30
RETRIES = 2

PROMPT = (
    "Detect vulnerabilities in this code and return ONLY the vulnerability type "
    "(SQL Injection, XSS, Command Injection, Path Traversal or None)."
)

LABELS = ["SQL Injection", "XSS", "Command Injection", "Path Traversal", "None"]

PROVIDERS = {
    "mistral": {
        "url": "https://api.mistral.ai/v1/chat/completions",
        "api_key": os.getenv("MISTRAL_API_KEY"),
        "model": "mistral-small",
        "type": "openai"
    },
    "ollama": {
        "url": "http://localhost:11434/api/chat",
        "api_key": None,
        "model": "llama3",
        "type": "ollama"
    },
    "gemma": {
        "url": "http://localhost:11434/api/chat",
        "api_key": None,
        "model": "gemma3",
        "type": "ollama"
    }
}

# ==============================
# LOAD DATASET
# ==============================

with open("dataset.json", "r", encoding="utf-8") as f:
    dataset = json.load(f)

# ==============================
# NORMALIZAÇÃO
# ==============================

def extract(text):
    if not text:
        return "None"

    text = text.lower()

    if any(x in text for x in ["sql injection", "sqli"]):
        return "SQL Injection"

    if any(x in text for x in ["xss", "cross site scripting", "cross-site scripting"]):
        return "XSS"

    if any(x in text for x in ["command injection", "os command"]):
        return "Command Injection"

    if any(x in text for x in ["path traversal", "directory traversal"]):
        return "Path Traversal"

    return "None"

# ==============================
# REQUEST COM RETRY
# ==============================

def safe_request(url, headers, body):
    for attempt in range(RETRIES):
        try:
            response = requests.post(url, headers=headers, json=body, timeout=TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if attempt == RETRIES - 1:
                raise e
            time.sleep(1)

# ==============================
# PROVIDERS
# ==============================

def call_mistral(provider, code):
    json_resp = safe_request(
        provider["url"],
        {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json"
        },
        {
            "model": provider["model"],
            "messages": [{"role": "user", "content": f"{PROMPT}\n{code}"}],
            "temperature": 0
        }
    )

    return json_resp.get("choices", [{}])[0].get("message", {}).get("content", "")


def call_ollama(provider, code):
    json_resp = safe_request(
        provider["url"],
        {},
        {
            "model": provider["model"],
            "messages": [
                {"role": "user", "content": f"{PROMPT}\n{code}"}
            ],
            "stream": False
        }
    )

    return (
        json_resp.get("message", {}).get("content") or
        json_resp.get("response") or
        ""
    )

# ==============================
# MÉTRICAS
# ==============================

def compute_metrics(confusion):
    metrics = {}

    for label in LABELS:
        tp = confusion[label][label]
        fp = sum(confusion[x][label] for x in LABELS if x != label)
        fn = sum(confusion[label][x] for x in LABELS if x != label)

        precision = tp / (tp + fp) if (tp + fp) else 0
        recall = tp / (tp + fn) if (tp + fn) else 0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0

        metrics[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1
        }

    return metrics

# ==============================
# BENCHMARK
# ==============================

def run_benchmark():
    results = {}

    for name, provider in PROVIDERS.items():

        if provider["type"] != "ollama" and not provider.get("api_key"):
            print(f"⚠️ Skipping {name} (no API key)")
            continue

        print(f"\n=== TESTING {name.upper()} ===")

        confusion = defaultdict(lambda: defaultdict(int))
        total_time = 0
        correct = 0
        valid = 0

        for i, test in enumerate(dataset):

            code = test["code"]

            expected = test["expected"]
            if isinstance(expected, list):
                expected = expected[0]

            try:
                start = time.time()

                if provider["type"] == "openai":
                    response = call_mistral(provider, code)
                else:
                    response = call_ollama(provider, code)

                latency = time.time() - start

            except Exception as e:
                print(f"[{i+1}] ERROR: {e}")
                continue

            total_time += latency
            valid += 1

            predicted = extract(response)

            confusion[expected][predicted] += 1

            if predicted == expected:
                correct += 1

            print(f"[{i+1}] {expected} -> {predicted} ({latency:.2f}s)")

        accuracy = correct / valid if valid else 0
        avg_latency = total_time / valid if valid else 0

        results[name] = {
            "accuracy": accuracy,
            "avg_latency": avg_latency,
            "metrics": compute_metrics(confusion),
            "confusion": confusion
        }

    return results

# ==============================
# GRÁFICOS
# ==============================

def plot_all(results):

    providers = list(results.keys())

    # Accuracy
    plt.figure()
    plt.bar(providers, [results[p]["accuracy"] for p in providers])
    plt.title("Accuracy")
    plt.savefig("accuracy.png")
    plt.close()

    # Latência
    plt.figure()
    plt.bar(providers, [results[p]["avg_latency"] for p in providers])
    plt.title("Latency (s)")
    plt.savefig("latency.png")
    plt.close()

    # F1
    rows = []
    for provider, data in results.items():
        for label, m in data["metrics"].items():
            rows.append({
                "Provider": provider,
                "Label": label,
                "F1": m["f1"]
            })

    df = pd.DataFrame(rows)

    plt.figure()
    sns.barplot(data=df, x="Label", y="F1", hue="Provider")
    plt.xticks(rotation=30)
    plt.title("F1 per Vulnerability")
    plt.savefig("f1_score.png")
    plt.close()

    # Confusion matrix
    for provider, data in results.items():
        matrix = [
            [data["confusion"][a][b] for b in LABELS]
            for a in LABELS
        ]

        df = pd.DataFrame(matrix, index=LABELS, columns=LABELS)

        plt.figure()
        sns.heatmap(df, annot=True, fmt="d")
        plt.title(provider)
        plt.savefig(f"confusion_{provider}.png")
        plt.close()

# ==============================
# CSV
# ==============================

def save_results(results):
    with open("results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Provider", "Label", "Precision", "Recall", "F1"])

        for provider, data in results.items():
            for label, m in data["metrics"].items():
                writer.writerow([
                    provider,
                    label,
                    round(m["precision"], 4),
                    round(m["recall"], 4),
                    round(m["f1"], 4)
                ])

# ==============================
# MAIN
# ==============================

if __name__ == "__main__":

    results = run_benchmark()

    print("\n=== FINAL RESULTS ===")

    for provider, data in results.items():
        print(f"\n{provider.upper()}")
        print(f"Accuracy: {data['accuracy']:.2f}")
        print(f"Latency: {data['avg_latency']:.2f}s")

    save_results(results)
    plot_all(results)

    print("\nBenchmark finalizado com sucesso")