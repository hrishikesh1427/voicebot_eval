#!/usr/bin/env python3
"""
LLM-as-a-Judge Voicebot Evaluator (Strict JSON - Cleaned Version)
- Forces valid JSON response format with sample
- Fixes over-escaping issues from LLM
- Aggregates scores and saves JSON to evaluations/<transcript_filename>.json
"""

import os
import json
import time
import re
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import openai


# ---------- Utility Functions ----------
def clean_json_string(raw: str):
    """Clean and sanitize possible malformed JSON text."""
    # Fix invalid smart quotes
    raw = raw.replace("“", '"').replace("”", '"').replace("’", "'")
    # Fix escaped nonsense like \"\2 -> "
    raw = re.sub(r'\\+\"', '"', raw)
    # Fix customer"s → customer's
    raw = raw.replace('customer"s', "customer's")
    raw = raw.replace('agent"s', "agent's")
    raw = raw.replace('bot"s', "bot's")
    raw = raw.replace('voicebot"s', "voicebot's")
    return raw


def extract_json(text: str):
    """Extract JSON object robustly."""
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        print("[DEBUG] No JSON found in text, returning raw snippet")
        raise ValueError("No JSON object found.")
    json_blob = match.group(0)
    json_blob = clean_json_string(json_blob)
    try:
        return json.loads(json_blob)
    except json.JSONDecodeError as e:
        print(f"[WARN] JSON parse failed: {e}")
        print("[DEBUG] Raw JSON that failed:\n", json_blob[:300])
        raise


def llm_call(system_prompt: str, user_prompt: str, model: str, temperature=0.2, max_retries=2):
    """Call LLM with retries."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    for attempt in range(max_retries + 1):
        try:
            resp = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=1000
            )
            return resp["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"[ERROR] LLM call failed (attempt {attempt+1}): {e}")
            if attempt < max_retries:
                time.sleep(1 + attempt * 1.5)
                continue
            raise


# ---------- Main Evaluator ----------
class VoicebotEvaluator:
    def __init__(self):
        load_dotenv()

        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv("OPENAI_API_BASE")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo")

        if not self.api_key or not self.api_base:
            raise RuntimeError("Missing OPENAI_API_KEY or OPENAI_API_BASE in .env file")

        openai.api_key = self.api_key
        openai.api_base = self.api_base

        self.WEIGHTS = {
            "quality": 0.35,
            "business": 0.30,
            "experience": 0.25,
            "compliance": 0.10
        }

        self.TRANSCRIPTS_DIR = Path("transcripts")
        self.OUT_DIR = Path("evaluations")
        self.OUT_DIR.mkdir(exist_ok=True)

        self.METRICS = {
            "quality": [
                {"name": "intent_understanding", "max": 10, "desc": "How well the bot grasped the customer’s intent"},
                {"name": "response_relevance", "max": 10, "desc": "How relevant the bot’s replies were"},
                {"name": "context_continuity", "max": 10, "desc": "How smoothly context was maintained"}
            ],
            "business": [
                {"name": "conversion_accuracy", "max": 15, "desc": "Accuracy of driving toward the correct business outcome"},
                {"name": "upsell_emi", "max": 5, "desc": "Whether upsell or EMI options were offered appropriately"},
                {"name": "escalation_accuracy", "max": 10, "desc": "Whether escalation was done correctly when required"}
            ],
            "experience": [
                {"name": "empathy_tone", "max": 15, "desc": "Empathy and warmth in tone"},
                {"name": "interruption_handling", "max": 10, "desc": "Ability to handle interruptions"},
                {"name": "politeness_clarity", "max": 5, "desc": "Politeness and clarity of language"}
            ],
            "compliance": [
                {"name": "introduction", "max": 5, "desc": "Whether bot introduced itself and mentioned recorded line"},
                {"name": "verification", "max": 5, "desc": "Whether customer and vehicle details were verified"},
                {"name": "rules_compliance", "max": 5, "desc": "Whether disclaimers/escalation rules were followed"},
                {"name": "closing", "max": 5, "desc": "Whether closing was courteous and complete"}
            ]
        }

    def build_prompt(self, section_name, metrics, transcript):
        """Create strict but clean JSON prompt."""
        metric_lines = [f"- {m['name']} (0–{m['max']}): {m['desc']}" for m in metrics]
        metrics_text = "\n".join(metric_lines)
        keys = [m["name"] for m in metrics]
        keys_str = ", ".join(keys)

        example_json = {m["name"]: 5 for m in metrics}
        example_json["comments"] = "The bot clearly understood the intent and responded well."
        example_str = json.dumps(example_json, indent=2)

        prompt = (
            f"Evaluate the voicebot's {section_name} performance.\n"
            f"Metrics:\n{metrics_text}\n\n"
            "Output rules:\n"
            "1. Respond ONLY with a JSON object.\n"
            "2. Use normal double quotes (no extra slashes or escapes).\n"
            f"3. Include keys: {keys_str}, comments.\n"
            f"4. Follow this JSON format:\n\n{example_str}\n\n"
            f"Transcript:\n{transcript}\n"
        )
        return prompt

    def evaluate_section(self, section_name, transcript):
        metrics = self.METRICS[section_name]
        system = f"You are an expert evaluator assessing the {section_name} performance of a Maruti Suzuki voicebot."
        prompt = self.build_prompt(section_name, metrics, transcript)
        print(f"[DEBUG] Calling LLM for section: {section_name}")
        raw = llm_call(system, prompt, model=self.model)
        raw = clean_json_string(raw)
        parsed = extract_json(raw)
        print(f"[DEBUG] Parsed JSON for {section_name}: {list(parsed.keys())}")
        return parsed

    def aggregate(self, results):
        section_scores = {}
        total_score = 0
        for section, metrics in self.METRICS.items():
            if section not in results:
                continue
            max_total = sum(m["max"] for m in metrics)
            section_total = sum(results[section].get(m["name"], 0) for m in metrics)
            pct = (section_total / max_total) * 100 if max_total > 0 else 0
            weighted = pct * self.WEIGHTS[section]
            section_scores[section] = round(pct, 2)
            total_score += weighted

        return {
            "per_section_pct": section_scores,
            "final_score": round(total_score, 2),
            "details": results
        }

    def evaluate_transcript(self, path):
        print(f"\n[INFO] Evaluating transcript: {path.name}")
        text = path.read_text(encoding="utf-8")
        results = {}
        for section in self.METRICS.keys():
            try:
                results[section] = self.evaluate_section(section, text)
            except Exception as e:
                print(f"[ERROR] Failed {section}: {e}")
                results[section] = {}

        agg = self.aggregate(results)
        out = {
            "transcript_filename": path.name,
            "timestamp": int(time.time()),
            "raw_evaluations": results,
            "aggregated": agg
        }
        out_file = self.OUT_DIR / f"{path.stem}.eval.json"
        out_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"[SUCCESS] File saved: {out_file}")
        return out

    def run(self):
        transcripts = sorted(self.TRANSCRIPTS_DIR.glob("*.txt"))
        if not transcripts:
            print("No transcripts found in transcripts/.")
            return

        print(f"Evaluating {len(transcripts)} transcript(s)...\n")
        results = []
        for t in tqdm(transcripts):
            results.append(self.evaluate_transcript(t))

        print("\nDone. Results saved in 'evaluations/' directory.\n")
        for r in results:
            print(f"- {r['transcript_filename']}: Final Score = {r['aggregated']['final_score']}")


# ---------- Entrypoint ----------
if __name__ == "__main__":
    evaluator = VoicebotEvaluator()
    evaluator.run()
