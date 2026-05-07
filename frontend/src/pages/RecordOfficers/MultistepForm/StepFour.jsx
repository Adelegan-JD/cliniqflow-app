import React from "react";
import { AlertCircle } from "lucide-react";
import Input from "../../../components/ui/Input";
import Select from "../../../components/ui/Select";

export const Step4NextOfKin = ({ formData, handleChange, errors = {} }) => {
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
          <Input
            label="Full Name"
            name="nokName"
            value={formData.nokName}
            onChange={handleChange}
            placeholder="e.g. Adewale Johnson"
            error={errors.nokName}
            required
          />
          <Select
            label="Relationship"
            name="nokRelationship"
            value={formData.nokRelationship}
            onChange={handleChange}
            options={[
              { value: "Parent", label: "Parent" },
              { value: "Sibling", label: "Sibling" },
              { value: "Spouse", label: "Spouse" },
              { value: "Child", label: "Child" },
              { value: "Friend", label: "Friend" },
              { value: "Other", label: "Other" },
            ]}
            error={errors.nokRelationship}
            required
          />
          <Input
            label="Phone Number"
            name="nokPhone"
            type="tel"
            value={formData.nokPhone}
            onChange={handleChange}
            placeholder="08011122233"
            error={errors.nokPhone}
            required
          />
          <Input
            label="Residential Address"
            name="nokAddress"
            value={formData.nokAddress}
            onChange={handleChange}
            placeholder="e.g. 5 Ogun Street, Ikeja"
            error={errors.nokAddress}
          />
        </div>
      </div>
    </div>
  );
};
