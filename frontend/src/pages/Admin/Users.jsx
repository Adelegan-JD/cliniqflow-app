import { useEffect, useState } from "react";
import { useAdminStore } from "../../store/adminStore";
import {
  Users as UsersIcon,
  Eye,
  EyeOff,
  UserPlus,
  ListFilter,
  Search,
  Info,
} from "lucide-react";
import { generateRandomPassword } from "../../utils/uitils";
import { api } from "../../utils/api";
import { ToastContainer, toast, Flip } from "react-toastify";

export const Users = () => {
  const { users, isLoading, fetchUsers, adminError } = useAdminStore();
  const [showAddUserForm, setShowAddUserForm] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    role: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!users[0] && !adminError) {
      fetchUsers();
    }
  }, []);
  const validateForm = () => {
    const { name, email, password, role } = formData;

    if (!name.trim()) return "Full name is required.";
    if (name.length < 3) return "Name must be at least 3 characters.";

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) return "Please enter a valid email address.";

    if (password.length < 8) return "Password must be at least 8 characters.";

    if (!role) return "Please select an assigned role.";

    return null; // No errors
  };

  async function handleSubmit() {
    if (adminError) {
      setError("Admin service unavailable. Cannot add user.");
      return;
    }
    // 2. Client-side Validation
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    try {
      // Map name to display_name for backend
      const requestData = {
        email: formData.email,
        password: formData.password,
        role: formData.role,
        display_name: formData.name,
      };
      const data = await api.post("/admin/invite-user", requestData);
      // console.log(data);
      if (data?.detail) {
        throw new Error(data?.detail);
      }
      toast.success(data.message, {
        position: "top-right",
        autoClose: 5000,
        hideProgressBar: false,
        closeOnClick: false,
        pauseOnHover: true,
        draggable: true,
        progress: undefined,
        theme: "light",
        transition: Flip,
      });
      // refresh the user list so new account appears immediately
      await fetchUsers();
      // close the modal and reset form
      setShowAddUserForm(false);
      setFormData({
        name: "",
        email: "",
        password: "",
        role: "",
      });
    } catch (error) {
      // Handle validation errors from backend
      const errorMsg =
        error?.response?.data?.error?.message ||
        error?.message ||
        "Failed to add user";
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col flex-1 p-4 overflow-auto">
      <div>
        <h1 className="text-2xl font-bold mb-4">Users Management</h1>
        <p className="text-gray-600 mb-6">
          View and manage all staff members in the hospital.
        </p>
        {adminError && (
          <div className="mb-4 p-3 bg-yellow-100 text-yellow-700 border-l-4 border-yellow-700 text-sm rounded-lg">
            {adminError}
          </div>
        )}
      </div>
      <div className="w-full">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-6 border-b border-gray-200 flex items-center justify-start gap-3 flex-wrap">
            <h2 className="text-xl font-semibold flex items-center gap-2 mr-auto">
              <UsersIcon size={20} className="text-gray-600" />
              Staff Directory
            </h2>
            <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
              Total: {users.length}
            </span>
            {/* Add user button */}
            <button
              className="inline-flex items-center gap-2 ml-4 px-5 py-2.5 bg-blue-600 text-white rounded-xl text-sm font-bold shadow-md shadow-blue-500/20 hover:bg-blue-700 hover:-translate-y-0.5 active:scale-95 transition-all duration-200"
              onClick={() => setShowAddUserForm(true)}
              aria-haspopup="dialog"
              aria-controls="add-user-popup"
              aria-expanded={showAddUserForm}
              disabled={!!adminError}
            >
              <UserPlus size={18} strokeWidth={2.5} />
              <span>Add User</span>
            </button>
            {/* Add User form (pop up) */}
            {showAddUserForm && (
              <div
                className="fixed inset-0 w-full h-screen bg-slate-900/60 z-50 flex items-center justify-center backdrop-blur-sm p-4 transition-all"
                id="add-user-popup"
                role="dialog"
                aria-modal="true"
                aria-labelledby="popup-title"
                onClick={(e) => {
                  if (e.target === e.currentTarget) {
                    setShowAddUserForm(false);
                  }
                }}
              >
                <form
                  className="bg-white rounded-2xl shadow-2xl w-full max-w-md flex flex-col overflow-hidden animate-in fade-in zoom-in duration-200"
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSubmit();
                  }}
                >
                  {/* Header */}
                  <div className="px-6 py-4 border-b border-gray-100 bg-gray-50/50">
                    <h3
                      className="text-xl font-bold text-gray-900"
                      id="popup-title"
                    >
                      Add New User
                    </h3>
                    <p className="text-sm text-gray-500">
                      Create a new staff account for the directory.
                    </p>
                  </div>

                  {error && (
                    <div className="p-4">
                      <div className="mb-4 p-3 bg-red-100 text-red-700 border-l-4 border-red-700 flex gap-2 items-center text-sm rounded-lg">
                        <span className="mr-2">
                          <Info size={16} />
                        </span>
                        <span>{error}</span>
                      </div>
                    </div>
                  )}

                  {/* Body */}
                  <div className="p-6 flex flex-col gap-5">
                    {/* Name Field */}
                    <div className="flex flex-col gap-1.5">
                      <label
                        htmlFor="name"
                        className="text-sm font-semibold text-gray-700 ml-1"
                      >
                        Full Name
                      </label>
                      <input
                        type="text"
                        id="name"
                        placeholder="e.g. Jane Doe"
                        className="w-full border border-gray-300 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                        value={formData.name}
                        onChange={(e) => {
                          setError(null);
                          setFormData({ ...formData, name: e.target.value });
                        }}
                        autoFocus
                      />
                    </div>

                    {/* Email Field */}
                    <div className="flex flex-col gap-1.5">
                      <label
                        htmlFor="email"
                        className="text-sm font-semibold text-gray-700 ml-1"
                      >
                        User Email
                      </label>
                      <input
                        type="email"
                        id="email"
                        placeholder="e.g. name@hospital.com"
                        className="w-full border border-gray-300 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                        value={formData.email}
                        onChange={(e) => {
                          setError(null);
                          setFormData({ ...formData, email: e.target.value });
                        }}
                      />
                    </div>

                    {/* Password Field */}
                    <div className="flex flex-col gap-1.5">
                      <div className="flex justify-between items-center ml-1">
                        <label
                          htmlFor="password"
                          className="text-sm font-semibold text-gray-700"
                        >
                          Password
                        </label>
                        <button
                          type="button"
                          className="text-xs font-bold text-blue-600 hover:text-blue-700 uppercase tracking-tight"
                          onClick={() =>
                            setFormData({
                              ...formData,
                              password: generateRandomPassword(),
                            })
                          }
                        >
                          Generate Random
                        </button>
                      </div>
                      <div className="relative group">
                        <input
                          type={showPassword ? "text" : "password"}
                          id="password"
                          placeholder="Min. 8 characters"
                          className="w-full border border-gray-300 rounded-xl px-4 py-2.5 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
                          value={formData.password}
                          onChange={(e) => {
                            setError(null);
                            setFormData({
                              ...formData,
                              password: e.target.value,
                            });
                          }}
                        />
                        <button
                          type="button"
                          className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-gray-400 hover:text-gray-600 rounded-md transition-colors"
                          onClick={() => setShowPassword(!showPassword)}
                        >
                          {showPassword ? (
                            <EyeOff size={18} />
                          ) : (
                            <Eye size={18} />
                          )}
                        </button>
                      </div>
                    </div>

                    {/* Role Selection */}
                    <div className="flex flex-col gap-1.5">
                      <label className="text-sm font-semibold text-gray-700 ml-1">
                        Assigned Role
                      </label>
                      <select
                        className="w-full border border-gray-300 rounded-xl px-4 py-2.5 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 cursor-pointer text-gray-700 appearance-none shadow-sm"
                        value={formData.role}
                        onChange={(e) => {
                          setError(null);
                          setFormData({ ...formData, role: e.target.value });
                        }}
                      >
                        <option value="">Select Role...</option>
                        <option value="doctor">Doctor</option>
                        <option value="nurse">Nurse</option>
                        <option value="record_officer">Record Officer</option>
                        <option value="admin">Admin Officer</option>
                      </select>
                    </div>
                  </div>

                  {/* Footer */}
                  <div className="px-6 py-4 bg-gray-50 border-t border-gray-100 flex items-center justify-end gap-3">
                    <button
                      type="button"
                      className="px-4 py-2 text-sm font-semibold text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-xl transition-all"
                      onClick={() => setShowAddUserForm(false)}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={loading}
                      className="px-6 py-2 bg-blue-600 text-white rounded-xl text-sm font-bold shadow-lg shadow-blue-500/30 hover:bg-blue-700 active:scale-95 transition-all disabled:bg-blue-600/60 disabled:cursor-not-allowed"
                    >
                      {loading ? "Adding User..." : "Add User"}
                    </button>
                  </div>
                </form>
              </div>
            )}
          </div>
          <div>
            {/* search box */}
            <div className="p-4 bg-white border-b border-gray-100 flex items-center gap-3">
              {/* Unified Search Container */}
              <div className="relative flex-1 group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <Search
                    size={18}
                    className="text-gray-400 group-focus-within:text-blue-500 transition-colors"
                  />
                </div>
                <input
                  type="text"
                  placeholder="Search users by name, email, or role..."
                  className="w-full bg-gray-50 border border-gray-200 rounded-xl pl-10 pr-4 py-2.5 text-sm placeholder:text-gray-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/10 focus:border-blue-500 transition-all"
                />
              </div>

              {/* Refined Filter Button */}
              <button className="inline-flex items-center gap-2 px-4 py-2.5 bg-white border border-gray-200 rounded-xl text-sm font-semibold text-gray-700 hover:bg-gray-50 hover:border-gray-300 active:bg-gray-100 transition-all shadow-sm">
                <ListFilter size={18} className="text-gray-500" />
                <span>Filter</span>
                {/* Optional: Add a subtle badge if filters are active */}
                <span className="flex h-2 w-2 rounded-full bg-blue-600"></span>
              </button>
            </div>
          </div>

          {isLoading ? (
            <div className="p-8 text-center text-gray-500">Loading data...</div>
          ) : (
            <div className="overflow-x-auto w-full">
              <table className="w-full text-left">
                <thead className="bg-gray-50 text-gray-600 text-sm uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-4 font-medium">Name</th>
                    <th className="px-6 py-4 font-medium">Role</th>
                    {/* <th className="px-6 py-4 font-medium">Status</th> */}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {users.length > 0 ? (
                    users.map((user, index) => (
                      <tr
                        key={index}
                        className="hover:bg-gray-50 transition-colors border-b border-gray-100"
                      >
                        {/* Name & Email */}
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div>
                              <p className="font-medium text-gray-900">
                                {user?.name || user?.email || "Not Available"}
                              </p>
                              <p className="text-xs text-gray-500">
                                {user.email}
                              </p>
                            </div>
                          </div>
                        </td>

                        {/* Role & Department */}
                        <td className="px-6 py-4">
                          <div className="flex flex-col">
                            <span className="text-sm font-medium text-gray-900">
                              {user.role === "record_officer"
                                ? "Record Officer"
                                : String(user.role)[0].toUpperCase() +
                                  String(user.role).slice(1, user.length)}
                              {/* {user.role} */}
                            </span>
                            <span className="text-xs text-gray-500">
                              {user.department}
                            </span>
                          </div>
                        </td>

                        {/* Status Badge */}
                        {/* <td className="px-2 py-4">
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-medium border
      ${user.status === "On Duty" ? "bg-green-100 text-green-700 border-green-200" : ""}
      ${user.status === "On Leave" ? "bg-orange-100 text-orange-700 border-orange-200" : ""}
      ${user.status === "In Surgery" ? "bg-purple-100 text-purple-700 border-purple-200" : ""}
      ${user.status === "Active" ? "bg-blue-100 text-blue-700 border-blue-200" : ""}
    `}
                          >
                            {user.status}
                          </span>
                        </td> */}
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td
                        colSpan="3"
                        className="px-6 py-8 text-center text-gray-500"
                      >
                        No users found. Add one to get started.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick={false}
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
        transition={Flip}
      />
    </div>
  );
};
