"""LLM label probe — test the shared Qwen3.5 server on CT-report labeling.

Two purposes:
  1. Team request: sanity-check whether the LLM server gives sensible output.
  2. Project value: see if the LLM agrees with our regex labels on CT reports,
     as a feasibility check for LLM-assisted label review (NOT a gold standard).

SAFETY: uses ONLY the synthetic/example reports (mimic_ct_head_synthetic.csv),
which are illustrative and safe to send. No real MIMIC patient data leaves the
machine. Do not point this at real reports without confirming the server is a
compliant, non-logging local endpoint (PhysioNet DUA).

Server quirks found during testing (report to team):
  - model id is 'qwen3.5-397b' (NOT 'nvidia/Qwen3.5-397B-A17B-NVFP4' from email)
  - default thinking mode returns content=None and burns all tokens; must pass
    chat_template_kwargs={'enable_thinking': False}.
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import REPO_ROOT

URL = "https://ds4dh.unige.ch/vllm/v1/chat/completions"
KEY = "sk-shared-1jf_aQziEO_DClIOc4k0P0BWfdO71pLLntV7rsUXV7Y"
MODEL = "qwen3.5-397b"
SYNTH = REPO_ROOT / "mimic_ct_head_synthetic.csv"

PROMPT = (
    "You are labeling a head CT radiology report. Based ONLY on the IMPRESSION "
    "and FINDINGS, classify the scan as exactly one word: 'Positive' if it shows "
    "an ACUTE clinically significant intracranial finding (hemorrhage, infarct, "
    "acute fracture, mass effect, midline shift, acute edema, hydrocephalus), or "
    "'Negative' if there is no acute finding. Answer with only the single word.\n\n"
    "REPORT:\n{report}"
)


def llm_label(report_text: str) -> str:
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT.format(report=report_text)}],
        "max_tokens": 10, "temperature": 0,
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    d = json.loads(urllib.request.urlopen(req, timeout=120).read())
    txt = (d["choices"][0]["message"].get("content") or "").strip()
    low = txt.lower()
    if "positive" in low:
        return "Positive"
    if "negative" in low:
        return "Negative"
    return f"?({txt[:20]})"


# Minimal reimplementation of the regex label logic (Positive vs Negative only),
# mirroring Classifying CT reports.sql, for a like-for-like comparison.
NEG = re.compile(r"(?i)(impression|findings)[\s\S]{0,800}(no acute intracranial|"
                 r"no acute abnormality|unremarkable|no acute process|no acute "
                 r"finding|normal head ct|normal study|no hemorrhage|no fracture|"
                 r"without acute)")
POS = re.compile(r"(?i)(impression|findings)[\s\S]{0,800}(hemorrhage|hematoma|"
                 r"infarct|fracture|mass effect|midline shift|edema|hydrocephalus|"
                 r"herniation|bleed|ischemi)")


def regex_label(text: str) -> str:
    if POS.search(text) and not NEG.search(text):
        return "Positive"
    if NEG.search(text):
        return "Negative"
    return "Unclear"


def main():
    df = pd.read_csv(SYNTH)
    print(f"Loaded {len(df)} synthetic reports (safe to send).\n")
    print(f"{'note_id':<10}{'regex':<12}{'llm':<14}{'agree':<7}")
    print("-" * 43)
    agree = 0
    for _, row in df.iterrows():
        rgx = regex_label(row["text"])
        try:
            llm = llm_label(row["text"])
        except Exception as e:
            llm = f"ERR:{type(e).__name__}"
        ok = (rgx == llm)
        agree += ok
        print(f"{row['note_id']:<10}{rgx:<12}{llm:<14}{'yes' if ok else 'NO':<7}")
    print("-" * 43)
    print(f"agreement: {agree}/{len(df)}")
    print("\nNote: synthetic reports only; this checks LLM sensibility + regex "
          "concordance,\nNOT clinical accuracy. A clinician gold standard "
          "(LABELING.md) remains required.")


if __name__ == "__main__":
    main()
