#!/usr/bin/env python3
"""
LLM-as-a-Judge Voicebot Evaluator
- Multi-prompt modular evaluation
- Ground-truth classification + similarity comparison
- Aggregates to a 0-100 final score
- Saves evaluation JSON to evaluations/<transcript_filename>.json
"""

import os
import json
import time
import re
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import openai
# from openai import OpenAI

openai.api_key = "sandlogic"
openai.api_base = "http://45.194.2.204:3535/v1"


# ---------- Config ----------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-5")  # change if needed
if not OPENAI_API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY in .env")

openai.api_key = OPENAI_API_KEY

# Weights for aggregation (final score out of 100)
WEIGHTS = {
    "quality": 0.30,
    "business": 0.30,
    "experience": 0.25,
    "compliance": 0.10,
    "ground_truth_similarity": 0.05
}

# Directory defaults
TRANSCRIPTS_DIR = Path("transcripts")
GOLD_DIR = Path("gold_flows")
OUT_DIR = Path("evaluations")
OUT_DIR.mkdir(exist_ok=True)

# ---------- Utilities ----------
def extract_json(text: str):
    """Attempt to extract JSON object from LLM text output robustly."""
    # First try to find a full {...} JSON blob in text.
    json_blob = None
    matches = re.findall(r"\{.*\}", text, flags=re.DOTALL)
    if matches:
        # choose the largest match (most likely to be the JSON)
        json_blob = max(matches, key=len)
    else:
        # fallback: try to replace single quotes with double quotes (best-effort)
        try:
            return json.loads(text)
        except:
            pass

    if not json_blob:
        raise ValueError("No JSON object found in LLM response.")

    # Clean and parse
    try:
        return json.loads(json_blob)
    except json.JSONDecodeError:
        # try to sanitize common issues
        sanitized = json_blob.replace("\n", " ").replace("'", '"')
        # remove trailing commas
        sanitized = re.sub(r",\s*}", "}", sanitized)
        sanitized = re.sub(r",\s*]", "]", sanitized)
        return json.loads(sanitized)

def llm_call(system_prompt: str, user_prompt: str, max_retries=2, temperature=0.2):
    """Call the OpenAI chat/completions endpoint (chat completion style)"""
    # Build messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    for attempt in range(max_retries + 1):
        try:
            resp = openai.ChatCompletion.create(
                model=MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=1000
            )
            text = resp["choices"][0]["message"]["content"].strip()
            return text
        except Exception as e:
            if attempt < max_retries:
                time.sleep(1 + attempt * 1.5)
                continue
            raise

# ---------- Focused evaluators (each returns dict with numeric fields + comments) ----------

def evaluate_quality(transcript: str):
    """Intent understanding, relevance, context continuity (each 0-10)"""
    system = "You are a conversation quality evaluator. Be objective and concise."
    prompt = (
        "Given the transcript below, rate the bot (only the bot messages) on:\n"
        "1) intent_understanding (0-10)\n"
        "2) response_relevance (0-10)\n"
        "3) context_continuity (0-10)\n\n"
        "Return only a JSON object with keys: intent_understanding, response_relevance, context_continuity, comments\n\n"
        "Transcript:\n\n" + transcript
    )
    raw = llm_call(system, prompt)
    parsed = extract_json(raw)
    return parsed

def evaluate_business(transcript: str):
    """Conversion, upsell/EMI attempt, escalation handling"""
    system = "You are an evaluator of sales effectiveness for EW/CCP voicebot calls."
    prompt = (
        "Given the transcript, score (numbers only):\n"
        "1) conversion_accuracy (0-15) -- how correctly the bot moves to the right business outcome (sale/lead/callback/negative)\n"
        "2) upsell_emi (0-5) -- did it attempt appropriate upsell or EMI when relevant?\n"
        "3) escalation_accuracy (0-10) -- did bot escalate to human when required?\n\n"
        "Return only JSON: {\"conversion_accuracy\":..., \"upsell_emi\":..., \"escalation_accuracy\":..., \"comments\":\"\"}\n\n"
        "Transcript:\n\n" + transcript
    )
    raw = llm_call(system, prompt)
    parsed = extract_json(raw)
    return parsed

def evaluate_experience(transcript: str):
    """Empathy, interruption handling, politeness/clarity"""
    system = "You judge user experience for a customer service voicebot."
    prompt = (
        "Rate the bot for:\n"
        "1) empathy_tone (0-15)\n"
        "2) interruption_handling (0-10) -- e.g., when user says 'driving' or 'call later'\n"
        "3) politeness_clarity (0-5)\n\n"
        "Return JSON: {\"empathy_tone\":..., \"interruption_handling\":..., \"politeness_clarity\":..., \"comments\":\"\"}\n\n"
        "Transcript:\n\n" + transcript
    )
    raw = llm_call(system, prompt)
    parsed = extract_json(raw)
    return parsed

