import React, { useState } from "react";
import RegistrationForm from "../components/registration/RegistrationForm";
import CreateVisit from "../components/CreateVisit";
import RecordOfficerDashboard from "../components/RecordOfficerDashboard";
import PatientRecords from "../components/PatientRecords";
import Sidebar from "../components/Sidebar";
import { useUserProfile } from "../hooks/useUserProfile";
import { ClipboardList, DownloadCloud, File, LayoutDashboard, Search } from "lucide-react";

const RecordOfficerDasboard = () => {
  const userProfile = useUserProfile();
  const menu = [
    { id: "dashboard", label: "Dashboard", icon: <LayoutDashboard size={20} /> },
    { id: "register-patient", label: "Register Patient", icon: <DownloadCloud size={20} /> },
    { id: "patient-records", label: "Patient Records", icon: <File size={20} /> },
    { id: "create-visit", label: "Create Visit", icon: <ClipboardList size={20} /> },
  ];

  const [activePage, setActivePage] = useState("dashboard");
  const [headerSearch, setHeaderSearch] = useState("");

  const renderContent = () => {
    switch (activePage) {
      case "create-visit":
        return <CreateVisit />;
      case "register-patient":
        return <RegistrationForm />;
      case "dashboard":
        return (
          <RecordOfficerDashboard
            onNavigate={setActivePage}
            user={userProfile}
          />
        );
      case "patient-records":
        return <PatientRecords headerSearchValue={headerSearch} />;
      default:
        return <CreateVisit />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar
        logo=""
        menuItems={menu}
        activeItem={activePage}
        onNavigate={setActivePage}
        userProfile={userProfile}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8">
          <div className="w-1/3 relative">
            <input
              type="text"
              placeholder="Search existing patients (Name, PID, NIN)..."
              value={headerSearch}
              onChange={(e) => setHeaderSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-100 border-transparent rounded-full text-sm focus:bg-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
            />
            <span className="absolute left-3 top-2.5 text-gray-400">
              <Search size={16} />
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="text-sm font-bold text-gray-800">{userProfile.name}</p>
              <p className="text-xs text-gray-500">{userProfile.role}</p>
            </div>
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-bold">
              {userProfile.name?.slice(0, 2).toUpperCase() || "RO"}
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-8">
          <div className="max-w-5xl mx-auto">{renderContent()}</div>
        </main>
      </div>
    </div>
  );
};

export default RecordOfficerDasboard;
