import React, { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  Clock,
  Filter,
  Loader2,
  Search,
  Users,
} from "lucide-react";
import { api } from "../../utils/api";

const NurseTriageResults = () => {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [urgencyFilter, setUrgencyFilter] = useState("all");

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await api.get("/doctor/triaged-queue");
        if (!mounted) return;
        setRows(Array.isArray(data) ? data : []);
      } catch (err) {
        if (!mounted) return;
        setError("Failed to load triaged patients.");
        setRows([]);
      } finally {
        if (mounted) setLoading(false);
      }
    };

    load();
    const timer = setInterval(load, 60000);

    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, []);

  const filteredRows = useMemo(() => {
    const q = searchTerm.trim().toLowerCase();
    return rows.filter((row) => {
      const fields = [row.patient_name, row.name, row.patient_id, row.patientId]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      const urgency = (
        row.urgency_level ||
        row.urgency ||
        "normal"
      ).toLowerCase();
      const matchesSearch = !q || fields.includes(q);
      const matchesUrgency =
        urgencyFilter === "all" || urgency === urgencyFilter;
      return matchesSearch && matchesUrgency;
    });
  }, [rows, searchTerm, urgencyFilter]);

  const formatDate = (value) =>
    value ? new Date(value).toLocaleDateString() : "—";
  const formatTime = (value) =>
    value
      ? new Date(value).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        })
      : "—";

  return (
    <div className="transition-all duration-300 p-4 md:p-6 overflow-auto w-full bg-gray-50/50">
      <header className="mb-8">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-emerald-50 rounded-xl">
            <Users className="text-emerald-600" size={32} />
          </div>
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
              Triage Results
            </h1>
            <p className="text-gray-600 mt-1">
              Patients triaged and ready for consultation.
            </p>
          </div>
        </div>
      </header>

      {error ? (
        <div className="alert alert-warning mb-6">
          <AlertCircle size={20} className="shrink-0" />
          <div>
            <p className="font-semibold">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      ) : null}

      <section className="card elevated p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              <Search size={16} className="inline mr-2" />
              Search by name or ID
            </label>
            <input
              type="text"
              placeholder="Enter patient name or ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field w-full"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              <Filter size={16} className="inline mr-2" />
              Filter by urgency
            </label>
            <select
              value={urgencyFilter}
              onChange={(e) => setUrgencyFilter(e.target.value)}
              className="input-field w-full"
            >
              <option value="all">All</option>
              <option value="critical">Critical</option>
              <option value="emergency">Emergency</option>
              <option value="urgent">Urgent</option>
              <option value="normal">Normal</option>
            </select>
          </div>
        </div>
      </section>

      <section className="card elevated">
        {loading ? (
          <div className="flex items-center justify-center p-12">
            <Loader2 size={32} className="animate-spin text-blue-600" />
            <span className="ml-3 text-gray-600 font-medium">
              Loading triage records...
            </span>
          </div>
        ) : filteredRows.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table-modern">
              <thead>
                <tr>
                  <th>Patient Name</th>
                  <th>Age / Gender</th>
                  <th>Urgency</th>
                  <th>Date Triaged</th>
                  <th>Time Triaged</th>
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((row, index) => (
                  <tr key={`${row.patient_id || row.patientId || index}`}>
                    <td className="font-semibold text-gray-900">
                      {row.patient_name || row.name || "—"}
                    </td>
                    <td className="text-gray-700">
                      {row.age || "—"} / {row.gender || row.sex || "—"}
                    </td>
                    <td>
                      <span className="badge badge-success">
                        {(row.urgency_level || row.urgency || "normal")
                          .toString()
                          .toUpperCase()}
                      </span>
                    </td>
                    <td className="text-gray-700">
                      {formatDate(row.triaged_at || row.created_at)}
                    </td>
                    <td className="text-gray-700">
                      <div className="flex items-center gap-2">
                        <Clock size={16} className="text-gray-400" />
                        {formatTime(row.triaged_at || row.created_at)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-12 text-center text-gray-500">
            <p className="font-medium text-lg text-gray-600">
              No triage records found
            </p>
          </div>
        )}
      </section>
    </div>
  );
};

export default NurseTriageResults;
