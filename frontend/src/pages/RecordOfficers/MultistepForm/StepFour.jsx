import React from "react";
import { AlertCircle } from "lucide-react";

export const Step4NextOfKin = () => {
  return (
    <div className="animate-fadeIn">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Next of Kin</h2>
        <p className="text-gray-500 text-sm mt-1">
          Emergency contact information.
        </p>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 relative overflow-hidden">
        {/* Decorative background icon */}
        <AlertCircle className="absolute -right-4 -top-4 text-amber-500/10 w-32 h-32" />

        <div className="flex items-center gap-2 mb-6 text-amber-700 relative z-10">
          <AlertCircle size={20} />
          <h3 className="font-semibold">Emergency Contact Person</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 relative z-10">
          <div>
            <label className="block text-sm font-medium text-amber-900 mb-1">
              Full Name *
            </label>
            <input
              type="text"
              placeholder="e.g. Adewale Johnson"
              className="w-full rounded-lg border-amber-200 bg-white border px-4 py-2.5 focus:ring-2 focus:ring-amber-500 outline-none transition-shadow"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-amber-900 mb-1">
              Relationship *
            </label>
            <select className="w-full rounded-lg border-amber-200 bg-white border px-4 py-2.5 text-gray-700 focus:ring-2 focus:ring-amber-500 outline-none">
              <option>Select Relationship</option>
              <option>Spouse</option>
              <option>Parent</option>
              <option>Sibling</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-amber-900 mb-1">
              Phone Number *
            </label>
            <input
              type="tel"
              placeholder="08011122233"
              className="w-full rounded-lg border-amber-200 bg-white border px-4 py-2.5 focus:ring-2 focus:ring-amber-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-amber-900 mb-1">
              Residential Address *
            </label>
            <input
              type="text"
              placeholder="e.g. 5 Ogun Street, Ikeja"
              className="w-full rounded-lg border-amber-200 bg-white border px-4 py-2.5 focus:ring-2 focus:ring-amber-500 outline-none"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
