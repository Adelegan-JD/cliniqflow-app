import React, { useState, useEffect } from "react";
import {
  Activity,
  Users,
  Search,
  Bell,
  LayoutDashboard,
  Settings,
  FileText,
  Clock,
} from "lucide-react";
import Sidebar from "../components/Sidebar";
import { useUserProfile } from "../hooks/useUserProfile";
import TriageForm from "../components/TriageForm";
import TriageRecords from "../components/TriageRecords";
import { api } from "../utils/api";

function NurseDashboard() {
  const [activePage, setActivePage] = useState("dashboard");
  const [isTriaging, setIsTriaging] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchQueue() {
      setLoading(true);
      setError(null);
      try {
        const data = await api.get("/nurse/queue");
        setPatients(Array.isArray(data) ? data : []);
      } catch (e) {
        setError(e?.message || "Failed to load queue");
        setPatients([]);
      } finally {
        setLoading(false);
      }
    }
    fetchQueue();
  }, []);

  const handleStartTriage = (patient) => {
    setSelectedPatient(patient);
    setIsTriaging(true);
  };

  const handleEndTriage = () => {
    setIsTriaging(false);
    setSelectedPatient(null);
  };

  const handleSaveTriage = async (visitId, vitals, triageStatus) => {
    const patient = patients.find(p => p.id === visitId || p.visit_id === visitId);
    const patientId = patient?.patient_id || patient?.id;
    try {
      await api.post("/nurse/complete-triage", {
        visit_id: visitId,
        patient_id: patientId || visitId,
        vitals: vitals || {},
        urgency_level: triageStatus || "normal",
      });
    } catch (e) {
      console.error("Failed to save triage:", e);
      // Still update local state so UI reflects completion
    }
    setPatients(prev => prev.map(p => {
      if (p.id === visitId || p.visit_id === visitId) {
        return { ...p, status: "Triaged", urgency: triageStatus || "unaccessed", vitals };
      }
      return p;
    }));
    handleEndTriage();
  };

  const sortedPatients = [...patients].sort((a, b) => {
    if (a.status === "Triaged" && b.status !== "Triaged") return 1;
    if (a.status !== "Triaged" && b.status === "Triaged") return -1;
    return 0;
  });

  const menuItems = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: <LayoutDashboard size={20} />,
      url: "/nurse-dashboard",
    },
    {
      id: "records",
      label: "Triage Records",
      icon: <FileText size={20} />,
      url: "/nurse-dashboard",
    },
    {
      id: "settings",
      label: "Settings",
      icon: <Settings size={20} />,
      url: "/nurse-dashboard",
    },
  ];

  const userProfile = useUserProfile();

  if (isTriaging && selectedPatient) {
    return (
      <div className="flex flex-1 h-screen bg-slate-50 overflow-hidden font-sans">
        <Sidebar
          logo="Cliniq Flow"
          menuItems={menuItems}
          activeItem={activePage}
          onNavigate={setActivePage}
          userProfile={userProfile}
        />
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {/* Header */}
          <header className="bg-white border-b border-slate-200 px-4 sm:px-8 py-4 flex justify-between items-center shrink-0">
            <div>
              <h1 className="text-2xl font-bold text-slate-800 tracking-tight">
                Triage Assessment
              </h1>
              <p className="text-slate-500 text-sm italic">
                {selectedPatient.name}
              </p>
            </div>
          </header>
          <TriageForm 
            patient={selectedPatient} 
            onCancel={handleEndTriage} 
            onSave={handleSaveTriage} 
          />
        </main>
      </div>
    );
  }

  return (
    <div className="flex flex-1 h-screen bg-slate-50 overflow-hidden font-sans">
      <Sidebar
        logo="Cliniq Flow"
        menuItems={menuItems}
        activeItem={activePage}
        onNavigate={setActivePage}
        userProfile={userProfile}
      />

      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-4 sm:px-8 py-4 flex justify-between items-center shrink-0">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 tracking-tight">
              Welcome, {userProfile.name}
            </h1>
            <p className="text-slate-500 text-sm italic">
              Triage & Patient Intake
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="hidden sm:block relative group">
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors"
                size={18}
              />
              <input
                type="text"
                placeholder="Search patient..."
                className="pl-10 pr-4 py-2 bg-slate-100 border-transparent rounded-full text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 transition-all outline-none"
              />
            </div>
            <button className="p-2 text-slate-400 hover:bg-slate-100 rounded-full relative transition-colors">
              <Bell size={22} />
              <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-red-600 rounded-full border-2 border-white"></span>
            </button>
          </div>
        </header>

        {/* Content: Dashboard or Triage Records */}
        <div className="flex-1 overflow-auto p-4 sm:p-8">
          <div className="max-w-7xl mx-auto space-y-6">
            {activePage === "records" ? (
              <TriageRecords />
            ) : (
              <>
            {/* Quick Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 flex items-center gap-4 hover:shadow-md transition-shadow">
                <div className="p-3 bg-blue-100 rounded-lg">
                  <Activity className="text-blue-600" size={24} />
                </div>
                <div>
                  <p className="text-slate-600 text-sm font-medium">
                    Patients Triaged
                  </p>
                  <p className="text-2xl font-bold text-slate-800">
                    {patients.filter(p => p.status === 'Triaged').length}
                  </p>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 flex items-center gap-4 hover:shadow-md transition-shadow">
                <div className="p-3 bg-amber-100 rounded-lg">
                  <Clock className="text-amber-600" size={24} />
                </div>
                <div>
                  <p className="text-slate-600 text-sm font-medium">
                    Awaiting Triage
                  </p>
                  <p className="text-2xl font-bold text-slate-800">
                    {patients.filter(p => p.status === 'Waiting for Triage').length}
                  </p>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4 flex items-center gap-4 hover:shadow-md transition-shadow">
                <div className="p-3 bg-emerald-100 rounded-lg">
                  <Users className="text-emerald-600" size={24} />
                </div>
                <div>
                  <p className="text-slate-600 text-sm font-medium">
                    Total Queue Status
                  </p>
                  <p className="text-2xl font-bold text-slate-800">
                    {patients.length}
                  </p>
                </div>
              </div>
            </div>

            {/* Table Card */}
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden mt-6">
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
              ) : sortedPatients.length === 0 ? (
                <div className="px-6 py-12 text-center text-slate-500">No patients in queue. Visits created by Record Officer will appear here.</div>
              ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-white text-slate-400 text-[11px] uppercase tracking-widest border-b border-slate-100">
                    <tr>
                      <th className="px-6 py-4 font-bold tracking-tighter text-slate-300">#</th>
                      <th className="px-6 py-4 font-bold text-slate-500">Patient</th>
                      <th className="px-6 py-4 font-bold text-center">Age / Gender</th>
                      <th className="px-6 py-4 font-bold text-center">Arrival</th>
                      <th className="px-6 py-4 font-bold">Status</th>
                      <th className="px-6 py-4 font-bold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {sortedPatients.map((patient) => (
                      <tr key={patient.id} className="hover:bg-slate-50 transition-all group">
                        <td className="px-6 py-4 text-slate-400 font-mono text-xs">{patient.pid || "—"}</td>
                        <td className="px-6 py-4">
                          <span className="font-bold text-slate-800 group-hover:text-blue-600 transition-colors tracking-tight">
                            {patient.name}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-center text-slate-600 font-medium">
                          {patient.age ?? "-"} / {(patient.gender || "").charAt(0) || "-"}
                        </td>
                        <td className="px-6 py-4 text-center text-slate-600 font-medium">
                          {patient.arrivalTime}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-3 py-1 rounded-full text-[10px] uppercase tracking-tighter border shadow-sm ${
                            patient.status === 'Triaged' 
                              ? 'bg-green-100 text-green-700 border-green-200 font-semibold' 
                              : 'bg-amber-100 text-amber-700 border-amber-200 font-semibold animate-pulse'
                          }`}>
                            {patient.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          {patient.status !== 'Triaged' ? (
                            <button
                              onClick={() => handleStartTriage(patient)}
                              className="px-4 py-1.5 bg-slate-900 text-white text-[11px] font-bold rounded-lg hover:bg-blue-600 transition-all hover:shadow-lg"
                            >
                              START TRIAGE
                            </button>
                          ) : (
                            <button
                              disabled
                              className="px-4 py-1.5 bg-slate-100 text-slate-400 text-[11px] font-bold rounded-lg border border-slate-200 cursor-not-allowed"
                            >
                              TRIAGED
                            </button>
                          )}
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
}

export default NurseDashboard;
