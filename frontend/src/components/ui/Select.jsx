import React from "react";

const Select = ({ label, name, value, onChange, options, required, error, disabled }) => {
    return (
        <div className="flex flex-col gap-2 w-full">
            <label className="text-sm font-semibold text-gray-700">
                {label} {required && <span className='text-red-500'>*</span>}
            </label>
            <select
                name={name}
                value={value}
                onChange={onChange}
                disabled={disabled}
                className={`px-4 py-2 bg-white border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all text-gray-800 ${
                    error ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : 'border-gray-300'
                }`}
            >
                <option value="">Select {label}</option>
                {options.map((option, index) => (
                    <option key={index} value={option.value}>
                        {option.label}
                    </option>
                ))}
            </select>
            {error && <p className="text-xs text-red-600">{error}</p>}
        </div>
    );
};
export default Select;