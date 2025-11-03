import React from "react";
import VoicebotEvaluationDashboard from "../dashboard";

export default function ReportList({ reports }) {
  if (reports.length === 0)
    return <p className="muted">No reports found.</p>;

  return (
    <div className="report-grid">
      {reports.map((r) => (
        <div key={r.name} className="report-item">
          <VoicebotEvaluationDashboard dataProp={r.data} />
        </div>
      ))}
    </div>
  );
}
