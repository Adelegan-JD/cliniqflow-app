import React from "react";
import { Camera } from "lucide-react";

export const Step1BioData = () => {
  return (
    <div className="animate-fadeIn">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Primary Identity</h2>
        <p className="text-gray-500 text-sm mt-1">
          Enter the patient's core biographical data.
        </p>
      </div>

      <div className="flex items-start gap-8 mb-8 pb-8 border-b border-gray-100">
        {/* Photo Upload */}
        <div className="flex flex-col items-center gap-3">
          <div className="h-28 w-28 rounded-full bg-indigo-50 border-2 border-dashed border-indigo-200 flex items-center justify-center text-indigo-400 hover:bg-indigo-100 hover:border-indigo-300 transition cursor-pointer relative overflow-hidden group">
            <Camera
              size={32}
              className="group-hover:scale-110 transition-transform"
            />
            <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
              <span className="text-white text-xs font-medium">Upload</span>
            </div>
          </div>
        </div>

        {/* Top identifiers */}
        <div className="flex-1 grid grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Patient ID (PID)
            </label>
            <input
              type="text"
              disabled
              placeholder="Auto-generated"
              className="w-full rounded-lg border-gray-200 bg-gray-50 px-4 py-2.5 text-gray-500 cursor-not-allowed border focus:ring-0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Civil Status *
            </label>
            <select className="w-full rounded-lg border-gray-300 border px-4 py-2.5 text-gray-700 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none">
              <option value="">Select Civil Status</option>
              <option>Single</option>
              <option>Married</option>
              <option>Divorced</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Form Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Last Name *
          </label>
          <input
            type="text"
            placeholder="e.g. Lasisi"
            className="w-full rounded-lg border-gray-300 border px-4 py-2.5 text-gray-900 focus:ring-2 focus:ring-indigo-500 outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            First Name *
          </label>
          <input
            type="text"
            placeholder="e.g. Fatima"
            className="w-full rounded-lg border-gray-300 border px-4 py-2.5 text-gray-900 focus:ring-2 focus:ring-indigo-500 outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Other Names
          </label>
          <input
            type="text"
            placeholder="Optional"
            className="w-full rounded-lg border-gray-300 border px-4 py-2.5 text-gray-900 focus:ring-2 focus:ring-indigo-500 outline-none"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Date of Birth *
          </label>
          <input
            type="date"
            className="w-full rounded-lg border-gray-300 border px-4 py-2.5 text-gray-900 focus:ring-2 focus:ring-indigo-500 outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Age
          </label>
          <input
            type="text"
            disabled
            placeholder="Auto-calculated"
            className="w-full rounded-lg border-gray-200 bg-gray-50 border px-4 py-2.5 text-gray-500 cursor-not-allowed"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Gender *
          </label>
          <select className="w-full rounded-lg border-gray-300 border px-4 py-2.5 text-gray-700 focus:ring-2 focus:ring-indigo-500 outline-none">
            <option>Select Gender</option>
            <option>Male</option>
            <option>Female</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Nationality
          </label>
          <input
            type="text"
            defaultValue="Nigerian"
            className="w-full rounded-lg border-gray-300 border px-4 py-2.5 text-gray-900 focus:ring-2 focus:ring-indigo-500 outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tribe (Optional)
          </label>
          <input
            type="text"
            placeholder="e.g. Yoruba, Igbo"
            className="w-full rounded-lg border-gray-300 border px-4 py-2.5 text-gray-900 focus:ring-2 focus:ring-indigo-500 outline-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Religion
          </label>
          <select className="w-full rounded-lg border-gray-300 border px-4 py-2.5 text-gray-700 focus:ring-2 focus:ring-indigo-500 outline-none">
            <option>Select Religion</option>
            <option>Christianity</option>
            <option>Islam</option>
            <option>Traditional</option>
          </select>
        </div>
      </div>
    </div>
  );
};
