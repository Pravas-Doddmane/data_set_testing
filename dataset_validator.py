import json
from collections import defaultdict
import re

# ===== CONFIG =====
ALLOWED_SUBCATEGORIES = {
    "raise_service_request",
    "explore_amc_plans",
    "discover_new_products",
    "check_loyalty_points",
    "register_product",
    "jebrish_commands"
}

DEVICE_KEYWORDS = ["turn on", "turn off", "set", "increase", "decrease"]
OUT_OF_SCOPE_KEYWORDS = ["what is", "who is", "tell me", "explain"]
SERVICE_KEYWORDS = ["repair", "fix", "service", "register", "amc"]

# ===== LOAD DATA =====
with open("final_dataset_balanced_12000.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total samples: {len(data)}\n")

# ===== 1. DUPLICATE CHECK =====
query_count = defaultdict(int)

for item in data:
    q = item["query"].strip().lower()
    query_count[q] += 1

duplicates = [q for q, c in query_count.items() if c > 1]

print(f"Duplicate queries: {len(duplicates)}")

# ===== 2. INTENT MISMATCH CHECK =====
def detect_intent(query):
    q = query.lower()

    if any(k in q for k in DEVICE_KEYWORDS):
        return "device_control"
    if any(k in q for k in SERVICE_KEYWORDS):
        return "service_request"
    if any(k in q for k in OUT_OF_SCOPE_KEYWORDS):
        return "out_of_scope"

    return "unknown"

mismatches = []

for item in data:
    predicted = detect_intent(item["query"])
    actual = item["expected_response_type"]

    if predicted != "unknown" and predicted != actual:
        mismatches.append({
            "query": item["query"],
            "expected": actual,
            "predicted": predicted
        })

print(f"Intent mismatches: {len(mismatches)}")

# ===== 3. SUBCATEGORY CHECK =====
invalid_subcategories = []

for item in data:
    if item["expected_response_type"] == "service_request":
        sub = item.get("sub_category", "").lower()

        if sub not in ALLOWED_SUBCATEGORIES:
            invalid_subcategories.append({
                "query": item["query"],
                "subcategory": sub
            })

print(f"Invalid subcategories: {len(invalid_subcategories)}")

# ===== 4. ENCODING ISSUES =====
encoding_issues = []

def is_broken_text(text):
    return "à" in text or "�" in text

for item in data:
    if is_broken_text(item["query"]):
        encoding_issues.append(item["query"])

print(f"Encoding issues: {len(encoding_issues)}")

# ===== SUMMARY =====
print("\n===== FINAL REPORT =====")
print(f"Total: {len(data)}")
print(f"Duplicates: {len(duplicates)}")
print(f"Mismatches: {len(mismatches)}")
print(f"Invalid subcategories: {len(invalid_subcategories)}")
print(f"Encoding issues: {len(encoding_issues)}")

# ===== OPTIONAL: SAVE REPORT =====
report = {
    "duplicates": duplicates[:20],
    "mismatches": mismatches[:20],
    "invalid_subcategories": invalid_subcategories[:20],
    "encoding_issues": encoding_issues[:20]
}

with open("dataset_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

print("\nReport saved as dataset_report.json")