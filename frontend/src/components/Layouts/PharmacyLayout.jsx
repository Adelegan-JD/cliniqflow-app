import { Outlet } from "react-router-dom";
import { PackageCheck } from "lucide-react";
import Sidebar from "../Sidebar";
import { useUserProfile } from "../../hooks/useUserProfile";

export default function PharmacyLayout() {
  const userProfile = useUserProfile();
  return <div className="h-screen flex bg-gray-50 overflow-hidden"><Sidebar logo="Pharmacy" activeItem="pharmacy-worklist" userProfile={userProfile} menuItems={[{ id: "pharmacy-worklist", label: "Medication Worklist", icon: <PackageCheck size={20}/>, url: "/pharmacy" }]} onNavigate={() => {}}/><Outlet /></div>;
}
