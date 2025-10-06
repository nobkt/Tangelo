import re

# ファイルパス
specfile = "dev_notes/dlpno/coupling_function_spec.md"

# 必須セクション見出し（部分一致OK）
sections = [
    "Purpose", "Relation to Skeleton", "Notation", "Formal Definition",
    "Alternative", "Mathematical Properties", "Data Requirements",
    "Computational Complexity", "Prohibited", "Deferred", "Validation",
    "Next Task"
]

# 禁止事項キーワード
prohibited_keywords = ["heuristic", "fallback", "RI", "Schwarz", "stochastic", "adaptive", "scaling factor"]

# 数式定義（MP2 ペアエネルギー式の一部）
math_expr = r"C\(i,j\).*?\|E_pair\^MP2\(i,j\)\|"

# Pythonコード混入禁止
python_keywords = ["def ", "import ", "for ", "while ", "return ", "class "]

with open(specfile, encoding="utf-8") as f:
    text = f.read()

# 1. セクション確認
missing_sections = [s for s in sections if s.lower() not in text.lower()]
print("MissingSections:", missing_sections if missing_sections else "None")

# 2. 数式定義確認
if not re.search(math_expr, text):
    print("MathDef: MISSING")
else:
    print("MathDef: OK")

# 3. 禁止事項列挙確認
prohibited_missing = [k for k in prohibited_keywords if k.lower() not in text.lower()]
print("ProhibitedKeywordsMissing:", prohibited_missing if prohibited_missing else "None")

# 4. Pythonコード混入確認
python_found = [k for k in python_keywords if k in text]
print("PythonCodeFound:", python_found if python_found else "None")

# 5. 次タスク記載
if "Next Task" in text or "Phase2-Task2.4" in text:
    print("NextTask: OK")
else:
    print("NextTask: MISSING")

# 6. 総合判定
if not missing_sections and re.search(math_expr, text) and not prohibited_missing and not python_found and ("Next Task" in text or "Phase2-Task2.4" in text):
    print("PASS")
else:
    print("FAIL: See above for details")