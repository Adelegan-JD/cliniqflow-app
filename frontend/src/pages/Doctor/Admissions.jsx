import { useEffect, useState } from "react";
import { BedDouble, ClipboardPlus, RefreshCw } from "lucide-react";
import { toast } from "react-toastify";
import { api } from "../../utils/api";

const blank = { patient_id: "", admission_type: "emergency", admission_reason: "", admitting_department_id: "" };

export default function Admissions() {
  const [admissions, setAdmissions] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [form, setForm] = useState(blank);
  const [loading, setLoading] = useState(true);
  const load = async () => { setLoading(true); try { const [a, d] = await Promise.all([api.get("/hospital/admissions"), api.get("/hospital/departments")]); setAdmissions(a); setDepartments(d); } catch (error) { toast.error(error.message || "Could not load admissions"); } finally { setLoading(false); } };
  useEffect(() => { load(); }, []);
  const change = (event) => setForm((old) => ({ ...old, [event.target.name]: event.target.value }));
  const admit = async (event) => { event.preventDefault(); try { await api.post("/hospital/admissions", { ...form, admitting_department_id: form.admitting_department_id || null }); toast.success("Patient admitted"); setForm(blank); await load(); } catch (error) { toast.error(error.message || "Could not admit patient"); } };
  return <main className="flex-1 overflow-auto p-4 md:p-6"><header className="mb-7 flex justify-between gap-4"><div><h1>Inpatient admissions</h1><p>Admit patients and monitor active hospital stays.</p></div><button className="btn btn-secondary" onClick={load}><RefreshCw size={16}/> Refresh</button></header><div className="grid grid-cols-1 xl:grid-cols-3 gap-5"><section className="card elevated p-5"><div className="flex items-center gap-2 mb-4 text-blue-700"><ClipboardPlus size={21}/><h2 className="text-lg">New admission</h2></div><form onSubmit={admit} className="space-y-3"><input className="input-field w-full" required name="patient_id" value={form.patient_id} onChange={change} placeholder="Patient ID / PID"/><select className="input-field w-full" name="admission_type" value={form.admission_type} onChange={change}>{["emergency","elective","transfer"].map((x) => <option key={x}>{x}</option>)}</select><select className="input-field w-full" name="admitting_department_id" value={form.admitting_department_id} onChange={change}><option value="">Department (optional)</option>{departments.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}</select><textarea className="input-field w-full min-h-28" required name="admission_reason" value={form.admission_reason} onChange={change} placeholder="Admission reason"/><button className="btn btn-primary w-full"><BedDouble size={16}/> Admit patient</button></form></section><section className="card elevated p-5 xl:col-span-2"><h2 className="text-lg mb-4">Current admissions</h2>{loading ? <p>Loading…</p> : admissions.length ? <div className="overflow-x-auto"><table className="table-modern"><thead><tr><th>Patient</th><th>Admission</th><th>Department</th><th>Type</th><th>Status</th><th>Admitted</th></tr></thead><tbody>{admissions.map((x) => <tr key={x.id}><td>{x.patient_name || x.patient_id}</td><td className="font-mono text-xs">{x.admission_number}</td><td>{x.department_name || "—"}</td><td className="capitalize">{x.admission_type}</td><td><span className="badge badge-warning">{x.status}</span></td><td>{x.admitted_at ? new Date(x.admitted_at).toLocaleString() : "—"}</td></tr>)}</tbody></table></div> : <p>No admissions yet.</p>}</section></div></main>;
}
