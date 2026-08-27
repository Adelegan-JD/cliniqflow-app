import { Outlet } from "react-router-dom";
import Sidebar from "../Sidebar";
import {
  HelpCircle,
  LayoutDashboard,
  ClipboardList,
  Clock,
  CheckCircle2,
  BedDouble,
} from "lucide-react";
import { useState, useEffect } from "react";
import { useUserProfile } from "../../hooks/useUserProfile";

export default function NurseLayout() {
  const userProfile = useUserProfile();
  const menuItems = [
    {
      id: "nurse-dashboard",
      label: "Dashboard",
      icon: <LayoutDashboard size={20} />,
      url: "/nurse-dashboard",
    },
    {
      id: "nurse-triage-queue",
      label: "Triage Queue",
      icon: <Clock size={20} />,
      url: "/nurse-dashboard/triage-queue",
    },
    {
      id: "nurse-triage-results",
      label: "Triage Results",
      icon: <CheckCircle2 size={20} />,
      url: "/nurse-dashboard/triage-results",
    },
    {
      id: "nurse-records",
      label: "Records",
      icon: <ClipboardList size={20} />,
      url: "/nurse-dashboard/records",
    },
    {
      id: "inpatient-care",
      label: "Inpatient Care",
      icon: <BedDouble size={20} />,
      url: "/nurse-dashboard/inpatient-care",
    },
    {
      id: "help",
      label: "Help & Support",
      icon: <HelpCircle size={20} />,
      url: "/nurse-dashboard/help",
    },
  ];

  const [activePage, setActivePage] = useState("nurse-dashboard");

  useEffect(() => {
    const path = location.pathname;
    if (path === "/nurse-dashboard" || path === "/nurse-dashboard/")
      setActivePage("nurse-dashboard");
    else if (path.startsWith("/nurse-dashboard/triage-queue"))
      setActivePage("nurse-triage-queue");
    else if (path.startsWith("/nurse-dashboard/triage-results"))
      setActivePage("nurse-triage-results");
    else if (path.startsWith("/nurse-dashboard/records"))
      setActivePage("nurse-records");
    else if (path.startsWith("/nurse-dashboard/inpatient-care")) setActivePage("inpatient-care");
    else if (path.startsWith("/nurse-dashboard/help")) setActivePage("help");
  }, [location.pathname]);

  return (
    <div className="h-screen flex bg-gray-50 overflow-hidden">
      <Sidebar
        logo="Nurse Dashboard"
        menuItems={menuItems}
        activeItem={activePage}
        onNavigate={setActivePage}
        userProfile={userProfile}
      />
      <Outlet />
    </div>
  );
}
