# #!/usr/bin/env python3
# """
# Hybrid Metric-wise Voicebot Evaluator
# - Evaluates each metric individually using strict JSON prompts
# - Reads API credentials from .env
# - Saves outputs in evaluations/ directory
# """

# import os
# import json
# import re
# import time
# from pathlib import Path
# from dotenv import load_dotenv
# from tqdm import tqdm
# import openai


# # ---------- Utility ----------
# def clean_json_string(raw: str):
#     """Sanitize common LLM formatting issues."""
#     if not raw:
#         return raw
#     raw = raw.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
#     raw = raw.replace("customer\"s", "customer's").replace("agent\"s", "agent's")
#     raw = re.sub(r'\\+', '', raw)
#     raw = re.sub(r'([{,]\s*)([A-Za-z0-9_]+)\s*:', r'\1"\2":', raw)
#     return raw


# def extract_json(text: str):
#     """Extract and fix JSON from LLM output."""
#     match = re.search(r"\{.*\}", text, flags=re.DOTALL)
#     if not match:
#         raise ValueError("No JSON found in LLM output.")
#     blob = clean_json_string(match.group(0))
#     try:
#         return json.loads(blob)
#     except json.JSONDecodeError as e:
#         print("[ERROR] JSON parsing failed:", e)
#         print("[DEBUG] Raw JSON:", blob[:250])
#         raise


# def llm_call(messages, model, temperature=0.2, max_retries=2):
#     """Call OpenAI-compatible API with retry logic."""
#     for attempt in range(max_retries + 1):
#         try:
#             resp = openai.ChatCompletion.create(
#                 model=model,
#                 messages=messages,
#                 temperature=temperature,
#                 max_tokens=1000
#             )
#             return resp["choices"][0]["message"]["content"].strip()
#         except Exception as e:
#             print(f"[WARN] LLM call failed (attempt {attempt+1}): {e}")
#             time.sleep(1.5 * attempt)
#     raise RuntimeError("LLM call failed after retries.")


# # ---------- Evaluator ----------
# class HybridEvaluator:
#     def __init__(self):
#         load_dotenv()

#         openai.api_key = os.getenv("OPENAI_API_KEY")
#         openai.api_base = os.getenv("OPENAI_API_BASE")
#         self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo")

#         if not openai.api_key or not openai.api_base:
#             raise RuntimeError("Missing OPENAI_API_KEY or OPENAI_API_BASE in .env")

#         self.TRANSCRIPTS_DIR = Path("transcripts")
#         self.OUT_DIR = Path("evaluations")
#         self.OUT_DIR.mkdir(exist_ok=True)

#         # Metric structure
#         self.METRICS = {
#             "quality": [
#                 {"name": "intent_understanding", "max": 10, "desc": "How well the bot understood customer intent"},
#                 {"name": "response_relevance", "max": 10, "desc": "Relevance of responses"},
#                 {"name": "context_continuity", "max": 10, "desc": "Context maintenance"}
#             ],
#             "business": [
#                 {"name": "conversion_accuracy", "max": 15, "desc": "Correct business outcome"},
#                 {"name": "upsell_emi", "max": 5, "desc": "Upsell/EMI offers"},
#                 {"name": "escalation_accuracy", "max": 10, "desc": "Escalation correctness"}
#             ],
#             "experience": [
#                 {"name": "empathy_tone", "max": 15, "desc": "Empathy and tone"},
#                 {"name": "interruption_handling", "max": 10, "desc": "Handling interruptions"},
#                 {"name": "politeness_clarity", "max": 5, "desc": "Politeness and clarity"}
#             ],
#             "compliance": [
#                 {"name": "introduction", "max": 5, "desc": "Proper introduction and recorded line"},
#                 {"name": "verification", "max": 5, "desc": "Customer/vehicle verification"},
#                 {"name": "rules_compliance", "max": 5, "desc": "Disclaimers and escalation rules"},
#                 {"name": "closing", "max": 5, "desc": "Courteous closing"}
#             ]
#         }

#         self.WEIGHTS = {
#             "quality": 0.35,
#             "business": 0.30,
#             "experience": 0.25,
#             "compliance": 0.10
#         }

