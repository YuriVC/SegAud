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

PROVIDERS = {
    "mistral": {
        "url": "https://api.mistral.ai/v1/chat/completions",
        "api_key": os.getenv("MISTRAL_API_KEY"),
        "model": "mistral-small",
        "type": "openai"
    },
    "deepseek": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "api_key": os.getenv("OPENROUTER_API_KEY"),
        "model": "deepseek/deepseek-v4-pro",
        "type": "openrouter"
    },
    "ollama": {
        "url": "http://localhost:11434/api/generate",
        "api_key": None,
        "model": "llama3",
        "type": "ollama"
    }
}

PROMPT = "Detect vulnerabilities in this code and return ONLY the vulnerability type (SQL Injection, XSS, Command Injection, Path Traversal or None)."

LABELS = ["SQL Injection", "XSS", "Command Injection", "Path Traversal", "None"]

# ==============================
# LOAD DATASET
# ==============================

with open("dataset.json", "r", encoding="utf-8") as f:
    dataset = json.load(f)

# ==============================
# EXTRAÇÃO
# ==============================

def extract(text):
    if not text:
        return "None"

    text = text.lower()

    if "sql injection" in text:
        return "SQL Injection"
    if "xss" in text or "cross site scripting" in text:
        return "XSS"
    if "command injection" in text:
        return "Command Injection"
    if "path traversal" in text:
        return "Path Traversal"

    return "None"

# ==============================
# CALLS
# ==============================

def safe_request(url, headers, body):
    response = requests.post(url, headers=headers, json=body, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def call_openai(provider, code):
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


def call_openrouter(provider, code):
    json_resp = safe_request(
        provider["url"],
        {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "benchmark"
        },
        {
            "model": provider["model"],
            "messages": [{"role": "user", "content": f"{PROMPT}\n{code}"}]
        }
    )

    return json_resp.get("choices", [{}])[0].get("message", {}).get("content", "")


def call_ollama(provider, code):
    json_resp = safe_request(
        provider["url"],
        {},
        {
            "model": provider["model"],
            "prompt": f"{PROMPT}\n{code}",
            "stream": False
        }
    )

    return json_resp.get("response", "")

# ==============================
# METRICS
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

        if provider["api_key"] is None and provider["type"] != "ollama":
            print(f"Skipping {name} (no API key)")
            continue

        print(f"\n=== TESTING {name.upper()} ===")

        confusion = defaultdict(lambda: defaultdict(int))
        total_time = 0
        correct = 0

        for i, test in enumerate(dataset):
            code = test["code"]
            expected = test["expected"][0]

            start = time.time()

            try:
                if provider["type"] == "openai":
                    response = call_openai(provider, code)
                elif provider["type"] == "openrouter":
                    response = call_openrouter(provider, code)
                else:
                    response = call_ollama(provider, code)

            except Exception as e:
                print(f"[{i+1}] ERROR: {e}")
                continue

            latency = time.time() - start
            total_time += latency

            predicted = extract(response)

            confusion[expected][predicted] += 1

            if predicted == expected:
                correct += 1

            print(f"[{i+1}] {expected} -> {predicted} ({latency:.2f}s)")

        total = len(dataset)
        accuracy = correct / total if total else 0
        avg_latency = total_time / total if total else 0

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

def plot_overall(results):
    providers = list(results.keys())

    acc = [results[p]["accuracy"] for p in providers]
    lat = [results[p]["avg_latency"] for p in providers]

    plt.figure()
    plt.bar(providers, acc)
    plt.title("Accuracy")
    plt.savefig("accuracy.png")
    plt.close()

    plt.figure()
    plt.bar(providers, lat)
    plt.title("Latency")
    plt.savefig("latency.png")
    plt.close()


def plot_f1(results):
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
    plt.savefig("f1_score.png")
    plt.close()


def plot_confusion(results):
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
# SAVE CSV
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
# EXECUTE
# ==============================

if __name__ == "__main__":

    results = run_benchmark()

    print("\n=== FINAL RESULTS ===")

    for provider, data in results.items():
        print(f"\n{provider.upper()}")
        print(f"Accuracy: {data['accuracy']:.2f}")
        print(f"Latency: {data['avg_latency']:.2f}s")

    save_results(results)

    plot_overall(results)
    plot_f1(results)
    plot_confusion(results)

    print("\n✔ Benchmark finalizado com gráficos")