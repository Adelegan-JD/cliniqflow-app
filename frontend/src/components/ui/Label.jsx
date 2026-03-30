export const Label = ({ htmlFor, children }) => {
  const handleKeyDown = (e) => {
    // Check for Enter or Space keys
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      // Programmatically click the element
      e.currentTarget.click();
    }
  };

  return (
    <label
      htmlFor={htmlFor}
      tabIndex="0"
      onKeyDown={handleKeyDown}
      className="w-32 cursor-pointer hover:bg-gray-200 h-40 bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center text-center p-2"
    >
      {children}
    </label>
  );
};
