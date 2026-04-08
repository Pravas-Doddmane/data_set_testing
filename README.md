# Dataset Validator & Cleaner (Multilingual Intent Dataset)

This folder contains a Python script that validates and cleans a multilingual intent dataset used for an intent classification agent.

## Dataset format
Each entry in `final_dataset_balanced_12000.json` is a JSON object with:

- `id` (format: `intent_language_number`)
- `language` (one of: `english`, `hindi`, `gujarati`, `bengali`, `telugu`, `tamil`, `kannada`, `malayalam`)
- `expected_response_type` (one of: `greetings`, `service_request`, `device_control`, `out_of_scope`)
- `query` (kept in the original script/language)
- `is_boundary` (boolean)
- optional `sub_category`
  - must exist for `service_request`
  - may exist for `out_of_scope` only when it is `jebrish_commands`

Allowed `service_request` subcategories:

- `raise_service_request`
- `explore_amc_plans`
- `discover_new_products`
- `check_loyalty_points`
- `register_product`
- `jebrish_commands`

## What the script does
`dataset_validator.py` is a **validator + cleaner**:

- Validates `id` format and sequential numbering per `(expected_response_type, language)`
- Validates that `sub_category` is present only when required (and is one of the allowed values)
- Detects duplicates (per-language, normalized)
- Detects broken/corrupted text and routes it to `out_of_scope` with `sub_category = "jebrish_commands"`
- Rewrites `final_dataset_balanced_12000.json` into a consistent, native-script dataset while keeping the same overall balance and structure
- Writes `dataset_report.json` in this structure:

```json
{
  "summary": {
    "total_samples": 12000,
    "duplicates_found": 0,
    "intent_mismatches": 0,
    "fixed_samples": 0,
    "encoding_issues": 0
  },
  "issues": {
    "duplicates": [],
    "mismatches": [],
    "invalid_subcategories": [],
    "encoding_issues": []
  },
  "corrected_dataset": []
}
```

Important: the script **overwrites** `final_dataset_balanced_12000.json` with the corrected dataset.

## Requirements
- Python 3.7+
- No external dependencies (standard library only)

## How to run
From this folder:

```bash
python dataset_validator.py
```

Optional paths:

```bash
python dataset_validator.py --dataset final_dataset_balanced_12000.json --report dataset_report.json
```

## Notes (Windows console)
If your terminal prints Unicode text as `????` but the JSON looks correct in your editor, it’s usually a console/codepage issue. The dataset itself is written as UTF-8 JSON.

