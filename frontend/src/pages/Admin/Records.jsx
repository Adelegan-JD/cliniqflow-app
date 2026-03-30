import { useEffect, useState } from "react";
import { FileText, Search } from "lucide-react";
import { api } from "../../utils/api";

export const Records = () => {
  const [patients, setPatients] = useState([]);
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPatients = async (q = "") => {
    setIsLoading(true);
    setError(null);
    try {
      const url = q
        ? `/record-officer/patients?search=${encodeURIComponent(q)}`
        : "/record-officer/patients";
      const data = await api.get(url);
      setPatients(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err?.message || "Failed to load records");
      setPatients([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPatients();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchPatients(search.trim());
  };

  return (
    <div className="flex flex-col flex-1 p-4 overflow-auto">
      <div>
        <h1 className="text-2xl font-bold mb-4">Patient Records</h1>
        <p className="text-gray-600 mb-6">
          View and search all registered patients. Patient ID (PID) is shown for each record.
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="p-6 border-b border-gray-200 flex flex-wrap items-center gap-3">
          <h2 className="text-xl font-semibold flex items-center gap-2 mr-auto">
            <FileText size={20} className="text-gray-600" />
            Records
          </h2>
          <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
            Total: {patients.length}
          </span>
          <form onSubmit={handleSearch} className="flex gap-2 flex-1 min-w-[200px] max-w-md">
            <div className="relative flex-1">
              <Search
                size={18}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
              />
              <input
                type="text"
                placeholder="Search by PID, name, phone..."
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700"
            >
              Search
            </button>
          </form>
        </div>

        {error && (
          <div className="mx-6 mt-4 p-3 bg-red-50 text-red-700 border-l-4 border-red-500 rounded">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading records...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-gray-50 text-gray-600 text-sm uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-4 font-medium">PID</th>
                  <th className="px-6 py-4 font-medium">Name</th>
                  <th className="px-6 py-4 font-medium">Age</th>
                  <th className="px-6 py-4 font-medium">Sex</th>
                  <th className="px-6 py-4 font-medium">Phone</th>
                  <th className="px-6 py-4 font-medium">Visits</th>
                  <th className="px-6 py-4 font-medium">Last Visit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {patients.length > 0 ? (
                  patients.map((p) => (
                    <tr key={p.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 font-medium text-blue-600">
                        {p.pid || p.id || "—"}
                      </td>
                      <td className="px-6 py-4">{p.name || "—"}</td>
                      <td className="px-6 py-4">{p.age ?? "—"}</td>
                      <td className="px-6 py-4 capitalize">
                        {(p.sex || p.gender || "—").toLowerCase()}
                      </td>
                      <td className="px-6 py-4">{p.phone || "—"}</td>
                      <td className="px-6 py-4">{p.previousVisits ?? 0}</td>
                      <td className="px-6 py-4">{p.lastVisit || "—"}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="7" className="px-6 py-8 text-center text-gray-500">
                      No records found. {search ? "Try a different search." : ""}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
