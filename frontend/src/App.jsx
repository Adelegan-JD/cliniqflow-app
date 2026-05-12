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
  useNavigate,
} from "react-router-dom";
import { useEffect } from "react";
import { LoginPage } from "./pages/Authentication/LoginPage";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import Dashboard from "./pages/Admin/Dashboard";
import Layout from "./components/Layouts/AdminLayout";
import DoctorsLayout from "./components/Layouts/DoctorsLayout";
import DoctorsDashboard from "./pages/Doctor/DoctorsDashboard";
import PatientsQueue from "./pages/Doctor/PatientsQueue";
import RecordingSession from "./pages/Doctor/RecordingSession";
import Soap from "./pages/Doctor/Soap";
import Home from "./pages/Home";
// import RecordOfficerDasboard from "./pages/RecordOfficerDasboard";
// import DoctorsDashboard from "./pages/DoctorsDashboard";
import { Users } from "./pages/Admin/Users";
import { Records } from "./pages/Admin/Records";
import { Settings } from "./pages/Admin/Settings";
import { Help } from "./pages/Admin/Help";
import NurseLayout from "./components/Layouts/NurseLayout";
import { NurseDashboard } from "./pages/Nurse/NurseDashboard";
import NurseTriage from "./pages/Nurse/NurseTriage";
import TriageQueue from "./pages/Nurse/TriageQueue";
import { NurseHelp } from "./pages/Nurse/Help";
import RecordOfficerRecords from "./pages/RecordOfficers/Records";
import RecordOfficerLayout from "./components/Layouts/RecordOfficerLayout";
import RecordOfficerHelp from "./pages/RecordOfficers/RecordOfficerHelp";
import RecordOfficerDashboard from "./pages/RecordOfficers/Dashboard";

// Role-based redirect mapping
const getRoleBasedRoute = (role) => {
  const roleRoutes = {
    admin: "/dashboard",
    nurse: "/nurse-dashboard",
    record_officer: "/record-officer",
    doctor: "/doctors-dashboard",
  };
  return roleRoutes[role] || null;
};

const getUserRole = (user) =>
  user?.user_metadata?.role || user?.app_metadata?.role || user?.role || null;

const UnknownRoleRedirect = () => {
  const { signOut } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;

    (async () => {
      await signOut();
      if (isMounted) {
        navigate("/login", { replace: true });
      }
    })();

    return () => {
      isMounted = false;
    };
  }, [signOut, navigate]);

  return (
    <div className="h-screen w-full flex items-center justify-center">
      <div className="text-center text-gray-700">
        <p className="text-lg font-semibold">
          Your account role is not set yet.
        </p>
        <p className="text-sm mt-2">Redirecting you to sign in again...</p>
      </div>
    </div>
  );
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
    const role = getUserRole(user);
    if (!role) {
      return <UnknownRoleRedirect />;
    }

    if (role && role !== "admin") {
      let dest = "/dashboard"; // fallback
      if (role === "nurse") dest = "/nurse-dashboard";
      else if (role === "doctor") dest = "/doctors-dashboard";
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

    const userRole = getUserRole(user);

    if (!userRole) {
      return <UnknownRoleRedirect />;
    }

    if (!allowedRoles.includes(userRole)) {
      const redirectUrl = getRoleBasedRoute(userRole);
      return redirectUrl ? (
        <Navigate to={redirectUrl} replace />
      ) : (
        <UnknownRoleRedirect />
      );
    }

    return children;
  };

  const PublicOnlyRoute = ({ children }) => {
    const { user, loading } = useAuth();

    if (loading) return null;
    if (user) {
      const role = getUserRole(user);
      if (!role) {
        return <UnknownRoleRedirect />;
      }
      const redirectUrl = getRoleBasedRoute(role);
      return redirectUrl ? (
        <Navigate to={redirectUrl} replace />
      ) : (
        <UnknownRoleRedirect />
      );
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
            {/* Nurses  */}
            <Route
              path="/nurse-dashboard"
              element={
                <RoleProtectedRoute allowedRoles={["nurse"]}>
                  <NurseLayout />
                </RoleProtectedRoute>
              }
            >
              <Route index element={<NurseDashboard />} />
              <Route path="triage-queue" element={<TriageQueue />} />
              <Route path="records" element={<RecordOfficerRecords />} />
              <Route path="triage/:patientId" element={<NurseTriage />} />
              <Route path="help" element={<NurseHelp />} />
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
              <Route path="records" element={<RecordOfficerRecords />} />
              <Route
                path="/record-officer/help"
                element={<RecordOfficerHelp />}
              />
            </Route>
            <Route
              path="/doctors-dashboard"
              element={
                <RoleProtectedRoute allowedRoles={["doctor"]}>
                  <DoctorsLayout />
                </RoleProtectedRoute>
              }
            >
              <Route index element={<DoctorsDashboard />} />
              <Route path="records" element={<RecordOfficerRecords />} />
              <Route
                path="/doctors-dashboard/patients_queue"
                element={<PatientsQueue />}
              />
              <Route
                path="/doctors-dashboard/recording-session/:patientId/:sessionId"
                element={<RecordingSession />}
              />
              <Route
                path="/doctors-dashboard/soap/:patientId/:sessionId"
                element={<Soap />}
              />
              <Route
                path="*"
                element={<Navigate to="/doctors-dashboard" replace />}
              />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
