import { Outlet } from "react-router-dom";
import { BadgeDollarSign } from "lucide-react";
import Sidebar from "../Sidebar";
import { useUserProfile } from "../../hooks/useUserProfile";

export default function BillingLayout() {
  const userProfile = useUserProfile();
  return <div className="h-screen flex bg-gray-50 overflow-hidden"><Sidebar logo="Billing" activeItem="billing-workspace" userProfile={userProfile} menuItems={[{ id: "billing-workspace", label: "Invoices & Payments", icon: <BadgeDollarSign size={20}/>, url: "/billing" }]} onNavigate={() => {}}/><Outlet /></div>;
}
