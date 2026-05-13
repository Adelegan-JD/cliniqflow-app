import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "../Sidebar";
import {
  LayoutDashboard,
  ListFilterIcon,
  ClipboardList,
  FileText,
} from "lucide-react";
import { useState, useEffect } from "react";
import { useUserProfile } from "../../hooks/useUserProfile";

export default function DoctorsLayout() {
  const userProfile = useUserProfile();
  const menuItems = [
    {
      id: "doctors-dashboard",
      label: "Dashboard",
      icon: <LayoutDashboard size={20} />,
      url: "/doctors-dashboard",
    },
    {
      id: "patients_queue",
      label: "Patients Queue",
      icon: <ListFilterIcon size={20} />,
      url: "/doctors-dashboard/patients_queue",
    },
    {
      id: "nurse_queue",
      label: "Nurse Triage Queue",
      icon: <ClipboardList size={20} />,
      url: "/doctors-dashboard/nurse-queue",
    },
    {
      id: "doctor-records",
      label: "Records",
      icon: <FileText size={20} />,
      url: "/doctors-dashboard/records",
    },
  ];

  const location = useLocation();
  const [activePage, setActivePage] = useState("doctors-dashboard");

  useEffect(() => {
    const path = location.pathname;
    if (path === "/doctors-dashboard" || path === "/doctors-dashboard/")
      setActivePage("doctors-dashboard");
    else if (
      path.startsWith("/doctors-dashboard/patients_queue") ||
      path.startsWith("/doctors-dashboard/recording-session") ||
      path.startsWith("/doctors-dashboard/soap")
    )
      setActivePage("patients_queue");
    else if (path.startsWith("/doctors-dashboard/nurse-queue"))
      setActivePage("nurse_queue");
    else if (path.startsWith("/doctors-dashboard/records"))
      setActivePage("doctor-records");
  }, [location.pathname]);

  return (
    <div className="h-screen flex bg-gray-50 overflow-hidden">
      <Sidebar
        logo="Doctors Dashboard"
        menuItems={menuItems}
        activeItem={activePage}
        onNavigate={setActivePage}
        userProfile={userProfile}
      />
      <Outlet />
    </div>
  );
}
