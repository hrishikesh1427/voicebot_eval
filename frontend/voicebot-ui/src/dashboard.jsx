// src/VoicebotEvaluationDashboard.jsx
import React from "react";
import data from "./data.json"; // or pass `data` prop

export default function VoicebotEvaluationDashboard({ dataProp }) {
  const dataObj = dataProp || data;
  const { transcript_filename, timestamp, sections, aggregated } = dataObj;

  return (
    <div className="app-container">
      <div className="report-header">
        <div className="report-title"></div>
        <div className="report-meta">
          <strong>Transcript:</strong> {transcript_filename} •{" "}
          {new Date(timestamp * 1000).toLocaleString()}
        </div>
      </div>

      <div className="section-card final-card" style={{ marginBottom: 18 }}>
        <div>
          <div className="final-label">Final Weighted Score</div>
          <div className="final-score">{aggregated.final_weighted_score.toFixed(2)}%</div>
        </div>

        <div style={{ minWidth: 260 }}>
          <div style={{ height: 10, background: "#e6eef6", borderRadius: 10 }}>
            <div
              style={{
                width: `${aggregated.final_weighted_score}%`,
                height: "100%",
                background: "linear-gradient(90deg,#06b6d4,#0ea5e9)",
                borderRadius: 10,
              }}
            />
          </div>
        </div>
      </div>

      <div className="sections-grid">
        {Object.entries(sections).map(([sectionKey, section]) => (
          <div key={sectionKey} className="section-card">
            <div className="section-header">
              <div className="section-title">{sectionKey}</div>
              <div className="section-badge">
                {section.total_score}/{section.max_score} ({section.percentage}%)
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {section.metrics.map((metric) => (
                <div className="metric" key={metric.name}>
                  <div className="metric-left">
                    <div className="metric-name">{metric.name.replace(/_/g, " ")}</div>
                    <div className="metric-comments">{metric.comments}</div>
                    {metric.proof ? (
                      <div className="metric-proof">“{metric.proof}”</div>
                    ) : (
                      <div className="muted">No proof available</div>
                    )}
                  </div>

                  <div className="metric-right">
                    <div className="metric-score">{metric.score}</div>
                    <div className="metric-max">/ {metric.max}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
