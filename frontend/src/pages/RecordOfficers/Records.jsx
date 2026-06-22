import { useEffect, useState } from "react";
import { api } from "../../utils/api";
import {
  CalendarDays,
  Clock3,
  FileText,
  Search,
  UserSquare2,
  Calendar,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

// Format date to readable string (e.g., "May 10, 2026")
const formatDateForDisplay = (dateStr) => {
  const date = new Date(dateStr + "T00:00:00");
  return date.toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  });
};

export default function RecordOfficerRecords() {
  const [records, setRecords] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [selectedDate, setSelectedDate] = useState(() => {
    // Default to today's date in YYYY-MM-DD format
    const today = new Date();
    return today.toISOString().split("T")[0];
  });

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setIsLoading(true);
      setError("");
      try {
        // Fetch records for the selected date
        const params = new URLSearchParams();
        if (selectedDate) {
          params.append("date", selectedDate);
        }
        const data = await api.get(
          `/record-officer/records?${params.toString()}`,
        );
        const records = Array.isArray(data) ? data : [];
        if (!cancelled) setRecords(records);
      } catch (err) {
        if (!cancelled) {
          setError(err?.message || "Failed to load records");
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
  }, [selectedDate]);

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
    <div className="w-full min-h-full px-4 py-4 sm:px-6 lg:px-8">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold text-gray-900">Patient Records</h1>
          <p className="text-gray-600">
            View patient registrations by date. Select a date to see all
            registrations for that day.
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
          <div className="border-b border-gray-100 bg-linear-to-r from-blue-50 to-white p-4 sm:p-6">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
              <div className="min-w-0">
                <div className="flex items-center gap-3">
                  <div className="rounded-xl bg-blue-100 p-2.5 shrink-0">
                    <FileText size={20} className="text-blue-600" />
                  </div>
                  <div className="min-w-0">
                    <h2 className="font-bold text-lg text-gray-900 truncate">
                     
                    </h2>
                    <p className="text-sm text-gray-600 mt-0.5">
                      Showing registrations for{" "}
                      <span className="font-semibold text-blue-600">
                        {formatDateForDisplay(selectedDate)}
                      </span>
                    </p>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-3 ml-11">
                  Total records:{" "}
                  <span className="font-semibold">{records.length}</span>
                </p>
              </div>

              <div className="flex flex-col gap-3 sm:min-w-[320px]">
                <label className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                  Select Date
                </label>
                <div className="flex flex-wrap items-center gap-2 rounded-xl border border-gray-200 bg-white p-2 shadow-sm transition-shadow hover:shadow-md">
                  <button
                    onClick={() => {
                      const date = new Date(selectedDate);
                      date.setDate(date.getDate() - 1);
                      setSelectedDate(date.toISOString().split("T")[0]);
                    }}
                    className="rounded-lg p-2 text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900"
                    title="Previous day"
                  >
                    <ChevronLeft size={18} />
                  </button>
                  <div className="flex min-w-0 flex-1 items-center gap-2 rounded-lg px-3 py-1.5">
                    <Calendar size={16} className="shrink-0 text-blue-500" />
                    <input
                      type="date"
                      value={selectedDate}
                      onChange={(e) => setSelectedDate(e.target.value)}
                      className="w-full min-w-0 cursor-pointer border-0 bg-transparent px-1 py-1 text-sm font-medium text-gray-700 outline-none focus:ring-0 hover:text-gray-900"
                    />
                  </div>
                  <button
                    onClick={() => {
                      const date = new Date(selectedDate);
                      date.setDate(date.getDate() + 1);
                      setSelectedDate(date.toISOString().split("T")[0]);
                    }}
                    className="rounded-lg p-2 text-gray-600 transition-colors hover:bg-gray-100 hover:text-gray-900"
                    title="Next day"
                  >
                    <ChevronRight size={18} />
                  </button>
                  <button
                    onClick={() => {
                      const today = new Date();
                      setSelectedDate(today.toISOString().split("T")[0]);
                    }}
                    className="rounded-lg px-3 py-2 text-xs font-semibold whitespace-nowrap text-blue-600 transition-colors hover:bg-blue-50"
                  >
                    Today
                  </button>
                </div>
              </div>
            </div>

            {/* Search Bar */}
            <div className="mt-6">
              <div className="relative w-full lg:max-w-md">
                <Search
                  size={18}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by PID, name, or officer..."
                  className="w-full rounded-xl border border-gray-200 bg-white py-3 pl-10 pr-4 text-sm outline-none transition focus:border-blue-400 focus:ring-2 focus:ring-blue-500/20"
                />
              </div>
            </div>
          </div>

          {error && (
            <div className="m-4 sm:m-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          {isLoading ? (
            <div className="p-10 sm:p-12 text-center">
              <div className="inline-flex items-center justify-center mb-4">
                <div className="relative h-10 w-10">
                  <div className="absolute inset-0 rounded-full bg-blue-200 animate-pulse"></div>
                  <Calendar
                    className="absolute inset-0 m-auto text-blue-600"
                    size={20}
                  />
                </div>
              </div>
              <p className="font-medium text-gray-700">
                Loading {formatDateForDisplay(selectedDate)} records...
              </p>
              <p className="mt-1 text-sm text-gray-500">Please wait</p>
            </div>
          ) : filteredRecords.length === 0 ? (
            <div className="p-10 sm:p-12 text-center">
              <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-gray-100 mb-4">
                <FileText size={24} className="text-gray-400" />
              </div>
              <p className="font-medium text-gray-700">
                No patient records found
              </p>
              <p className="mt-1 text-sm text-gray-500">
                No registrations on {formatDateForDisplay(selectedDate)}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr className="text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                    <th className="px-4 py-4 sm:px-6">PID</th>
                    <th className="px-4 py-4 sm:px-6">Patient Name</th>
                    <th className="px-4 py-4 sm:px-6">Date</th>
                    <th className="px-4 py-4 sm:px-6">Time</th>
                    <th className="px-4 py-4 sm:px-6">Record Officer</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {filteredRecords.map((record) => (
                    <tr key={record.id} className="hover:bg-gray-50">
                      <td className="px-4 py-4 sm:px-6 font-medium text-blue-700">
                        {record.pid || "—"}
                      </td>
                      <td className="px-4 py-4 sm:px-6">
                        <div className="font-medium text-gray-900">
                          {record.name || "—"}
                        </div>
                        {record.otherNames ? (
                          <div className="text-xs text-gray-500">
                            Other names: {record.otherNames}
                          </div>
                        ) : null}
                      </td>
                      <td className="px-4 py-4 sm:px-6 text-gray-700">
                        <div className="flex items-center gap-2">
                          <CalendarDays size={16} className="text-gray-400" />
                          {record.date || "—"}
                        </div>
                      </td>
                      <td className="px-4 py-4 sm:px-6 text-gray-700">
                        <div className="flex items-center gap-2">
                          <Clock3 size={16} className="text-gray-400" />
                          {record.time || "—"}
                        </div>
                      </td>
                      <td className="px-4 py-4 sm:px-6 text-gray-700">
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
    </div>
  );
}
