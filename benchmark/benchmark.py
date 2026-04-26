import requests
import time
import json
import csv
from typing import List, Dict

with open("dataset.json", "r", encoding="utf-8") as f:
    dataset = json.load(f)

OLLAMA_URL = "http://localhost:11434/v1/messages"
MODEL = "llama3"  # pode trocar: codellama, mistral, etc.

PROMPT_TEMPLATE = """
Detect the vulnerabilities in the code and explain them.

Code:
{code}
"""

dataset = [
    {
        "id": 1,
        "code": "query = 'SELECT * FROM users WHERE id=' + user_input",
        "expected": ["SQL Injection"]
    },
    {
        "id": 2,
        "code": "document.write(location.hash)",
        "expected": ["XSS"]
    },
    {
        "id": 3,
        "code": "password = '123456'",
        "expected": ["Weak Password"]
    }
]


def query_ollama(prompt: str):
    start = time.time()

    response = requests.post(
        OLLAMA_URL,
        headers={
            "x-api-key": "ollama",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": MODEL,
            "max_tokens": 1024,
            "temperature": 0,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )

    latency = time.time() - start

    if response.status_code != 200:
        print("Erro:", response.text)
        return "", latency

    data = response.json()

    try:
        text = data["content"][0]["text"]
    except:
        text = ""

    return text.lower(), latency



VULN_KEYWORDS = {
    "SQL Injection": ["sql injection"],
    "XSS": ["cross-site scripting", "xss"],
    "Weak Password": ["weak password", "hardcoded password"]
}


def extract_vulnerabilities(response_text: str) -> List[str]:
    found = []

    for vuln, keywords in VULN_KEYWORDS.items():
        for kw in keywords:
            if kw in response_text:
                found.append(vuln)
                break

    return found


def evaluate(expected: List[str], predicted: List[str]):
    tp = len(set(expected) & set(predicted))
    fp = len(set(predicted) - set(expected))
    fn = len(set(expected) - set(predicted))

    return tp, fp, fn


def calculate_metrics(tp, fp, fn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0

    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) > 0 else 0)

    return precision, recall, f1


def run_benchmark():
    results = []

    total_tp = total_fp = total_fn = 0
    total_latency = 0

    for sample in dataset:
        prompt = PROMPT_TEMPLATE.format(code=sample["code"])

        response_text, latency = query_ollama(prompt)

        predicted = extract_vulnerabilities(response_text)
        expected = sample["expected"]

        tp, fp, fn = evaluate(expected, predicted)

        total_tp += tp
        total_fp += fp
        total_fn += fn
        total_latency += latency

        results.append({
            "id": sample["id"],
            "expected": expected,
            "predicted": predicted,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "latency": latency
        })

        print(f"[{sample['id']}] TP={tp} FP={fp} FN={fn} Latência={latency:.2f}s")

    precision, recall, f1 = calculate_metrics(total_tp, total_fp, total_fn)
    avg_latency = total_latency / len(dataset)

    print("\n=== resultado final ===")
    print(f"Precision: {precision:.2f}")
    print(f"Recall: {recall:.2f}")
    print(f"F1-score: {f1:.2f}")
    print(f"Latência média: {avg_latency:.2f}s")

    save_csv(results)


def save_csv(results: List[Dict]):
    with open("results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print("\nResultados salvos em results.csv")


if __name__ == "__main__":
    run_benchmark()
