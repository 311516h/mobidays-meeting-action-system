import json
import re
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
PREDICTION_PATH = BASE_DIR / "data" / "processed" / "action_items.json"
GOLD_PATH = BASE_DIR / "data" / "eval" / "gold_action_items.json"


def load_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def tokenize(text: str) -> set[str]:
    normalized = re.sub(r"[^0-9A-Za-z가-힣/]+", " ", text).lower()
    return {token for token in normalized.split() if token}


def similarity(left: dict[str, Any], right: dict[str, Any]) -> float:
    if left.get("owner") != right.get("owner"):
        return 0.0

    left_tokens = tokenize(left.get("task", ""))
    right_tokens = tokenize(right.get("task", ""))

    if not left_tokens or not right_tokens:
        return 0.0

    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def match_items(
    predictions: list[dict[str, Any]],
    gold_items: list[dict[str, Any]],
    threshold: float = 0.5,
) -> tuple[list[tuple[int, int, float]], list[int], list[int]]:
    candidates = []

    for pred_idx, prediction in enumerate(predictions):
        for gold_idx, gold in enumerate(gold_items):
            score = similarity(prediction, gold)
            if score >= threshold:
                candidates.append((pred_idx, gold_idx, score))

    candidates.sort(key=lambda item: item[2], reverse=True)

    matched_predictions = set()
    matched_gold = set()
    matches = []

    for pred_idx, gold_idx, score in candidates:
        if pred_idx in matched_predictions or gold_idx in matched_gold:
            continue
        matched_predictions.add(pred_idx)
        matched_gold.add(gold_idx)
        matches.append((pred_idx, gold_idx, score))

    false_positive = [
        idx for idx in range(len(predictions)) if idx not in matched_predictions
    ]
    false_negative = [
        idx for idx in range(len(gold_items)) if idx not in matched_gold
    ]

    return matches, false_positive, false_negative


def evaluate(
    prediction_path: Path = PREDICTION_PATH,
    gold_path: Path = GOLD_PATH,
    threshold: float = 0.5,
) -> dict[str, Any]:
    predictions = load_json(prediction_path)
    gold_items = load_json(gold_path)
    matches, false_positive, false_negative = match_items(
        predictions,
        gold_items,
        threshold,
    )

    true_positive_count = len(matches)
    precision = true_positive_count / len(predictions) if predictions else 0.0
    recall = true_positive_count / len(gold_items) if gold_items else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "prediction_count": len(predictions),
        "gold_count": len(gold_items),
        "true_positive": true_positive_count,
        "false_positive": len(false_positive),
        "false_negative": len(false_negative),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "matches": matches,
        "false_positive_items": [predictions[idx] for idx in false_positive],
        "false_negative_items": [gold_items[idx] for idx in false_negative],
    }


def print_report(result: dict[str, Any]) -> None:
    print("Action Item Extraction Evaluation")
    print("---------------------------------")
    print(f"predictions: {result['prediction_count']}")
    print(f"gold: {result['gold_count']}")
    print(f"true_positive: {result['true_positive']}")
    print(f"false_positive: {result['false_positive']}")
    print(f"false_negative: {result['false_negative']}")
    print(f"precision: {result['precision']:.3f}")
    print(f"recall: {result['recall']:.3f}")
    print(f"f1: {result['f1']:.3f}")

    if result["false_positive_items"]:
        print("\nFalse positives")
        for item in result["false_positive_items"]:
            print(f"- {item['owner']}: {item['task']}")

    if result["false_negative_items"]:
        print("\nFalse negatives")
        for item in result["false_negative_items"]:
            print(f"- {item['owner']}: {item['task']}")


def main() -> None:
    print_report(evaluate())


if __name__ == "__main__":
    main()

