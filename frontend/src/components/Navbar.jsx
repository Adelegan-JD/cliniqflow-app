export default function Navbar() {
  return (
    <nav className="bg-teal-600 text-white px-6 py-4 flex justify-between items-center">
      <h1 className="font-bold text-lg">CLINIQ-FLOW</h1>
      <div className="space-x-6 text-sm">
        <span className="cursor-pointer border-b-2 border-white">
          Dashboard
        </span>
        <span className="cursor-pointer opacity-80">Patients</span>
        <span className="cursor-pointer opacity-80">Reports</span>
      </div>
    </nav>
  );
}
