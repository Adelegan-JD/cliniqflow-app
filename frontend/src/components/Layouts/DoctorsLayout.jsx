import { Outlet, useLocation } from "react-router-dom";
import Sidebar from "../Sidebar";
import {
  LayoutDashboard,
  ListFilterIcon,
  ClipboardList,
  FileText,
  BedDouble,
  FileCheck2,
  ClipboardPenLine,
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
    {
      id: "admissions",
      label: "Admissions",
      icon: <BedDouble size={20} />,
      url: "/doctors-dashboard/admissions",
    },
    {
      id: "discharges",
      label: "Discharge Summaries",
      icon: <FileCheck2 size={20} />,
      url: "/doctors-dashboard/discharges",
    },
    {
      id: "clinical-forms",
      label: "Specialty Forms",
      icon: <ClipboardPenLine size={20} />,
      url: "/doctors-dashboard/clinical-forms",
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
    else if (path.startsWith("/doctors-dashboard/admissions")) setActivePage("admissions");
    else if (path.startsWith("/doctors-dashboard/discharges")) setActivePage("discharges");
    else if (path.startsWith("/doctors-dashboard/clinical-forms")) setActivePage("clinical-forms");
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