def evaluate_compliance(transcript: str):
    """Script adherence: introduction, verification, rules compliance, closing (each 0-5)"""
    system = "You are a compliance auditor checking script requirements."
    prompt = (
        "Check compliance with required script elements. Score each 0-5:\n"
        "1) introduction (bot introduced itself and mentioned 'recorded line')\n"
        "2) verification (bot checked name/model/VIN or registration)\n"
        "3) rules_compliance (escalation/disclaimer rules followed)\n"
        "4) closing (courteous closure and next steps)\n\n"
        "Return JSON with keys: introduction, verification, rules_compliance, closing, comments\n\n"
        "Transcript:\n\n" + transcript
    )
    raw = llm_call(system, prompt)
    parsed = extract_json(raw)
    return parsed

# ---------- Ground-truth modules ----------

def load_gold_flows(gold_dir=GOLD_DIR):
    """Load gold flows from files in gold_dir. Returns dict: {filename_stem: text}"""
    flows = {}
    if not gold_dir.exists():
        return flows
    for p in gold_dir.glob("*.txt"):
        key = p.stem
        flows[key] = p.read_text(encoding="utf-8")
    return flows

def classify_scenario(transcript: str, gold_keys):
    """
    Use LLM to classify which gold scenario the transcript best matches.
    Returns one of gold_keys or 'unknown'
    """
    system = "You classify the conversation into the most appropriate scenario label from the provided list."
    choices_list = ", ".join(gold_keys) if gold_keys else "none"
    prompt = (
        f"Choose the single best matching label from: {choices_list}\n\n"
        "If none match well, return 'unknown'.\n\n"
        "Transcript:\n\n" + transcript
    )
    raw = llm_call(system, prompt)
    # Clean answer - return the label word only
    answer = raw.strip().splitlines()[0].strip()
    # normalize
    answer_clean = re.sub(r"[^\w_ -]", "", answer)
    if answer_clean in gold_keys:
        return answer_clean
    # try matching ignoring case
    for k in gold_keys:
        if k.lower() in answer_clean.lower() or answer_clean.lower() in k.lower():
            return k
    return "unknown"

def compare_with_ground_truth(transcript: str, gold_text: str):
    """
    Compare transcript to gold_text semantically and structurally.
    Returns scores:
      - structure_similarity (0-10)
      - content_coverage (0-10)
      - tone_match (0-10)
      - intent_alignment (0-10)
      - overall_similarity (0-100)
      - key_deviations (string)
    """
    system = "You are a comparison engine. Compare two customer service call transcripts."
    prompt = (
        "Compare GOLD (ideal reference) with TEST (actual bot transcript).\n\n"
        "Score (0-10):\n"
        "- structure_similarity (did the conversation follow the same sequence and checkpoints?)\n"
        "- content_coverage (were key product details, EMI, or eligibility mentioned?)\n"
        "- tone_match (politeness / empathy vs gold standard)\n"
        "- intent_alignment (did they reach same business outcome?)\n\n"
        "Also compute overall_similarity as an integer 0-100 (higher is better).\n\n"
        "Return JSON:\n"
        "{\n"
        "  \"structure_similarity\":int,\n"
        "  \"content_coverage\":int,\n"
        "  \"tone_match\":int,\n"
        "  \"intent_alignment\":int,\n"
        "  \"overall_similarity\":int,\n"
        "  \"key_deviations\":\"short human-readable summary\"\n"
        "}\n\n"
        "GOLD:\n" + gold_text + "\n\nTEST:\n" + transcript
    )
    raw = llm_call(system, prompt, temperature=0.15)
    parsed = extract_json(raw)
    return parsed

