"""e05 — LLM label ALL real CT reports and compare with the regex labels.

Runs every real head-CT report through the local Qwen3.5 server, records the
LLM's Positive/Negative judgment, computes the regex label the same way the
datathon SQL does, and reports agreement + a disagreement list for clinician
review. This is LLM-ASSISTED label review (a second opinion that flags likely
regex errors), NOT a clinician gold standard — that still requires humans
(LABELING.md).

DATA: real MIMIC-IV report text. The user confirmed this server is MIMIC-approved
(inside the DUA/IRB-covered environment, local, non-logging). Do not run against
any other endpoint.

Robustness: concurrent requests, checkpointing (resumes if interrupted),
per-report error capture.

Run from repo root:  python paper/reproduce/experiments/e05_llm_label_all.py
"""
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import REPO_ROOT, OUTPUT_DIR

REPORTS = REPO_ROOT / "extracted" / "team2-ZZZ Lab" / "mimitc-ct-head-example.csv"
CHECKPOINT = OUTPUT_DIR / "e05_llm_labels_checkpoint.csv"
RESULT = OUTPUT_DIR / "e05_llm_vs_regex.csv"
DISAGREE = OUTPUT_DIR / "e05_disagreements_for_review.csv"

URL = "https://ds4dh.unige.ch/vllm/v1/chat/completions"
KEY = "sk-shared-1jf_aQziEO_DClIOc4k0P0BWfdO71pLLntV7rsUXV7Y"
MODEL = "qwen3.5-397b"
N_WORKERS = 8

PROMPT = (
    "You are labeling a head CT radiology report. Based ONLY on the IMPRESSION "
    "and FINDINGS, classify the scan as exactly one word: 'Positive' if it shows "
    "an ACUTE clinically significant intracranial finding (hemorrhage, infarct, "
    "acute fracture, mass effect, midline shift, acute edema, hydrocephalus), or "
    "'Negative' if there is no acute finding. Even if the report also says 'no "
    "hemorrhage', answer Positive if ANY acute finding is present. Answer with "
    "only the single word.\n\nREPORT:\n{report}"
)

# Regex label (Positive vs Negative), mirroring Classifying CT reports.sql.
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
    txt = (d["choices"][0]["message"].get("content") or "").strip().lower()
    if "positive" in txt:
        return "Positive"
    if "negative" in txt:
        return "Negative"
    return f"?{txt[:15]}"


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    df = pd.read_csv(REPORTS)
    df = df.drop_duplicates("note_id").reset_index(drop=True)
    print(f"{len(df)} unique reports to label.")

    done = {}
    if CHECKPOINT.exists():
        ck = pd.read_csv(CHECKPOINT)
        done = dict(zip(ck["note_id"], ck["llm_label"]))
        print(f"Resuming: {len(done)} already labeled.")

    todo = df[~df["note_id"].isin(done)]
    print(f"{len(todo)} remaining. Running with {N_WORKERS} workers...\n")

    results, errors, t0 = dict(done), 0, time.time()

    def work(rec):
        try:
            return rec["note_id"], llm_label(rec["text"]), None
        except Exception as e:
            return rec["note_id"], "ERR", f"{type(e).__name__}:{e}"

    with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
        futs = [ex.submit(work, r) for _, r in todo.iterrows()]
        for i, f in enumerate(as_completed(futs), 1):
            nid, lab, err = f.result()
            results[nid] = lab
            if err:
                errors += 1
            if i % 200 == 0 or i == len(futs):
                pd.DataFrame({"note_id": list(results), "llm_label": list(results.values())}
                             ).to_csv(CHECKPOINT, index=False)
                el = time.time() - t0
                print(f"  {i}/{len(futs)} | {errors} errors | {el:.0f}s "
                      f"| ~{el/max(i,1)*len(futs):.0f}s total")

    # merge + regex + report
    df["llm_label"] = df["note_id"].map(results)
    df["regex_label"] = df["text"].apply(regex_label)
    df[["note_id", "subject_id", "hadm_id", "regex_label", "llm_label"]].to_csv(
        RESULT, index=False)

    both = df[df["llm_label"].isin(["Positive", "Negative"]) &
              df["regex_label"].isin(["Positive", "Negative"])]
    agree = (both["llm_label"] == both["regex_label"]).sum()
    print("\n" + "=" * 60)
    print(f"Comparable (both Pos/Neg): {len(both)} / {len(df)}")
    print(f"Agreement: {agree}/{len(both)} = {agree/len(both):.1%}")
    print("\nConfusion (rows=regex, cols=LLM):")
    print(pd.crosstab(both["regex_label"], both["llm_label"]))

    # the key finding: regex=Negative but LLM=Positive (suspected regex misses)
    dis = both[(both["regex_label"] == "Negative") & (both["llm_label"] == "Positive")]
    print(f"\nregex=Negative but LLM=Positive (suspected FALSE NEGATIVES): {len(dis)}")
    print(f"  = {len(dis)}/{(both['regex_label']=='Negative').sum()} "
          f"of regex-Negatives flagged for review")
    df[df["note_id"].isin(dis["note_id"])][
        ["note_id", "subject_id", "hadm_id", "regex_label", "llm_label", "text"]
    ].to_csv(DISAGREE, index=False)
    print(f"\nSaved: {RESULT.name}, {DISAGREE.name} (disagreements for clinician review)")


if __name__ == "__main__":
    main()
