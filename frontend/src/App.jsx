// import NurseDashboard from "./pages/NurseDashboard";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  Outlet,
  useLocation,
} from "react-router-dom";
import { LoginPage } from "./pages/Authentication/LoginPage";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import Dashboard from "./pages/Admin/Dashboard";
import Layout from "./components/Layouts/AdminLayout";
import Home from "./pages/Home";
// import RecordOfficerDasboard from "./pages/RecordOfficerDasboard";
// import DoctorsDashboard from "./pages/DoctorsDashboard";
import { Users } from "./pages/Admin/Users";
import { Records } from "./pages/Admin/Records";
import { Settings } from "./pages/Admin/Settings";
import { Help } from "./pages/Admin/Help";
import NurseLayout from "./components/Layouts/NurseLayout";
import { NurseDashboard } from "./pages/Nurse/NurseDashboard";
import { NurseHelp } from "./pages/Nurse/Help";
import RecordOfficerLayout from "./components/Layouts/RecordOfficerLayout";
import RecordOfficerHelp from "./pages/RecordOfficers/RecordOfficerHelp";
import RecordOfficerDashboard from "./pages/RecordOfficers/Dashboard";

// Role-based redirect mapping
const getRoleBasedRoute = (role) => {
  const roleRoutes = {
    admin: "/dashboard",
    nurse: "/nurse-dashboard",
    // record_officer: "/record-officer",
    // doctor: "/doctor-dashboard",
  };
  return roleRoutes[role] || "/";
};
function App() {
  const ProtectedRoute = () => {
    const { user, loading } = useAuth();
    const location = useLocation();

    if (loading)
      return (
        <div className="h-screen w-full flex items-center justify-center">
          Loading...
        </div>
      );

    if (!user) return <Navigate to="/login" replace />;

    // if the authenticated user does not have the admin role, redirect
    const role = user.user_metadata?.role || user.role;
    if (role && role !== "admin") {
      let dest = "/dashboard"; // fallback
      if (role === "nurse") dest = "/nurse-dashboard";
      else if (role === "doctor") dest = "/doctor-dashboard";
      else if (role === "record_officer" || role === "record officer")
        dest = "/record-officer";
      const path = location.pathname;
      const allowed = path === dest || path.startsWith(dest + "/");
      if (!allowed) {
        return <Navigate to={dest} replace />;
      }
    }

    return <Outlet />;
  };

  const RoleProtectedRoute = ({ children, allowedRoles }) => {
    const { user, loading } = useAuth();

    if (loading)
      return (
        <div className="h-screen w-full flex items-center justify-center">
          Loading...
        </div>
      );

    const userRole = user?.user_metadata?.role;

    if (!allowedRoles.includes(userRole)) {
      const redirectUrl = getRoleBasedRoute(userRole);
      return <Navigate to={redirectUrl} replace />;
    }

    return children;
  };

  const PublicOnlyRoute = ({ children }) => {
    const { user, loading } = useAuth();

    if (loading) return null;
    if (user) {
      const role = user?.user_metadata?.role || user?.role;
      const redirectUrl = getRoleBasedRoute(role);
      return <Navigate to={redirectUrl} replace />;
    }

    return children;
  };

  return (
    <AuthProvider>
      <ToastContainer position="top-right" autoClose={3000} />
      <BrowserRouter>
        <Routes>
          <Route
            path="/login"
            element={
              <PublicOnlyRoute>
                <LoginPage />
              </PublicOnlyRoute>
            }
          />
          <Route path="/" element={<Home />} />

          {/* Admin Route */}
          <Route element={<ProtectedRoute />}>
            <Route
              path="/dashboard"
              element={
                <RoleProtectedRoute allowedRoles={["admin"]}>
                  <Layout />
                </RoleProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="/dashboard/users" element={<Users />} />
              <Route path="/dashboard/records" element={<Records />} />
              <Route path="/dashboard/settings" element={<Settings />} />
              <Route path="/dashboard/help" element={<Help />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Route>


            {/* nurse route */}
            <Route
              path="/nurse-dashboard"
              element={
                <RoleProtectedRoute allowedRoles={["nurse"]}>
                  <NurseLayout />
                </RoleProtectedRoute>
              }
            >
              <Route index element={<NurseDashboard />} />
              <Route path="/nurse-dashboard/help" element={<NurseHelp />} />
            </Route>

            {/* record officer route */}
            <Route
              path="/record-officer"
              element={
                <RoleProtectedRoute allowedRoles={["record_officer"]}>
                  <RecordOfficerLayout />
                </RoleProtectedRoute>
              }
            >
              <Route index element={<RecordOfficerDashboard />} />
              <Route path="/record-officer/help" element={<RecordOfficerHelp />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
