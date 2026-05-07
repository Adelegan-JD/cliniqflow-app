import { useEffect, useState } from "react";
import { api } from "../../utils/api";
import { CalendarDays, Clock3, FileText, Search, UserSquare2 } from "lucide-react";

export default function RecordOfficerRecords() {
  const [records, setRecords] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setIsLoading(true);
      setError("");
      try {
        const data = await api.get("/record-officer/dashboard");
        const todayRecords = Array.isArray(data?.todayRecords) ? data.todayRecords : [];
        if (!cancelled) setRecords(todayRecords);
      } catch (err) {
        if (!cancelled) {
          setError(err?.message || "Failed to load today's records");
          setRecords([]);
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const filteredRecords = records.filter((r) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return (
      (r.pid || "").toLowerCase().includes(q) ||
      (r.name || "").toLowerCase().includes(q) ||
      (r.registeredBy || "").toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold text-gray-900">Today's Patient Records</h1>
        {/* <p className="text-gray-600">
          Patients registered today, using the <code>patients</code> table, with date/time and the record officer on duty.
        </p> */}
      </div>

      <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-200 flex flex-col md:flex-row md:items-center gap-4 md:justify-between">
          <div>
            <div className="flex items-center gap-2 text-gray-700 font-semibold">
              <FileText size={18} className="text-blue-600" />
              Records for Today
            </div>
            <p className="text-sm text-gray-500 mt-1">Total records: {records.length}</p>
          </div>

          <div className="relative w-full md:max-w-md">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by PID, name, or officer..."
              className="w-full rounded-lg border border-gray-200 pl-10 pr-4 py-2 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
        </div>

        {error && (
          <div className="m-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading today's records...</div>
        ) : filteredRecords.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No patient records found for today.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr className="text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                  <th className="px-6 py-4">PID</th>
                  <th className="px-6 py-4">Patient Name</th>
                  <th className="px-6 py-4">Date</th>
                  <th className="px-6 py-4">Time</th>
                  <th className="px-6 py-4">Record Officer</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {filteredRecords.map((record) => (
                  <tr key={record.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-medium text-blue-700">{record.pid || "—"}</td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-gray-900">{record.name || "—"}</div>
                      {record.otherNames ? (
                        <div className="text-xs text-gray-500">Other names: {record.otherNames}</div>
                      ) : null}
                    </td>
                    <td className="px-6 py-4 text-gray-700">
                      <div className="flex items-center gap-2">
                        <CalendarDays size={16} className="text-gray-400" />
                        {record.date || "—"}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-700">
                      <div className="flex items-center gap-2">
                        <Clock3 size={16} className="text-gray-400" />
                        {record.time || "—"}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-700">
                      <div className="flex items-center gap-2">
                        <UserSquare2 size={16} className="text-gray-400" />
                        {record.registeredBy || "—"}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
