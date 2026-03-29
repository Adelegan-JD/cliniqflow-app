import React from 'react';

const Input = ({ label, type = 'text', name, value, onChange, placeholder, required, error, readOnly, helperText, ...rest }) => {
    return (
        <div className='flex flex-col gap-2 w-full'>
            <label className='text-sm font-semibold text-gray-700'>
                {label} {required && <span className='text-red-500'>*</span>}
            </label>
            <input
                type={type}
                name={name}
                value={value}
                onChange={onChange}
                placeholder={placeholder}
                readOnly={readOnly}
                className={`px-4 py-2 bg-white border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all text-gray-800 ${
                    error ? 'border-red-500 focus:ring-red-500 focus:border-red-500' : 'border-gray-300'
                } ${readOnly ? 'bg-gray-50 cursor-not-allowed' : ''}`}
                {...rest}
            />
            {error && <p className="text-xs text-red-600">{error}</p>}
            {helperText && !error && <p className="text-xs text-gray-500">{helperText}</p>}
        </div>
    );
};

export default Input;