import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  CheckCircle2,
  Calendar,
  Clock,
  Users,
  Search,
  Filter,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { api } from "../../utils/api";

const TriageRecords = () => {
  const navigate = useNavigate();
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [urgencyFilter, setUrgencyFilter] = useState("all");

  useEffect(() => {
    let mounted = true;

    const loadRecords = async () => {
      setLoading(true);
      setError("");
      try {
        const data = await api.get("/nurse/triage-records");
        if (!mounted) return;
        setRecords(Array.isArray(data) ? data : []);
      } catch (err) {
        if (!mounted) return;
        console.error("Failed to load triage records:", err);
        setError("Failed to load triage records. Please try again.");
        setRecords([]);
      } finally {
        if (mounted) setLoading(false);
      }
    };

    loadRecords();
    const interval = setInterval(loadRecords, 60000); // Refresh every 60 seconds

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  // Filter records based on search and urgency
  const filteredRecords = records.filter((record) => {
    const matchesSearch =
      record.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      record.patient_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      record.patientId?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      record.patient_id?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesUrgency =
      urgencyFilter === "all" ||
      (record.urgencyLevel || record.urgency || "normal").toLowerCase() ===
        urgencyFilter.toLowerCase();

    return matchesSearch && matchesUrgency;
  });

  // Calculate stats
  const stats = {
    total: records.length,
    critical: records.filter(
      (r) =>
        r.urgencyLevel === "critical" ||
        r.urgency === "critical" ||
        r.urgencyLevel === "emergency" ||
        r.urgency === "emergency",
    ).length,
    high: records.filter(
      (r) => r.urgencyLevel === "urgent" || r.urgency === "urgent",
    ).length,
    normal: records.filter(
      (r) =>
        (r.urgencyLevel === "normal" ||
          r.urgency === "normal" ||
          !r.urgencyLevel) &&
        r.urgencyLevel !== "urgent" &&
        r.urgency !== "urgent",
    ).length,
  };

  const formatDate = (dateString) => {
    if (!dateString) return "—";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return "—";
    }
  };

  const formatTime = (dateString) => {
    if (!dateString) return "—";
    try {
      const date = new Date(dateString);
      return date.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
      });
    } catch {
      return "—";
    }
  };

  const getUrgencyBadgeColor = (urgency) => {
    const level = (urgency || "normal").toLowerCase();
    if (level === "critical" || level === "emergency") return "badge-critical";
    if (level === "urgent") return "badge-warning";
    if (level === "normal") return "badge-success";
    return "badge-primary";
  };

  return (
    <div className="transition-all duration-300 p-4 md:p-6 overflow-auto w-full">
      <header className="mb-8">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-green-50 rounded-xl">
            <CheckCircle2 className="text-green-600" size={32} />
          </div>
          <div>
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
              Triage Results
            </h1>
            <p className="text-gray-600 mt-1">
              View all completed patient triage records with timestamps
            </p>
          </div>
        </div>
      </header>

      {error ? (
        <div className="alert alert-error mb-6">
          <AlertCircle size={20} className="shrink-0" />
          <div>
            <p className="font-semibold">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      ) : null}

      {/* Stats Cards */}
      <section className="mb-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="stat-card">
            <p className="stat-card-label">Total Triaged</p>
            <p className="stat-card-value">{stats.total}</p>
          </div>
          <div className="stat-card">
            <p className="stat-card-label">Critical</p>
            <p className="stat-card-value text-red-600">{stats.critical}</p>
          </div>
          <div className="stat-card">
            <p className="stat-card-label">Urgent</p>
            <p className="stat-card-value text-amber-600">{stats.high}</p>
          </div>
          <div className="stat-card">
            <p className="stat-card-label">Normal</p>
            <p className="stat-card-value text-green-600">{stats.normal}</p>
          </div>
        </div>
      </section>

      {/* Filter Section */}
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
              <option value="all">All Urgency Levels</option>
              <option value="critical">Critical / Emergency</option>
              <option value="urgent">Urgent</option>
              <option value="normal">Normal</option>
            </select>
          </div>
        </div>
      </section>

      {/* Records Table */}
      <section className="card elevated">
        {loading ? (
          <div className="flex items-center justify-center p-12">
            <Loader2 size={32} className="animate-spin text-blue-600" />
            <span className="ml-3 text-gray-600 font-medium">
              Loading triage records...
            </span>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="table-modern">
                <thead>
                  <tr>
                    <th>Patient Name</th>
                    <th>Age / Gender</th>
                    <th>Urgency Level</th>
                    <th>Date Triaged</th>
                    <th>Time Triaged</th>
                    <th>Chief Complaint</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredRecords.length > 0 ? (
                    filteredRecords.map((record, index) => (
                      <tr key={record.id || record.patientId || index}>
                        <td className="font-semibold text-gray-900">
                          {record.name || record.patient_name || "—"}
                        </td>
                        <td className="text-gray-700">
                          {record.age || "—"} /{" "}
                          {record.gender || record.sex || "—"}
                        </td>
                        <td>
                          <span
                            className={`badge ${getUrgencyBadgeColor(
                              record.urgencyLevel || record.urgency,
                            )}`}
                          >
                            {(
                              record.urgencyLevel ||
                              record.urgency ||
                              "Normal"
                            ).toUpperCase()}
                          </span>
                        </td>
                        <td className="text-gray-700">
                          <div className="flex items-center gap-2">
                            <Calendar size={16} className="text-gray-400" />
                            {formatDate(record.triagedAt || record.created_at)}
                          </div>
                        </td>
                        <td className="text-gray-700">
                          <div className="flex items-center gap-2">
                            <Clock size={16} className="text-gray-400" />
                            {formatTime(record.triagedAt || record.created_at)}
                          </div>
                        </td>
                        <td className="text-gray-700 text-sm">
                          {record.chief_complaint ||
                            record.chiefComplaint ||
                            "—"}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        colSpan={6}
                        className="text-center py-8 text-gray-500"
                      >
                        <Users size={32} className="mx-auto mb-2 opacity-50" />
                        <p className="text-sm font-medium">
                          No triage records found
                        </p>
                        <p className="text-xs">
                          {records.length === 0
                            ? "No patients have been triaged yet."
                            : "No records match your search criteria."}
                        </p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            {filteredRecords.length > 0 && (
              <div className="p-4 border-t border-gray-200 text-sm text-gray-600">
                Showing {filteredRecords.length} of {records.length} record
                {records.length !== 1 ? "s" : ""}
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
};

export default TriageRecords;