#     def metric_prompt(self, section: str, metric: dict, transcript: str):
#         """Strict JSON-only prompt for one metric."""
#         example = {
#             metric["name"]: metric["max"] // 2,
#             "comments": "Example: moderate performance."
#         }
#         example_str = json.dumps(example, indent=2)
#         return (
#             f"You are an expert evaluator for a Maruti Suzuki voicebot.\n"
#             f"Evaluate ONLY the metric '{metric['name']}' from the '{section}' category.\n"
#             f"Description: {metric['desc']}\n"
#             f"Score scale: 0 (worst) to {metric['max']} (best).\n\n"
#             "Output only valid JSON with these 2 keys:\n"
#             f"- {metric['name']} (numeric)\n- comments (string)\n\n"
#             f"Example:\n{example_str}\n\n"
#             f"Transcript:\n{transcript}"
#         )

#     def evaluate_metric(self, section: str, metric: dict, transcript: str):
#         """Call LLM for one metric."""
#         messages = [
#             {"role": "system", "content": f"Evaluate the voicebot's {section} performance."},
#             {"role": "user", "content": self.metric_prompt(section, metric, transcript)}
#         ]
#         print(messages)
#         raw = llm_call(messages, model=self.model)
#         raw = clean_json_string(raw)
#         data = extract_json(raw)

#         score = float(data.get(metric["name"], 0))
#         comments = data.get("comments", "")
#         return {metric["name"]: score, "comments": comments}

#     def evaluate_transcript(self, file_path: Path):
#         """Evaluate full transcript section by section."""
#         print(f"[INFO] Evaluating transcript: {file_path.name}")
#         text = file_path.read_text(encoding="utf-8")
#         section_results = {}

#         for section, metrics in self.METRICS.items():
#             section_data = {}
#             for metric in metrics:
#                 try:
#                     res = self.evaluate_metric(section, metric, text)
#                     section_data.update(res)
#                 except Exception as e:
#                     print(f"[ERROR] {section}:{metric['name']} -> {e}")
#                     section_data[metric["name"]] = 0
#                     section_data["comments"] = str(e)
#             section_results[section] = section_data

#         aggregated = self.aggregate(section_results)
#         out = {
#             "transcript_filename": file_path.name,
#             "timestamp": int(time.time()),
#             "raw_evaluations": section_results,
#             "aggregated": aggregated
#         }

#         out_path = self.OUT_DIR / f"{file_path.stem}.eval.json"
#         out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
#         print(f"[SUCCESS] Saved: {out_path}")
#         return out

#     def aggregate(self, results: dict):
#         """Compute weighted final score."""
#         per_section = {}
#         final = 0
#         for section, metrics in self.METRICS.items():
#             total = sum(results[section].get(m["name"], 0) for m in metrics)
#             max_total = sum(m["max"] for m in metrics)
#             pct = (total / max_total) * 100 if max_total else 0
#             weighted = pct * self.WEIGHTS[section]
#             per_section[section] = round(pct, 2)
#             final += weighted
#         return {"per_section_pct": per_section, "final_score": round(final, 2)}

#     def run(self):
#         """Run evaluator for all transcripts."""
#         files = list(self.TRANSCRIPTS_DIR.glob("*.txt"))
#         if not files:
#             print("No transcripts found in transcripts/ folder.")
#             return

#         print(f"Evaluating {len(files)} transcript(s)...\n")
#         for f in tqdm(files):
#             self.evaluate_transcript(f)

#         print("\n✅ Done. All results saved in 'evaluations/' folder.")


# # ---------- Entry ----------
# if __name__ == "__main__":
#     HybridEvaluator().run()






#!/usr/bin/env python3
"""
Hybrid Metric-wise Voicebot Evaluator (Production Version)
- Evaluates each metric individually using strict JSON prompts
- Reads API credentials from .env
- Includes 'proof' and 'max' fields in JSON
- Computes section totals and weighted overall score
- Saves structured outputs in evaluations/ directory
"""

import os
import json
import re
import time
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import openai


