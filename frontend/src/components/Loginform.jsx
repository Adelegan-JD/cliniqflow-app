import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
import { Eye, EyeOff } from "lucide-react";
import { Info } from "lucide-react";

const LoginForm = () => {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [showPassword, setShowPassword] = useState(false);

  const { login, loading, error, setError } = useAuthStore();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setError(null);
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const user = await login(formData);
      // after successful login, redirect based on user role metadata
      const role = user?.user_metadata?.role || user?.role;
      switch (role) {
        case "nurse":
          navigate("/nurse-dashboard", { replace: true });
          break;
        case "doctor":
          navigate("/doctor-dashboard", { replace: true });
          break;
        case "record_officer":
        case "record officer":
          navigate("/record-officer", { replace: true });
          break;
        default:
          // default to admin dashboard
          navigate("/dashboard", { replace: true });
          break;
      }
    } catch (e) {
      console.log(e);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-linear-to-br from-blue-500 to-blue-800 p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
        {/* Header */}
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-gray-800">
            Cliniq Flow Login
          </h2>
          <p className="text-gray-500">Please enter your details</p>
        </div>

        {/* Error display */}
        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 border-l-4 border-red-700 flex gap-2 items-center">
            <span className="mr-2">
              <Info size={16} />
            </span>
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700 mb-1"
            >
              Email Address
            </label>
            <input
              type="email"
              name="email"
              id="email"
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
              placeholder="name@company.com"
              onChange={handleChange}
            />
          </div>

          <div>
            <div className="flex justify-between mb-1">
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700"
              >
                Password
              </label>
              <a href="#" className="text-sm text-blue-600 hover:underline">
                Forgot password?
              </a>
            </div>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                name="password"
                id="password"
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                placeholder="**********"
                onChange={handleChange}
              />
              <button
                type="button"
                className="absolute right-3 top-3 text-gray-500 hover:text-gray-800"
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? <Eye size={20} /> : <EyeOff size={20} />}
              </button>
            </div>
          </div>

          {/* <div className="flex items-center">
            <input
              id="remember-me"
              type="checkbox"
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label
              htmlFor="remember-me"
              className="ml-2 block text-sm text-gray-700"
            >
              Remember me
            </label>
          </div> */}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg transition-colors duration-300 shadow-md disabled:bg-blue-600/70 disabled:cursor-not-allowed"
          >
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default LoginForm;
