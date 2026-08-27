import { useEffect, useState } from "react";
import { Building2, BedDouble, MapPin, Plus, RefreshCw, WandSparkles } from "lucide-react";
import { toast } from "react-toastify";
import { api } from "../../utils/api";

const emptyDepartment = { code: "", name: "", specialty: "" };
const emptyLocation = { department_id: "", code: "", name: "", location_type: "outpatient_clinic" };
const emptyBed = { location_id: "", code: "", bed_class: "standard" };

export const Settings = () => {
  const [departments, setDepartments] = useState([]);
  const [locations, setLocations] = useState([]);
  const [beds, setBeds] = useState([]);
  const [department, setDepartment] = useState(emptyDepartment);
  const [location, setLocation] = useState(emptyLocation);
  const [bed, setBed] = useState(emptyBed);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [d, l, b] = await Promise.all([api.get("/hospital/departments"), api.get("/hospital/locations"), api.get("/hospital/beds")]);
      setDepartments(d); setLocations(l); setBeds(b);
    } catch (error) { toast.error(error.message || "Could not load hospital configuration"); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);
  const field = (setter) => (event) => setter((value) => ({ ...value, [event.target.name]: event.target.value }));
  const submit = async (event, endpoint, data, reset) => {
    event.preventDefault();
    try { await api.post(endpoint, { ...data, department_id: data.department_id || null }); toast.success("Saved"); reset(); await load(); }
    catch (error) { toast.error(error.message || "Could not save"); }
  };
  const loadStarterCatalogue = async () => {
    setSeeding(true);
    try { const result = await api.post("/hospital/starter-catalogue", {}); toast.success(`Added ${result.departments_added} departments and ${result.locations_added} locations`); await load(); }
    catch (error) { toast.error(error.message || "Could not load starter catalogue"); }
    finally { setSeeding(false); }
  };

  return <main className="flex-1 overflow-auto p-4 md:p-6">
    <header className="mb-7 flex flex-wrap gap-4 items-center justify-between"><div><h1>Hospital configuration</h1><p>Set up departments, care locations, and bed capacity.</p></div><div className="flex gap-2"><button className="btn btn-primary" onClick={loadStarterCatalogue} disabled={seeding}><WandSparkles size={16} />{seeding ? "Adding…" : "Load starter catalogue"}</button><button className="btn btn-secondary" onClick={load}><RefreshCw size={16} /> Refresh</button></div></header>
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
      <Card icon={<Building2 size={21} />} title="Department / specialty"><form onSubmit={(e) => submit(e, "/hospital/departments", department, () => setDepartment(emptyDepartment))} className="space-y-3"><input className="input-field w-full" required name="code" value={department.code} onChange={field(setDepartment)} placeholder="Code, e.g. PAEDS"/><input className="input-field w-full" required name="name" value={department.name} onChange={field(setDepartment)} placeholder="Name"/><input className="input-field w-full" name="specialty" value={department.specialty} onChange={field(setDepartment)} placeholder="Specialty (optional)"/><button className="btn btn-primary w-full"><Plus size={16}/> Add department</button></form><Rows loading={loading} rows={departments} render={(x) => <><b>{x.name}</b><span>{x.code}{x.specialty ? ` · ${x.specialty}` : ""}</span></>}/></Card>
      <Card icon={<MapPin size={21} />} title="Clinical location"><form onSubmit={(e) => submit(e, "/hospital/locations", location, () => setLocation(emptyLocation))} className="space-y-3"><select className="input-field w-full" name="department_id" value={location.department_id} onChange={field(setLocation)}><option value="">No department</option>{departments.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}</select><input className="input-field w-full" required name="code" value={location.code} onChange={field(setLocation)} placeholder="Code, e.g. PAEDS-WARD"/><input className="input-field w-full" required name="name" value={location.name} onChange={field(setLocation)} placeholder="Name"/><select className="input-field w-full" name="location_type" value={location.location_type} onChange={field(setLocation)}>{["outpatient_clinic","emergency_unit","ward","theatre","laboratory","pharmacy"].map((x) => <option key={x} value={x}>{x.replaceAll("_", " ")}</option>)}</select><button className="btn btn-primary w-full"><Plus size={16}/> Add location</button></form><Rows loading={loading} rows={locations} render={(x) => <><b>{x.name}</b><span>{x.code} · {x.location_type.replaceAll("_", " ")}</span></>}/></Card>
      <Card icon={<BedDouble size={21} />} title="Bed capacity"><form onSubmit={(e) => submit(e, "/hospital/beds", bed, () => setBed(emptyBed))} className="space-y-3"><select className="input-field w-full" required name="location_id" value={bed.location_id} onChange={field(setBed)}><option value="">Select ward</option>{locations.filter((x) => x.location_type === "ward").map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}</select><input className="input-field w-full" required name="code" value={bed.code} onChange={field(setBed)} placeholder="Bed code, e.g. A-01"/><input className="input-field w-full" name="bed_class" value={bed.bed_class} onChange={field(setBed)} placeholder="Bed class"/><button className="btn btn-primary w-full"><Plus size={16}/> Add bed</button></form><Rows loading={loading} rows={beds} render={(x) => <><b>{x.location_name || "Ward"} · {x.code}</b><span>{x.status} · {x.bed_class}</span></>}/></Card>
    </div>
  </main>;
};

const Card = ({ icon, title, children }) => <section className="card elevated p-5"><div className="flex items-center gap-2 mb-4 text-blue-700">{icon}<h2 className="text-lg">{title}</h2></div>{children}</section>;
const Rows = ({ loading, rows, render }) => <div className="mt-5 border-t pt-3 space-y-2 max-h-56 overflow-auto">{loading ? <p>Loading…</p> : rows.length ? rows.map((x) => <div key={x.id} className="rounded-lg bg-slate-50 px-3 py-2 text-sm flex flex-col">{render(x)}</div>) : <p className="text-sm">No records yet.</p>}</div>;