# ---------- Utility ----------
def clean_json_string(raw: str):
    """Sanitize common LLM formatting issues."""
    if not raw:
        return raw
    raw = raw.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    raw = raw.replace("customer\"s", "customer's").replace("agent\"s", "agent's")
    raw = re.sub(r'\\+', '', raw)
    raw = re.sub(r'([{,]\s*)([A-Za-z0-9_]+)\s*:', r'\1"\2":', raw)
    return raw


def extract_json(text: str):
    """Extract and fix JSON from LLM output."""
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("No JSON found in LLM output.")
    blob = clean_json_string(match.group(0))
    try:
        return json.loads(blob)
    except json.JSONDecodeError as e:
        print("[ERROR] JSON parsing failed:", e)
        print("[DEBUG] Raw JSON:", blob[:250])
        raise


def llm_call(messages, model, temperature=0.2, max_retries=2):
    """Call OpenAI-compatible API with retry logic."""
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
            print(f"[WARN] LLM call failed (attempt {attempt+1}): {e}")
            time.sleep(1.5 * attempt)
    raise RuntimeError("LLM call failed after retries.")


# ---------- Evaluator ----------
class HybridEvaluator:
    def __init__(self):
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")
        openai.api_base = os.getenv("OPENAI_API_BASE")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo")

        if not openai.api_key or not openai.api_base:
            raise RuntimeError("Missing OPENAI_API_KEY or OPENAI_API_BASE in .env")

        self.TRANSCRIPTS_DIR = Path("transcripts")
        self.OUT_DIR = Path("evaluations")
        self.OUT_DIR.mkdir(exist_ok=True)

        self.METRICS = {
            "quality": [
                {"name": "intent_understanding", "max": 10, "desc": "How well the bot understood customer intent"},
                {"name": "response_relevance", "max": 10, "desc": "Relevance of responses"},
                {"name": "context_continuity", "max": 10, "desc": "Context maintenance"}
            ],
            "business": [
                {"name": "conversion_accuracy", "max": 15, "desc": "Correct business outcome"},
                {"name": "upsell_emi", "max": 5, "desc": "Upsell/EMI offers"},
                {"name": "escalation_accuracy", "max": 10, "desc": "Escalation correctness"}
            ],
            "experience": [
                {"name": "empathy_tone", "max": 15, "desc": "Empathy and tone"},
                {"name": "interruption_handling", "max": 10, "desc": "Handling interruptions"},
                {"name": "politeness_clarity", "max": 5, "desc": "Politeness and clarity"}
            ],
            "compliance": [
                {"name": "introduction", "max": 5, "desc": "Proper introduction and recorded line"},
                {"name": "verification", "max": 5, "desc": "Customer/vehicle verification"},
                {"name": "rules_compliance", "max": 5, "desc": "Disclaimers and escalation rules"},
                {"name": "closing", "max": 5, "desc": "Courteous closing"}
            ]
        }

        self.WEIGHTS = {
            "quality": 0.35,
            "business": 0.30,
            "experience": 0.25,
            "compliance": 0.10
        }

    # ---------- Prompt ----------
    # def metric_prompt(self, section: str, metric: dict, transcript: str):
    #     """Strict JSON-only prompt for one metric."""
    #     return (
    #         f"You are an expert evaluator for a Maruti Suzuki voicebot.\n"
    #         f"Evaluate ONLY the metric '{metric['name']}' from the '{section}' category.\n"
    #         f"Description: {metric['desc']}\n"
    #         f"Score scale: 0 (worst) to {metric['max']} (best).\n\n"
    #         "Return ONLY valid JSON with the following keys:\n"
    #         f"- {metric['name']}: numeric score between 0 and {metric['max']}\n"
    #         "- comments: short reasoning (1-2 lines)\n"
    #         "- proof: exact line(s) or phrases from transcript that support the score\n\n"
    #         "Do NOT include examples, explanations, or text outside JSON.\n\n"
    #         f"Transcript:\n{transcript}"
    #     )
    def metric_prompt(self, section: str, metric: dict, transcript: str):
        """Production-grade JSON-only prompt for one Voicebot evaluation metric."""
        return f"""
    ROLE:
    You are an expert conversation quality evaluator for the Maruti Suzuki Voicebot.

    TASK:
    Evaluate the transcript provided below for the specific metric '{metric['name']}' under the '{section}' category.

    METRIC DETAILS:
    - Description: {metric['desc']}
    - Scoring Scale: 0 (worst) to {metric['max']} (best)

    EVALUATION FOCUS:
    - Assess only this single metric; ignore all others.
    - Base your judgment strictly on the agent’s and customer’s spoken interactions as shown in the transcript.
    - Remain objective — no assumptions or inferred meanings.

    SCORING REQUIREMENTS:
    - Assign one numeric score between 0 and {metric['max']}
    - Provide a brief reasoning (1–2 lines)
    - Extract verbatim supporting phrase(s) from the transcript

    OUTPUT FORMAT:
    ```json
    {{
    "{metric['name']}": <numeric_score_between_0_and_{metric['max']}>,
    "comments": "<short_reasoning>",
    "proof": "<exact_line_or_phrase_from_transcript>"
    }}
    CRITICAL INSTRUCTIONS:

    Respond ONLY with the JSON object shown above — no explanations, notes, or markdown.

    Ensure valid JSON (double quotes only, no trailing commas).

    The "proof" field must contain exact verbatim text from the transcript.

    If the transcript lacks evidence for this metric, return an empty string for "proof".

    TRANSCRIPT:
    {transcript}
"""
    # ---------- Metric Evaluation ----------
    def evaluate_metric(self, section: str, metric: dict, transcript: str):
        """Call LLM for one metric."""
        messages = [
            {"role": "system", "content": f"Evaluate the voicebot's {section} performance objectively."},
            {"role": "user", "content": self.metric_prompt(section, metric, transcript)}
        ]
        raw = llm_call(messages, model=self.model)
        raw = clean_json_string(raw)
        data = extract_json(raw)

        score = float(data.get(metric["name"], 0))
        comments = data.get("comments", "")
        proof = data.get("proof", "")

        return {
            "name": metric["name"],
            "score": score,
            "max": metric["max"],
            "comments": comments,
            "proof": proof
        }

    # ---------- Section Evaluation ----------
    def evaluate_transcript(self, file_path: Path):
        """Evaluate full transcript section by section."""
        print(f"[INFO] Evaluating transcript: {file_path.name}")
        text = file_path.read_text(encoding="utf-8")
        section_results = {}

        for section, metrics in self.METRICS.items():
            metrics_data = []
            for metric in metrics:
                try:
                    res = self.evaluate_metric(section, metric, text)
                    metrics_data.append(res)
                except Exception as e:
                    print(f"[ERROR] {section}:{metric['name']} -> {e}")
                    metrics_data.append({
                        "name": metric["name"],
                        "score": 0,
                        "max": metric["max"],
                        "comments": f"Error: {str(e)}",
                        "proof": ""
                    })

            # compute totals
            total_score = sum(m["score"] for m in metrics_data)
            max_score = sum(m["max"] for m in metrics_data)
            pct = round((total_score / max_score) * 100, 2) if max_score else 0

            section_results[section] = {
                "metrics": metrics_data,
                "total_score": round(total_score, 2),
                "max_score": max_score,
                "percentage": pct
            }

        aggregated = self.aggregate(section_results)
        out = {
            "transcript_filename": file_path.name,
            "timestamp": int(time.time()),
            "sections": section_results,
            "aggregated": aggregated
        }

        out_path = self.OUT_DIR / f"{file_path.stem}.eval.json"
        out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
        print(f"[SUCCESS] Saved: {out_path}")
        return out

    # ---------- Aggregation ----------
    def aggregate(self, results: dict):
        """Compute weighted final score."""
        final = 0
        for section, details in results.items():
            weighted = details["percentage"] * self.WEIGHTS[section]
            final += weighted
        return {"final_weighted_score": round(final, 2)}

    # ---------- Runner ----------
    def run(self):
        """Run evaluator for all transcripts."""
        files = list(self.TRANSCRIPTS_DIR.glob("*.txt"))
        if not files:
            print("No transcripts found in transcripts/ folder.")
            return

        print(f"Evaluating {len(files)} transcript(s)...\n")
        for f in tqdm(files):
            self.evaluate_transcript(f)

        print("\n✅ Done. All results saved in 'evaluations/' folder.")


# ---------- Entry ----------
if __name__ == "__main__":
    HybridEvaluator().run()
