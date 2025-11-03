
<img width="1730" height="856" alt="Screenshot 2025-11-03 123426" src="https://github.com/user-attachments/assets/cc462bc0-dc9e-45fa-be79-8b848886f3d3" />

<img width="952" height="748" alt="Screenshot 2025-11-03 123511" src="https://github.com/user-attachments/assets/98578a87-bfee-4f60-bc36-fb064ebdaf76" />

---

```markdown
# 🎙️ Hybrid Metric-wise Voicebot Evaluator

An intelligent evaluation framework for a **Voicebot Quality Analysis System**, designed to automatically assess call transcripts using a **hybrid LLM-based evaluation** method.  
It evaluates performance across four key dimensions — **Quality**, **Business**, **Experience**, and **Compliance** — producing structured JSON outputs with transparent scoring and proof extraction.

---

## 🚀 Features

- 🤖 **Automated evaluation** using LLMs (JSON-only prompts)
- 🧠 **Metric-wise scoring** for granular analysis
- 💬 **Proof extraction** – highlights exact voicebot utterances used to justify scores
- 📊 **Section-wise totals and weighted percentages**
- 💾 Generates readable and structured `.json` reports for each transcript
- 🖥️ Compatible with a **frontend dashboard UI** for visualization and filtering

---

## ⚙️ How It Works

1. Reads transcript text files automatically.  
2. Sends each to the LLM with structured metric-specific prompts.  
3. Receives strict JSON output (score, comments, proof).  
4. Aggregates per-metric, per-section, and final weighted scores.  
5. Saves output reports as JSON for easy review or visualization.

---

## 🧩 Evaluation Metrics

### **1️⃣ Quality (Weight: 35%)**
Focuses on how well the bot understands and maintains conversation context.

| Metric | Max | Description |
|---------|-----|-------------|
| **Intent Understanding** | 10 | How accurately the bot grasps the customer's intent. |
| **Response Relevance** | 10 | Logical and appropriate response quality. |
| **Context Continuity** | 10 | Ability to stay on topic and maintain context. |

---

### **2️⃣ Business (Weight: 30%)**
Evaluates whether the bot helps achieve intended business goals.

| Metric | Max | Description |
|---------|-----|-------------|
| **Conversion Accuracy** | 15 | Measures if the desired outcome (e.g., renewal, booking) is achieved. |
| **Upsell/EMI Offers** | 5 | Checks if upsell opportunities were offered. |
| **Escalation Accuracy** | 10 | Ensures proper escalation for complex cases. |

---

### **3️⃣ Experience (Weight: 25%)**
Assesses the emotional and human quality of the bot’s interaction.

| Metric | Max | Description |
|---------|-----|-------------|
| **Empathy & Tone** | 15 | Warmth, tone, and friendliness of the bot. |
| **Interruption Handling** | 10 | How well the bot manages interruptions or overlaps. |
| **Politeness & Clarity** | 5 | Professional and clear communication. |

---

### **4️⃣ Compliance (Weight: 10%)**
Ensures the bot follows standard communication and process protocols.

| Metric | Max | Description |
|---------|-----|-------------|
| **Introduction** | 5 | Proper greeting and mention of recorded line. |
| **Verification** | 5 | Confirms customer or vehicle details. |
| **Rules Compliance** | 5 | Follows required disclaimers and policies. |
| **Closing** | 5 | Ends the conversation courteously. |

---

## 🧮 Scoring Methodology

Each section’s metrics are individually evaluated and aggregated using weighted averages.

**Formulas:**

```

Section Score (%) = (Sum of Metric Scores / Sum of Metric Max) × 100
Final Score = Σ (Section Score × Section Weight)

````

**Example:**

| Section | Score % | Weight | Weighted Contribution |
|----------|----------|---------|-----------------------|
| Quality | 80% | 0.35 | 28.0 |
| Business | 73% | 0.30 | 21.9 |
| Experience | 90% | 0.25 | 22.5 |
| Compliance | 100% | 0.10 | 10.0 |
| **Final Weighted Score** | — | — | **82.4 / 100** |

---

## 🧠 Output Format (Example)

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
````

---

## 💻 Optional Dashboard UI

A companion dashboard built with **React + Tailwind CSS** is available for:

* Searching and filtering evaluation files
* Viewing metric-level comments and proofs
* Comparing transcripts by overall score

---

## 🧾 Weight Justification

| Category             | Weight                                                                                            | Justification |
| -------------------- | ------------------------------------------------------------------------------------------------- | ------------- |
| **Quality (35%)**    | Foundation of conversational AI — understanding user intent and context is critical for accuracy. |               |
| **Business (30%)**   | Directly affects ROI and customer conversions.                                                    |               |
| **Experience (25%)** | Influences brand perception and customer satisfaction.                                            |               |
| **Compliance (10%)** | Essential for process adherence but non-influential to dialogue quality.                          |               |

---

## 📊 Summary

This framework ensures balanced, transparent, and explainable evaluation of a voicebot system.
It emphasizes **comprehension**, **conversion**, **experience**, and **compliance**, enabling both **quantitative scoring** and **qualitative insights**.

---

## 🧠 Tech Stack

| Component               | Technology                                    |
| ----------------------- | --------------------------------------------- |
| **Backend**             | Python, dotenv, OpenAI API                    |
| **Frontend (Optional)** | React, Tailwind, Vite                         |
| **Output Format**       | JSON                                          |
| **Evaluation Method**   | Metric-wise LLM scoring with proof extraction |

---

## 🧾 License

This project is intended for internal evaluation and research purposes related to Voicebot Quality Analysis.

---

## ✉️ Contact

Developed by **Hrishikesh Vastrad**
📧 *[hrishivastrad14@gmail.com](mailto:hrishivastrad14@gmail.com])*

```



```
