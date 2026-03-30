import React, { useEffect, useState } from "react";
import { api } from "../utils/api";
import { User, FileText } from "lucide-react";
import { toast } from "react-toastify";

const PatientRecords = ({ headerSearchValue = "" }) => {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const params = headerSearchValue?.trim()
          ? new URLSearchParams({ search: headerSearchValue.trim() })
          : "";
        const data = await api.get(`/record-officer/patients${params ? `?${params}` : ""}`);
        if (!cancelled) setPatients(Array.isArray(data) ? data : []);
      } catch (err) {
        if (!cancelled) {
          toast.error(err.message || "Failed to load patients");
          setPatients([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [headerSearchValue]);

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
        <p className="text-gray-500">Loading patients...</p>
      </div>
    );
  }

  if (patients.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
        <FileText size={48} className="mx-auto text-gray-300 mb-4" />
        <p className="text-gray-600 font-medium">No patients found</p>
        <p className="text-gray-500 text-sm mt-1">
          Register a patient using the Register Patient tab to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
        <h3 className="font-semibold text-gray-800">Patient Records</h3>
        <p className="text-sm text-gray-500 mt-0.5">{patients.length} patient(s)</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-gray-50 text-gray-600 text-sm uppercase">
            <tr>
              <th className="px-6 py-3 font-medium">Patient</th>
              <th className="px-6 py-3 font-medium">PID</th>
              <th className="px-6 py-3 font-medium">Age / Sex</th>
              <th className="px-6 py-3 font-medium">Phone</th>
              <th className="px-6 py-3 font-medium">Visits</th>
              <th className="px-6 py-3 font-medium">Last Visit</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {patients.map((p) => (
              <tr key={p.id} className="hover:bg-gray-50">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                      <User size={14} className="text-blue-600" />
                    </div>
                    <span className="font-medium text-gray-800">{p.name}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-gray-600 text-sm font-mono">{p.pid || p.id}</td>
                <td className="px-6 py-4 text-gray-600">
                  {p.age ?? "—"} / {p.sex ?? "—"}
                </td>
                <td className="px-6 py-4 text-gray-600">{p.phone || "—"}</td>
                <td className="px-6 py-4 text-gray-600">{p.previousVisits ?? 0}</td>
                <td className="px-6 py-4 text-gray-600">{p.lastVisit ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default PatientRecords;
