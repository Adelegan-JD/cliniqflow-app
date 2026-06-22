import React, { useEffect, useMemo, useState } from "react";
import { AlertCircle, Loader2, Search, Users } from "lucide-react";
import { api } from "../../utils/api";

const NurseQueueAwareness = () => {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await api.get("/doctor/nurse-queue-awareness");
        if (!mounted) return;
        setRows(Array.isArray(data) ? data : []);
      } catch (err) {
        if (!mounted) return;
        setError("Failed to load nurse triage queue.");
        setRows([]);
      } finally {
        if (mounted) setLoading(false);
      }
    };

    load();
    const timer = setInterval(load, 30000);

    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, []);

  const filteredRows = useMemo(() => {
    const q = searchTerm.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((row) => {
      const fields = [row.patient_name, row.name, row.patient_id, row.patientId]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return fields.includes(q);
    });
  }, [rows, searchTerm]);

  return (
    <div className="transition-all duration-300 p-4 md:p-6 overflow-auto w-full bg-gray-50/50">
      <header className="mb-8">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-50 rounded-xl">
            <Users className="text-blue-600" size={32} />
          </div>
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
              Nurse Triage Queue
            </h1>
            <p className="text-gray-600 mt-1">
              Read-only view of patients awaiting nurse triage.
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
      </section>

      <section className="card elevated">
        {loading ? (
          <div className="flex items-center justify-center p-12">
            <Loader2 size={32} className="animate-spin text-blue-600" />
            <span className="ml-3 text-gray-600 font-medium">
              Loading triage queue...
            </span>
          </div>
        ) : filteredRows.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table-modern">
              <thead>
                <tr>
                  <th>Patient Name</th>
                  <th>Patient ID</th>
                  <th>Age / Gender</th>
                  <th>Urgency</th>
                  <th>Registered</th>
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((row, index) => (
                  <tr key={`${row.patient_id || row.patientId || index}`}>
                    <td className="font-semibold text-gray-900">
                      {row.patient_name || row.name || "—"}
                    </td>
                    <td className="font-mono text-xs text-gray-700">
                      {row.patient_id || row.patientId || "—"}
                    </td>
                    <td className="text-gray-700">
                      {row.age || "—"} / {row.gender || row.sex || "—"}
                    </td>
                    <td>
                      <span className="badge badge-warning">
                        {(row.urgency || "normal").toString().toUpperCase()}
                      </span>
                    </td>
                    <td className="text-gray-600 text-sm">
                      {row.created_at
                        ? new Date(row.created_at).toLocaleString()
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-12 text-center text-gray-500">
            <p className="font-medium text-lg text-gray-600">
              No patients in nurse triage queue
            </p>
          </div>
        )}
      </section>
    </div>
  );
};

export default NurseQueueAwareness;
