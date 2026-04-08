# 📊 Dataset Validator for Intent Classification Agent

## 📌 Overview

This project is a **Python-based dataset validation tool** designed to evaluate the quality of a JSON dataset used for training an intent classification agent.

The agent classifies queries into:

* `greetings`
* `service_request`
* `device_control`
* `out_of_scope`

This validator ensures that the dataset meets required standards such as:

* No duplicate queries
* Correct intent labeling
* Standardized service request subcategories
* Proper text encoding

---

## 🎯 Objectives

The tool validates whether the dataset fulfills the following requirements:

1. Detect **duplicate queries**
2. Identify **intent mismatches**
3. Validate **service request subcategories**
4. Detect **encoding issues (broken text)**

---

## 📂 Project Structure

```
project-folder/
│
├── dataset_validator.py
├── final_dataset_balanced_12000.json
├── dataset_report.json   # (generated after running)
└── README.md
```

---

## ⚙️ Requirements

* Python 3.7 or above
* No external libraries required (uses built-in modules)

---

## ▶️ How to Run

### Step 1: Clone or Download the Project

Download the files or clone the repository:

```
git clone <your-repo-link>
cd project-folder
```

---

### Step 2: Place Dataset File

Make sure your dataset file is named:

```
final_dataset_balanced_12000.json
```

and placed in the same folder as the script.

---

### Step 3: Run the Script

Execute the following command:

```
python dataset_validator.py
```

---

## 📈 Output

After running, you will see a summary like:

```
Total samples: 12000

Duplicate queries: 150
Intent mismatches: 80
Invalid subcategories: 300
Encoding issues: 25

===== FINAL REPORT =====
...
```

---

## 📄 Generated Report

A file named:

```
dataset_report.json
```

will be created, containing sample issues:

* Duplicate queries
* Mismatched intents
* Invalid subcategories
* Encoding problems

---

## 🧠 Validation Logic

### ✅ Duplicate Detection

Checks for repeated queries (case-insensitive).

---

### ⚠️ Intent Mismatch Detection

Uses keyword-based rules:

| Type            | Example Keywords               |
| --------------- | ------------------------------ |
| Device Control  | turn on, set, off              |
| Service Request | repair, fix, service, register |
| Out of Scope    | what is, explain, who is       |

---

### 📦 Subcategory Validation

Allowed subcategories:

* `raise_service_request`
* `explore_amc_plans`
* `discover_new_products`
* `check_loyalty_points`
* `register_product`
* `jebrish_commands`

Any other subcategory is flagged as invalid.

---

### 🔤 Encoding Check

Detects broken or corrupted text such as:

```
à¤¸à¥à¤®...
```

---

## 🚀 Future Improvements

* Add **fuzzy duplicate detection**
* Improve **intent classification rules**
* Add **language validation**
* Generate **dataset quality score**

---

## 🤝 Contribution

Feel free to improve:

* Validation rules
* Performance
* Reporting format

---

## 📌 Notes

* This tool is designed for **pre-training dataset validation**
* Helps improve model accuracy by ensuring clean data
* Works across **multiple languages**

---

## 👨‍💻 Author

Built for validating multilingual intent classification datasets.

---
