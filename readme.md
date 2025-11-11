
<img width="1730" height="856" alt="Screenshot 2025-11-03 123426" src="https://github.com/user-attachments/assets/cc462bc0-dc9e-45fa-be79-8b848886f3d3" />

<img width="952" height="748" alt="Screenshot 2025-11-03 123511" src="https://github.com/user-attachments/assets/98578a87-bfee-4f60-bc36-fb064ebdaf76" />

# Hybrid Metric-wise Voicebot Evaluator

## Overview
This project provides an intelligent evaluation framework for a **Voicebot Quality Analysis System**, designed to automatically assess call transcripts using a **hybrid LLM-based evaluation** approach.  
It evaluates voicebot performance across four key dimensions — **Quality**, **Business**, **Experience**, and **Compliance** — producing structured JSON outputs with clear scores, comments, and extracted proofs from the conversation.

The framework enables transparent, consistent, and explainable evaluation for enterprise-grade conversational AI systems.

---

## Features
- Automated LLM-driven transcript evaluation.
- Metric-wise scoring and per-section aggregation.
- Proof extraction: highlights transcript lines justifying each score.
- Weighted scoring across multiple categories.
- Structured and human-readable JSON reports.
- Integrates with a dashboard UI for visualization.

---

## Evaluation Framework

The evaluation is divided into four weighted categories, each containing multiple metrics. Every metric has a defined maximum score and contributes to the overall weighted result.

### 1. Quality (Weight: 35%)
Measures how accurately and contextually the bot handles conversations.

| Metric | Max | Description |
|---------|-----|-------------|
| Intent Understanding | 10 | Accuracy in identifying customer intent. |
| Response Relevance | 10 | Logical consistency and relevance of responses. |
| Context Continuity | 10 | Ability to maintain conversational context. |

---

### 2. Business (Weight: 30%)
Assesses how effectively the bot meets organizational and process goals.

| Metric | Max | Description |
|---------|-----|-------------|
| Conversion Accuracy | 15 | Success in achieving intended business outcomes. |
| Upsell/EMI Offers | 5 | Presence of relevant offers or upsell attempts. |
| Escalation Accuracy | 10 | Correct escalation handling when required. |

---

### 3. Experience (Weight: 25%)
Evaluates conversational tone, emotional intelligence, and user experience.

| Metric | Max | Description |
|---------|-----|-------------|
| Empathy & Tone | 15 | Friendliness, tone, and human-like warmth. |
| Interruption Handling | 10 | Smooth management of interruptions. |
| Politeness & Clarity | 5 | Courtesy and clear communication. |

---

### 4. Compliance (Weight: 10%)
Verifies adherence to operational and communication guidelines.

| Metric | Max | Description |
|---------|-----|-------------|
| Introduction | 5 | Proper greeting and call disclosure. |
| Verification | 5 | Validation of customer or case details. |
| Rules Compliance | 5 | Following internal or legal communication rules. |
| Closing | 5 | Professional and polite call conclusion. |

---

## Scoring Methodology

Each section’s score is calculated using the ratio of total metric scores to their maximum possible scores, followed by weighted aggregation across all sections.

**Formulas:**
Section Score (%) = (Sum of Metric Scores / Sum of Metric Max) × 100
Final Score = Σ (Section Score × Section Weight)

yaml
Copy code

**Example Calculation:**

| Section | Score % | Weight | Weighted Contribution |
|----------|----------|---------|-----------------------|
| Quality | 80% | 0.35 | 28.0 |
| Business | 73% | 0.30 | 21.9 |
| Experience | 90% | 0.25 | 22.5 |
| Compliance | 100% | 0.10 | 10.0 |
| **Final Weighted Score** | — | — | **82.4 / 100** |

---

## Output Format (Example)

```json
{
  "transcript_filename": "1.txt",
  "timestamp": 1762148443,
  "sections": {
    "quality": {
      "metrics": [
        {
          "name": "intent_understanding",
          "score": 8.0,
          "max": 10,
          "comments": "The bot correctly identified the customer’s intent to renew the warranty.",
          "proof": "Customer: Yes, please go ahead."
        }
      ],
      "total_score": 24.0,
      "max_score": 30,
      "percentage": 80.0
    }
  },
  "aggregated": {
    "final_weighted_score": 82.5
  }
}
```
Workflow
The evaluator reads transcript text files from a directory.

Each transcript is processed through structured LLM prompts.

The model outputs metric-level scores, comments, and proof segments.

The system aggregates section-wise and overall results.

All evaluations are saved as JSON reports for review or visualization.

Dashboard UI (Optional)
A companion frontend built using React + Tailwind CSS can be integrated for:

Searching and filtering evaluated transcripts.

Viewing metric-level insights and extracted proofs.

Comparing overall performance across different transcripts.

Weight Justification
Category	Weight	Justification
Quality (35%)	Primary indicator of core conversational accuracy and logic.	
Business (30%)	Measures contribution toward business outcomes.	
Experience (25%)	Reflects user satisfaction and emotional tone.	
Compliance (10%)	Ensures adherence to process and legal standards.	

Summary
The Hybrid Metric-wise Voicebot Evaluator delivers transparent, explainable, and scalable voicebot evaluation.
It integrates structured metric scoring, weighted aggregation, and LLM-based judgment to produce reliable and interpretable assessments of conversational AI systems.

Tech Stack
Component	Technology
Backend	Python, dotenv, OpenAI API
Frontend (Optional)	React, Tailwind CSS, Vite
Output Format	JSON
Evaluation Logic	Metric-wise LLM evaluation using structured prompts

License
This project is intended for research and internal evaluation purposes related to automated voicebot quality analysis.

Author
Hrishikesh Vastrad
AI Engineer Trainee, SandLogic Technologies
Email: hrishivastrad14@gmail.com
