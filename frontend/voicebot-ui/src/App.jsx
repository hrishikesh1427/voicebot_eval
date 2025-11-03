import React, { useEffect, useState } from "react";
import ReportList from "./components/ReportList";
import "./index.css";

export default function App() {
  const [reports, setReports] = useState([]);
  const [search, setSearch] = useState("");

  // Load all JSON files from /src/results
  useEffect(() => {
    const modules = import.meta.glob("./results/evaluations/*.json", { eager: true });
    const loadedReports = Object.entries(modules).map(([path, content]) => ({
      path,
      name: path.split("/").pop(),
      data: content.default || content,
    }));

    // Sort newest first by timestamp if available
    loadedReports.sort((a, b) => (b.data.timestamp || 0) - (a.data.timestamp || 0));
    setReports(loadedReports);
  }, []);

  const filtered = reports.filter((r) =>
    r.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="app-container">
      <div className="report-header">
        <h1 className="report-title">Voicebot Evaluation Reports</h1>
        <input
          type="text"
          placeholder="Search by transcript name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="search-input"
        />
      </div>

      <ReportList reports={filtered} />
    </div>
  );
}
