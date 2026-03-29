import React, { useState } from "react";
import {
  Search,
  User,
  Calendar,
  Hash,
  Phone,
  ChevronRight,
  CheckCircle2,
  Clock,
} from "lucide-react";
import { api } from "../utils/api";
import { toast } from "react-toastify";

const DEPARTMENTS = [
  { value: "general", label: "General Outpatient" },
  { value: "pediatrics", label: "Pediatrics" },
  { value: "obgyn", label: "Obstetrics & Gynecology" },
  { value: "surgery", label: "Surgery" },
  { value: "emergency", label: "Emergency" },
];

const CreateVisit = () => {
  const [searchMode, setSearchMode] = useState("pid");
  const [searchValue, setSearchValue] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [reasonForVisit, setReasonForVisit] = useState("");
  const [department, setDepartment] = useState("");
  const [visitCreated, setVisitCreated] = useState(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!searchValue.trim()) return;
    setIsSearching(true);
    setSearchResults([]);
    try {
      const searchBy = searchMode === "pid" ? "pid" : searchMode === "phone" ? "phone" : "nameDob";
      const params = new URLSearchParams({ q: searchValue.trim(), search_by: searchBy });
      const data = await api.get(`/record-officer/patients/search?${params}`);
      setSearchResults(Array.isArray(data) ? data : []);
    } catch (err) {
      toast.error(err.message || "Search failed");
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelectPatient = (patient) => {
    setSelectedPatient(patient);
    setSearchResults([]);
    setSearchValue("");
  };

  const handleCreateVisit = async (e) => {
    e?.preventDefault();
    if (!selectedPatient) return;
    setIsCreating(true);
    try {
      const data = await api.post("/record-officer/visits", {
        patient_id: selectedPatient.id,
        reason_for_visit: reasonForVisit || null,
        department: department || null,
      });
      const dateStr = data.visit_date || (data.created_at || "").slice(0, 10);
      const timeStr = data.visit_time || ((data.created_at || "").length >= 16 ? (data.created_at || "").slice(11, 16) : "");
      const createdAtDisplay = [timeStr, dateStr].filter(Boolean).join(", ") || new Date().toLocaleString();
      setVisitCreated({
        visit_id: data.visit_id,
        patient_id: selectedPatient.id,
        patient_name: data.patient_name || selectedPatient.name,
        visit_date: dateStr,
        visit_time: timeStr,
        visit_status: data.visit_status || "WAITING_FOR_TRIAGE",
        triage_status: data.triage_status || "PENDING",
        created_at: createdAtDisplay,
      });
      toast.success("Visit created successfully");
    } catch (err) {
      console.error("Create visit error:", err);
      toast.error(err.message || "Failed to create visit");
    } finally {
      setIsCreating(false);
    }
  };

  const handleNewVisit = () => {
    setSelectedPatient(null);
    setVisitCreated(null);
    setReasonForVisit("");
    setDepartment("");
  };

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-xl font-bold text-gray-800">Create Visit</h2>
        <p className="text-sm text-gray-500 mt-1">
          Search for a patient, then create a new visit. The visit will be added to the Nurse Triage Queue.
        </p>
      </div>

      {/* 1️⃣ Retrieve Patient Record - Search */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
          <h3 className="font-semibold text-gray-800 flex items-center gap-2">
            <Search size={18} className="text-blue-600" />
            1. Retrieve Patient Record
          </h3>
          <p className="text-sm text-gray-500 mt-1">Search by Patient ID, Phone, or Name + Date of Birth</p>
        </div>
        <div className="p-6 space-y-4">
          <div className="flex flex-wrap gap-2">
            {[
              { id: "pid", label: "Patient ID", icon: <Hash size={16} /> },
              { id: "phone", label: "Phone Number", icon: <Phone size={16} /> },
              { id: "nameDob", label: "Name + Date of Birth", icon: <User size={16} /> },
            ].map((opt) => (
              <button
                key={opt.id}
                type="button"
                onClick={() => setSearchMode(opt.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  searchMode === opt.id ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {opt.icon}
                {opt.label}
              </button>
            ))}
          </div>

          <form onSubmit={handleSearch} className="flex gap-3 flex-wrap">
            <input
              type="text"
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              placeholder={
                searchMode === "pid"
                  ? "e.g. PT-2041 or uuid"
                  : searchMode === "phone"
                    ? "e.g. 08012345678"
                    : "e.g. John Doe 1992-05-15"
              }
              className="flex-1 min-w-[200px] px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-gray-800"
            />
            <button
              type="submit"
              disabled={!searchValue.trim() || isSearching}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSearching ? "Searching..." : "Search"}
            </button>
          </form>

          {searchResults.length > 0 && (
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <p className="px-4 py-2 bg-gray-50 text-sm font-medium text-gray-600">Select a patient</p>
              <ul className="divide-y divide-gray-100">
                {searchResults.map((p) => (
                  <li key={p.id}>
                    <button
                      type="button"
                      onClick={() => handleSelectPatient(p)}
                      className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-blue-50 transition-colors"
                    >
                      <div>
                        <span className="font-medium text-gray-800">{p.name}</span>
                        <span className="text-gray-500 text-sm ml-2">({p.pid || p.id})</span>
                      </div>
                      <ChevronRight size={18} className="text-gray-400" />
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Selected Patient Profile */}
      {selectedPatient && !visitCreated && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 bg-blue-50 border-b border-blue-100">
            <h3 className="font-semibold text-gray-800 flex items-center gap-2">
              <User size={18} className="text-blue-600" />
              Patient Profile
            </h3>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Patient</p>
                <p className="font-semibold text-gray-800">{selectedPatient.name}</p>
              </div>
              <div>
                <p className="text-gray-500">Age</p>
                <p className="font-semibold text-gray-800">{selectedPatient.age ?? "—"}</p>
              </div>
              <div>
                <p className="text-gray-500">Sex</p>
                <p className="font-semibold text-gray-800">{selectedPatient.sex ?? "—"}</p>
              </div>
              <div>
                <p className="text-gray-500">Patient ID (PID)</p>
                <p className="font-semibold text-gray-800">{selectedPatient.pid || selectedPatient.id}</p>
              </div>
              <div>
                <p className="text-gray-500">Previous Visits</p>
                <p className="font-semibold text-gray-800">{selectedPatient.previousVisits ?? 0}</p>
              </div>
              <div>
                <p className="text-gray-500">Last Visit</p>
                <p className="font-semibold text-gray-800">{selectedPatient.lastVisit ?? "—"}</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setSelectedPatient(null)}
              className="mt-4 text-sm text-gray-500 hover:text-gray-700"
            >
              Change patient
            </button>
          </div>
        </div>
      )}

      {/* 2️⃣ & 3️⃣ Create Visit + Optional Fields */}
      {selectedPatient && !visitCreated && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 bg-gray-50 border-b border-gray-200">
            <h3 className="font-semibold text-gray-800 flex items-center gap-2">
              <Calendar size={18} className="text-blue-600" />
              2. Create Visit
            </h3>
          </div>
          <div className="p-6 space-y-6">
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-gray-600">3. Optional Quick Intake (Recommended)</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Reason for Visit</label>
                  <input
                    type="text"
                    value={reasonForVisit}
                    onChange={(e) => setReasonForVisit(e.target.value)}
                    placeholder="e.g. Fever and headache"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-gray-800"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">Department</label>
                  <select
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-gray-800"
                  >
                    <option value="">Select department</option>
                    {DEPARTMENTS.map((d) => (
                      <option key={d.value} value={d.value}>
                        {d.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={handleCreateVisit}
              disabled={isCreating}
              className="w-full md:w-auto px-8 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-2 transition-colors shadow-sm"
            >
              <CheckCircle2 size={20} />
              {isCreating ? "Creating..." : "Create Visit"}
            </button>
          </div>
        </div>
      )}

      {/* 4️⃣ Visit Created - Success State */}
      {visitCreated && (
        <div className="bg-white rounded-xl border-2 border-green-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 bg-green-50 border-b border-green-200">
            <h3 className="font-semibold text-green-800 flex items-center gap-2">
              <CheckCircle2 size={20} />
              Visit Created — Added to Nurse Triage Queue
            </h3>
            <p className="text-sm text-green-700 mt-1">
              visit_status = WAITING_FOR_TRIAGE · triage_status = PENDING
            </p>
          </div>
          <div className="p-6 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                <Hash size={24} className="text-blue-600" />
                <div>
                  <p className="text-xs text-gray-500">Visit ID</p>
                  <p className="font-bold text-gray-800">{visitCreated.visit_id}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                <User size={24} className="text-blue-600" />
                <div>
                  <p className="text-xs text-gray-500">Patient</p>
                  <p className="font-bold text-gray-800">{visitCreated.patient_name}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                <Clock size={24} className="text-amber-600" />
                <div>
                  <p className="text-xs text-gray-500">Status</p>
                  <p className="font-bold text-amber-700">Waiting for Triage</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                <Calendar size={24} className="text-blue-600" />
                <div>
                  <p className="text-xs text-gray-500">Created At</p>
                  <p className="font-bold text-gray-800">{visitCreated.created_at}</p>
                </div>
              </div>
            </div>
            <button
              type="button"
              onClick={handleNewVisit}
              className="px-6 py-2.5 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Create Another Visit
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CreateVisit;
