import React from 'react';
import Input from '../ui/Input';
import Select from '../ui/Select';

const StepThree = ({ formData, handleChange, errors = {} }) => {
  const educationLevels = [
    { value: 'None', label: 'None' },
    { value: 'Primary', label: 'Primary' },
    { value: 'Secondary', label: 'Secondary' },
    { value: 'Tertiary', label: 'Tertiary' },
    { value: 'Post-Graduate', label: 'Post-Graduate' }
  ];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-500">
      <div className="border-b border-gray-300 pb-2">
        <h3 className="text-lg font-semibold text-gray-700">Statutory Identification</h3>
        <p className="text-sm text-gray-500">Official government and insurance records.</p>
      </div>

      {/* Identification Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Input 
          label="NIN (National Identity Number)" 
          name="nin" 
          placeholder="e.g. 12345678901 (11 digits, optional)"
          value={formData.nin} 
          onChange={handleChange} 
          error={errors?.nin}
        />
        <Input 
          label="NHIS Number" 
          name="nhisNumber" 
          placeholder="e.g. NHIS-123456 (6–20 chars, optional)"
          value={formData.nhisNumber} 
          onChange={handleChange} 
          error={errors?.nhisNumber}
        />
        <Input 
          label="Military Service Number" 
          name="militaryNumber" 
          placeholder="e.g. NA/12345 (if applicable, optional)"
          value={formData.militaryNumber} 
          onChange={handleChange} 
        />
      </div>

      <div className="border-b border-gray-300 pb-2 pt-4">
        <h3 className="text-lg font-semibold text-gray-700">Socio-Economic & Admin</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Select 
          label="Highest Level of Education" 
          name="education" 
          value={formData.education} 
          onChange={handleChange} 
          options={educationLevels}
        />
        <Input 
          label="Occupation" 
          name="occupation" 
          placeholder="e.g. Teacher, Trader, Civil Servant (optional)"
          value={formData.occupation} 
          onChange={handleChange} 
          error={errors?.occupation}
        />
      </div>

      {/* Administrative Info (Read Only) */}
      <div className="bg-blue-50 p-4 rounded-lg grid grid-cols-1 md:grid-cols-2 gap-6 border border-blue-100">
        <Input 
          label="Date of Registration" 
          name="regDate" 
          type="date"
          value={formData.regDate} 
          readOnly 
        />
        <Input
          label="Registered By (Officer)" 
          name="regBy" 
          value={formData.regBy} 
          readOnly 
        />
      </div>
      <p className="text-xs text-red-500 italic">
        * Note: Administrative fields are auto-filled and cannot be edited.
      </p>
    </div>
  );
};

export default StepThree;