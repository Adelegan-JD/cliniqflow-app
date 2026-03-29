import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import {
  FileText,
  Search,
  Bell,
  AlertTriangle,
  Clock,
  CheckCircle,
  FolderOpen,
  LayoutDashboard,
  ClipboardList,
} from "lucide-react";
import Sidebar from "../components/Sidebar";
import ConsultationRoom from "../components/Patient";
import ExaminationRecords from "../components/ExaminationRecords";
import { useUserProfile } from "../hooks/useUserProfile";
import { api } from "../utils/api";
import { toast } from "react-toastify";

const menuItems = [
  { id: "dashboard", label: "Patient Queue", icon: <LayoutDashboard size={20} />, url: "/doctor-dashboard" },
  { id: "examination-records", label: "Examination Records", icon: <ClipboardList size={20} />, url: "/doctor-dashboard/examination-records" },
];

const DoctorsDashboard = () => {
  const location = useLocation();
  const userProfile = useUserProfile();
  const isExaminationRecords = location.pathname.includes("examination-records");
  const [activePage, setActivePage] = useState(isExaminationRecords ? "examination-records" : "dashboard");
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isConsulting, setIsConsulting] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState(null);

  const fetchQueue = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get("/doctor/queue");
      setPatients(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e?.message || "Failed to load doctor queue");
      setPatients([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setActivePage(location.pathname.includes("examination-records") ? "examination-records" : "dashboard");
  }, [location.pathname]);

  useEffect(() => {
    if (!isExaminationRecords) fetchQueue();
  }, [isExaminationRecords]);

  const handleStartExam = async (patient) => {
    const visitId = patient.id || patient.visit_id;
    try {
      await api.post(`/doctor/start-exam?visit_id=${encodeURIComponent(visitId)}`, {});
    } catch (e) {
      console.warn("Could not update visit status:", e);
    }
    setSelectedPatient({ ...patient });
    setIsConsulting(true);
  };

  const handleEndConsultation = async (skipRevert = false) => {
    const visitId = selectedPatient?.id || selectedPatient?.visit_id;
    if (visitId && !skipRevert) {
      try {
        await api.post(`/doctor/cancel-exam?visit_id=${encodeURIComponent(visitId)}`, {});
        await fetchQueue();
      } catch (e) {
        console.warn("Could not revert visit status:", e);
      }
    }
    setIsConsulting(false);
    setSelectedPatient(null);
  };

  const handleVisitSaved = () => {
    handleEndConsultation(true);
    fetchQueue();
  };

  const getUrgencyStyles = (urgency) => {
    switch (urgency.toLowerCase()) {
      case "emergency":
        return "bg-red-100 text-red-700 border-red-200 animate-pulse font-bold";
      case "urgent":
        return "bg-yellow-100 text-yellow-700 border-yellow-200 font-semibold";
      case "follow-up":
        return "bg-green-100 text-green-700 border-green-200";
      default:
        return "bg-slate-100 text-slate-600 border-slate-200";
    }
  };

  // If we are in consultation mode, render the ConsultationRoom instead of the dashboard content
  if (isConsulting) {
    return (
      <div className="flex flex-1 h-screen bg-slate-50 overflow-hidden font-sans">
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
          <ConsultationRoom
            patient={selectedPatient}
            onCancel={handleEndConsultation}
            onSave={handleVisitSaved}
          />
        </main>
      </div>
    );
  }

  return (
    <div className="flex flex-1 h-screen bg-slate-50 overflow-hidden font-sans">
      <Sidebar
        userProfile={userProfile}
        menuItems={menuItems}
        activeItem={activePage}
        onNavigate={(id) => setActivePage(id)}
      />
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <header className="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center shrink-0">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 tracking-tight">
              Welcome, {userProfile.role === "Doctor" ? "Doctor " : ""}{userProfile.name}
            </h1>
            <p className="text-slate-500 text-sm italic">System Active</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative group">
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors"
                size={18}
              />
              <input
                type="text"
                placeholder="Search patient record..."
                className="pl-10 pr-4 py-2 bg-slate-100 border-transparent rounded-full text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 transition-all outline-none w-64"
              />
            </div>
            <button className="p-2 text-slate-400 hover:bg-slate-100 rounded-full relative transition-colors">
              <Bell size={22} />
              <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-red-600 rounded-full border-2 border-white"></span>
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-auto p-8">
          <div className="max-w-6xl mx-auto space-y-6">
            {isExaminationRecords ? (
              <ExaminationRecords />
            ) : (
            <>
            {/* Triage Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white p-4 rounded-xl border-l-4 border-red-500 shadow-sm flex items-center justify-between">
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase tracking-wider">
                    Emergency
                  </p>
                  <p className="text-2xl font-black text-slate-800">
                    {patients.filter((p) => p.urgency === "emergency").length}
                  </p>
                </div>
                <AlertTriangle className="text-red-500 opacity-20" size={32} />
              </div>
              <div className="bg-white p-4 rounded-xl border-l-4 border-yellow-500 shadow-sm flex items-center justify-between">
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase tracking-wider">
                    Urgent
                  </p>
                  <p className="text-2xl font-black text-slate-800">
                    {patients.filter((p) => p.urgency === "urgent").length}
                  </p>
                </div>
                <Clock className="text-yellow-500 opacity-20" size={32} />
              </div>
              <div className="bg-white p-4 rounded-xl border-l-4 border-green-500 shadow-sm flex items-center justify-between">
                <div>
                  <p className="text-slate-500 text-xs font-bold uppercase tracking-wider">
                    Normal
                  </p>
                  <p className="text-2xl font-black text-slate-800">
                    {patients.filter((p) => p.urgency === "normal").length}
                  </p>
                </div>
                <CheckCircle className="text-green-500 opacity-20" size={32} />
              </div>
            </div>

            {/* Table Card */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="px-6 py-5 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
                <h2 className="font-bold text-slate-700 flex items-center gap-2">
                  <FileText size={18} className="text-blue-500" />
                  Active Patients Queue
                </h2>
                <span className="px-3 py-1 bg-white border border-slate-200 text-slate-600 text-[10px] font-bold rounded-md uppercase">
                  Live Feed
                </span>
              </div>

              {loading ? (
                <div className="px-6 py-12 text-center text-slate-500">Loading queue...</div>
              ) : error ? (
                <div className="px-6 py-12 text-center text-amber-600">{error}</div>
              ) : patients.length === 0 ? (
                <div className="px-6 py-12 text-center text-slate-500">
                  No patients waiting. Triaged patients will appear here when nurse completes triage.
                </div>
              ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-white text-slate-400 text-[11px] uppercase tracking-widest border-b border-slate-100">
                    <tr>
                      <th className="px-6 py-4 font-bold tracking-tighter text-slate-300">
                        #
                      </th>
                      <th className="px-6 py-4 font-bold text-slate-500">
                        Patient
                      </th>
                      <th className="px-6 py-4 font-bold text-center">Age</th>
                      <th className="px-6 py-4 font-bold">Triage Status</th>
                      <th className="px-6 py-4 font-bold">Vitals</th>
                      <th className="px-6 py-4 font-bold">Activity Status</th>
                      <th className="px-6 py-4 font-bold text-center">
                        Records
                      </th>
                      <th className="px-6 py-4 font-bold text-right">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {patients.map((patient) => (
                      <tr
                        key={patient.id}
                        className="hover:bg-slate-50 transition-all group"
                      >
                        <td className="px-6 py-4 text-slate-400 font-mono text-xs">
                          {patient.pid || patient.id}
                        </td>
                        <td className="px-6 py-4">
                          <span className="font-bold text-slate-800 group-hover:text-blue-600 transition-colors uppercase tracking-tight">
                            {patient.name}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-center text-slate-600 font-medium">
                          {patient.Age ?? patient.age ?? "—"}
                        </td>
                        <td className="px-6 py-4">
                          <span
                            className={`px-3 py-1 rounded-full text-[10px] uppercase tracking-tighter border shadow-sm ${getUrgencyStyles(patient.urgency)}`}
                          >
                            {patient.urgency}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex flex-wrap gap-2">
                            {patient.vitals ? (
                              <>
                                <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[10px] font-bold border border-slate-200">
                                  {patient.vitals.temperature}°C
                                </span>
                                <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[10px] font-bold border border-slate-200">
                                  {patient.vitals.bpSystolic}/{patient.vitals.bpDiastolic}
                                </span>
                                <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[10px] font-bold border border-slate-200">
                                  {patient.vitals.heartRate} HR
                                </span>
                                {patient.vitals.bmi && (
                                  <span className="bg-blue-50 text-blue-600 px-2 py-0.5 rounded text-[10px] font-bold border border-blue-100">
                                    BMI {patient.vitals.bmi}
                                  </span>
                                )}
                              </>
                            ) : (
                              <span className="text-slate-400 text-[10px]">No Vitals</span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <span className="relative flex h-2 w-2">
                              {patient.active && (
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                              )}
                              <span
                                className={`relative inline-flex rounded-full h-2 w-2 ${patient.active ? "bg-green-500" : "bg-slate-300"}`}
                              ></span>
                            </span>
                            <span className="text-xs text-slate-500 font-medium">
                              {patient.active ? "In Consultation" : "Waiting"}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <button
                            className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-all"
                            title="View Medical History"
                          >
                            <FolderOpen size={18} />
                          </button>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={() => handleStartExam(patient)}
                            disabled={patient.active}
                            className={`px-4 py-1.5 text-[11px] font-bold rounded-lg transition-all ${
                              patient.active
                                ? "bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200"
                                : "bg-slate-900 text-white hover:bg-blue-600 hover:shadow-lg"
                            }`}
                          >
                            {patient.active ? "IN PROGRESS" : "START EXAM"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              )}
            </div>
            </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default DoctorsDashboard;