# ---------- Aggregator ----------
def aggregate(quality, business, experience, compliance, gt_similarity_obj):
    # Sum raw scores to a 0..raw_max scale as designed earlier
    # Maxes by metric:
    maxes = {
        "intent_understanding": 10,
        "response_relevance": 10,
        "context_continuity": 10,
        "conversion_accuracy": 15,
        "upsell_emi": 5,
        "escalation_accuracy": 10,
        "empathy_tone": 15,
        "interruption_handling": 10,
        "politeness_clarity": 5,
        "introduction": 5,
        "verification": 5,
        "rules_compliance": 5,
        "closing": 5,
        "overall_similarity": 100  # for ground-truth entry
    }

    # normalize each section to 0-1 then apply WEIGHTS to sum to 100
    # Quality section
    quality_score_raw = (
        quality.get("intent_understanding", 0) / maxes["intent_understanding"] +
        quality.get("response_relevance", 0) / maxes["response_relevance"] +
        quality.get("context_continuity", 0) / maxes["context_continuity"]
    ) / 3.0  # average 0-1
    quality_pct = quality_score_raw * 100

    # Business section
    business_score_raw = (
        business.get("conversion_accuracy", 0) / maxes["conversion_accuracy"] +
        business.get("upsell_emi", 0) / maxes["upsell_emi"] +
        business.get("escalation_accuracy", 0) / maxes["escalation_accuracy"]
    ) / 3.0
    business_pct = business_score_raw * 100

    # Experience
    experience_score_raw = (
        experience.get("empathy_tone", 0) / maxes["empathy_tone"] +
        experience.get("interruption_handling", 0) / maxes["interruption_handling"] +
        experience.get("politeness_clarity", 0) / maxes["politeness_clarity"]
    ) / 3.0
    experience_pct = experience_score_raw * 100

    # Compliance
    compliance_score_raw = (
        compliance.get("introduction", 0) / maxes["introduction"] +
        compliance.get("verification", 0) / maxes["verification"] +
        compliance.get("rules_compliance", 0) / maxes["rules_compliance"] +
        compliance.get("closing", 0) / maxes["closing"]
    ) / 4.0
    compliance_pct = compliance_score_raw * 100

    # Ground truth overall_similarity expected as 0..100
    gt_overall = gt_similarity_obj.get("overall_similarity", 0)
    gt_pct = max(0, min(100, int(gt_overall)))  # clamp

    # Weighted sum
    final_score = (
        WEIGHTS["quality"] * quality_pct +
        WEIGHTS["business"] * business_pct +
        WEIGHTS["experience"] * experience_pct +
        WEIGHTS["compliance"] * compliance_pct +
        WEIGHTS["ground_truth_similarity"] * gt_pct
    )

    # Build aggregated report
    report = {
        "per_section_pct": {
            "quality_pct": round(quality_pct, 2),
            "business_pct": round(business_pct, 2),
            "experience_pct": round(experience_pct, 2),
            "compliance_pct": round(compliance_pct, 2),
            "ground_truth_pct": round(gt_pct, 2)
        },
        "final_score": round(final_score, 2),
        "details": {
            "quality": quality,
            "business": business,
            "experience": experience,
            "compliance": compliance,
            "ground_truth_comparison": gt_similarity_obj
        }
    }
    return report

# ---------- Main evaluation runner ----------
def evaluate_transcript_file(transcript_path: Path, gold_flows: dict):
    transcript_text = transcript_path.read_text(encoding="utf-8")

    # 1. Run modular evaluations
    quality = evaluate_quality(transcript_text)
    business = evaluate_business(transcript_text)
    experience = evaluate_experience(transcript_text)
    compliance = evaluate_compliance(transcript_text)

    # 2. Ground-truth classification & comparison
    gold_keys = list(gold_flows.keys())
    selected_label = classify_scenario(transcript_text, gold_keys)
    if selected_label != "unknown":
        gt_obj = compare_with_ground_truth(transcript_text, gold_flows[selected_label])
    else:
        # fallback: if unknown, create neutral ground-truth object
        gt_obj = {
            "structure_similarity": 0,
            "content_coverage": 0,
            "tone_match": 0,
            "intent_alignment": 0,
            "overall_similarity": 0,
            "key_deviations": "No similar gold flow found (classification=unknown)."
        }

    # 3. Aggregate
    agg = aggregate(quality, business, experience, compliance, gt_obj)

    # 4. Save
    output = {
        "transcript_filename": transcript_path.name,
        "selected_gold_label": selected_label,
        "timestamp": int(time.time()),
        "raw_evaluations": {
            "quality": quality,
            "business": business,
            "experience": experience,
            "compliance": compliance,
            "ground_truth_comparison": gt_obj
        },
        "aggregated": agg
    }

    out_path = OUT_DIR / (transcript_path.stem + ".eval.json")
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return output

# ---------- CLI entrypoint ----------
def main():
    gold_flows = load_gold_flows()
    transcripts = sorted(TRANSCRIPTS_DIR.glob("*.txt"))
    if not transcripts:
        print("No transcripts found in 'transcripts/' - place .txt files there and re-run.")
        return

    print(f"Loaded {len(gold_flows)} gold flows. Evaluating {len(transcripts)} transcripts...")
    results = []
    for t in tqdm(transcripts):
        try:
            out = evaluate_transcript_file(t, gold_flows)
            results.append(out)
        except Exception as e:
            print(f"Failed to evaluate {t.name}: {e}")

    print("Done. Results saved in 'evaluations/' directory.")
    # print brief summary
    for r in results:
        fname = r["transcript_filename"]
        score = r["aggregated"]["final_score"]
        label = r["selected_gold_label"]
        print(f"- {fname}: final_score={score}, gold_label={label}")

if __name__ == "__main__":
    main()
