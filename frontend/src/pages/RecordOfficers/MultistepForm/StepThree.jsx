import React from "react";
import { ShieldCheck, Briefcase } from "lucide-react";
import Input from "../../../components/ui/Input";
import Select from "../../../components/ui/Select";

export const Step3Statutory = ({ formData, handleChange, errors = {} }) => {
  return (
    <div className="animate-fadeIn">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">
          Statutory & Socio-Economic
        </h2>
        <p className="text-gray-500 text-sm mt-1">
          Official government and insurance records.
        </p>
      </div>

      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4 text-gray-800">
          <ShieldCheck size={18} className="text-indigo-600" />
          <h3 className="font-semibold">Identification Documents</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <Input
            label="NIN"
            name="nin"
            value={formData.nin}
            onChange={handleChange}
            placeholder="11 digits"
            error={errors.nin}
          />
          <Input
            label="NHIS Number"
            name="nhisNumber"
            value={formData.nhisNumber}
            onChange={handleChange}
            placeholder="Optional"
            error={errors.nhisNumber}
          />
          <Input
            label="Military Number"
            name="militaryNumber"
            value={formData.militaryNumber}
            onChange={handleChange}
            placeholder="If applicable"
            error={errors.militaryNumber}
          />
        </div>
      </div>

      <div className="mb-8">
        <div className="flex items-center gap-2 mb-4 text-gray-800">
          <Briefcase size={18} className="text-indigo-600" />
          <h3 className="font-semibold">Socio-Economic Info</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <Select
            label="Highest Education"
            name="education"
            value={formData.education}
            onChange={handleChange}
            options={[
              { value: "None", label: "None" },
              { value: "Primary", label: "Primary" },
              { value: "Secondary", label: "Secondary" },
              { value: "Tertiary", label: "Tertiary" },
              { value: "Post-Graduate", label: "Post-Graduate" },
            ]}
            error={errors.education}
          />
          <Input
            label="Occupation"
            name="occupation"
            value={formData.occupation}
            onChange={handleChange}
            placeholder="e.g. Software Engineer"
            error={errors.occupation}
          />
        </div>
      </div>

      {/* Admin Block */}
      <div className="bg-blue-50/50 border border-blue-100 rounded-xl p-5">
        <p className="text-xs text-blue-600 mb-3 font-medium uppercase tracking-wider">
          Administrative (Auto-filled)
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Date of Registration
            </label>
            <input
              type="text"
              disabled
              value={formData.regDate}
              className="w-full rounded-lg bg-white border border-blue-100 px-4 py-2.5 text-gray-500 cursor-not-allowed shadow-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Registered By
            </label>
            <input
              type="text"
              disabled
              value={formData.regBy}
              className="w-full rounded-lg bg-white border border-blue-100 px-4 py-2.5 text-gray-500 cursor-not-allowed shadow-sm"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
