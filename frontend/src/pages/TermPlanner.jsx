import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Save, Loader2, Plus, X } from 'lucide-react';
import { getSections, getLocations, getOASSkills, createTermPlan, createLocation } from '../utils/api';

export default function TermPlanner() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [sections, setSections] = useState([]);
  const [locations, setLocations] = useState([]);
  const [skills, setSkills] = useState([]);
  const [selectedLevels, setSelectedLevels] = useState([]);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const [newLocation, setNewLocation] = useState({ name: '', city: '', province: '', country: 'Canada' });
  
  const [form, setForm] = useState({
    name: '',
    section_id: '',
    location_id: '1',
    start_date: '',
    end_date: '',
    theme: '',
    notes: '',
    duration: 90,
    focus_skills: [],
  });

  useEffect(() => {
    async function loadData() {
      try {
        const [sectionsRes, locationsRes, skillsRes] = await Promise.all([
          getSections(),
          getLocations(),
          getOASSkills(),
        ]);
        setSections(sectionsRes.data);
        setLocations(locationsRes.data);
        setSkills(skillsRes.data);
      } catch (err) {
        console.error('Error loading data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const start = new Date(form.start_date);
      const end = new Date(form.end_date);
      const total_weeks = Math.ceil((end - start) / (7 * 24 * 60 * 60 * 1000));
      
      const data = {
        name: form.name,
        section_id: parseInt(form.section_id),
        location_id: parseInt(form.location_id) || 1,
        start_date: form.start_date,
        end_date: form.end_date,
        total_weeks: total_weeks,
        theme: form.theme || null,
        notes: form.notes || null,
        focus_badges: [],
        focus_skills: form.focus_skills || [],
        target_levels: selectedLevels.length > 0 ? selectedLevels : null,
      };
      const res = await createTermPlan(data);
      navigate(`/my-plans?view=${res.data.id}`);
    } catch (err) {
      console.error('Error creating term plan:', err);
      alert('Failed to create term plan: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  const handleCreateLocation = async (e) => {
    e.preventDefault();
    try {
      const res = await createLocation(newLocation);
      setLocations([...locations, res.data]);
      setForm({ ...form, location_id: String(res.data.id) });
      setShowLocationModal(false);
      setNewLocation({ name: '', city: '', province: '', country: 'Canada' });
    } catch (err) {
      console.error('Error creating location:', err);
      alert('Failed to create location');
    }
  };

  const filteredSkills = selectedLevels.length > 0
    ? skills.filter(skill => {
        const levels = skill.levels || [];
        return levels.some(l => selectedLevels.includes(l.level_number));
      })
    : skills;

  const groupedSkills = filteredSkills.reduce((acc, skill) => {
    if (!acc[skill.category]) acc[skill.category] = [];
    acc[skill.category].push(skill);
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-scout-blue" size={32} />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold text-slate-800 mb-6">Create New Term Plan</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card space-y-4">
          <h3 className="font-semibold text-slate-700">Basic Information</h3>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Plan Name</label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g., Fall 2026"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              required
            />
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Scout Section</label>
              <select
                className="input-field"
                value={form.section_id}
                onChange={(e) => setForm({ ...form, section_id: e.target.value })}
                required
              >
                <option value="">Select section...</option>
                {sections.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Meeting Duration</label>
              <select
                className="input-field"
                value={form.duration}
                onChange={(e) => setForm({ ...form, duration: e.target.value })}
              >
                <option value="60">60 minutes</option>
                <option value="90">90 minutes</option>
                <option value="120">2 hours</option>
              </select>
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-medium text-slate-700">Location</label>
                <button
                  type="button"
                  onClick={() => setShowLocationModal(true)}
                  className="text-xs text-scout-blue hover:underline flex items-center gap-1"
                >
                  <Plus size={12} /> Add New
                </button>
              </div>
              <select
                className="input-field"
                value={form.location_id}
                onChange={(e) => setForm({ ...form, location_id: e.target.value })}
              >
                <option value="1">Default Location</option>
                {locations.filter(l => l.id !== 1).map((l) => (
                  <option key={l.id} value={l.id}>{l.name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="card space-y-4">
          <h3 className="font-semibold text-slate-700">Term Dates</h3>
          
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Start Date</label>
              <input
                type="date"
                className="input-field"
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">End Date</label>
              <input
                type="date"
                className="input-field"
                value={form.end_date}
                onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                required
              />
            </div>
          </div>
        </div>

        <div className="card space-y-4">
          <h3 className="font-semibold text-slate-700">Additional Options</h3>
          
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Term Theme (optional)</label>
            <input
              type="text"
              className="input-field"
              placeholder="e.g., Outdoor Adventures"
              value={form.theme}
              onChange={(e) => setForm({ ...form, theme: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Target OAS Levels {selectedLevels.length > 0 && `(showing ${Object.values(groupedSkills).flat().length} skills)`}
            </label>
            <div className="flex flex-wrap gap-2 mb-2">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(level => (
                <label
                  key={level}
                  className={`px-3 py-1 rounded-full text-sm cursor-pointer transition-colors ${
                    selectedLevels.includes(level)
                      ? 'bg-scout-blue text-white'
                      : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedLevels.includes(level)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedLevels([...selectedLevels, level]);
                      } else {
                        setSelectedLevels(selectedLevels.filter(l => l !== level));
                      }
                      setForm({ ...form, focus_skills: [] });
                    }}
                    className="sr-only"
                  />
                  Level {level}
                </label>
              ))}
            </div>
            {selectedLevels.length > 0 && (
              <button
                type="button"
                onClick={() => {
                  setSelectedLevels([]);
                  setForm({ ...form, focus_skills: [] });
                }}
                className="text-sm text-scout-blue hover:underline"
              >
                Clear level filter
              </button>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              Focus OAS Skills {selectedLevels.length > 0 && `(Levels ${selectedLevels.join(', ')})`}
            </label>
            <div className="max-h-60 overflow-y-auto border rounded-lg p-2 space-y-3">
              {Object.entries(groupedSkills).map(([category, categorySkills]) => (
                <div key={category}>
                  <h4 className="text-xs font-semibold text-slate-500 uppercase mb-1">{category}</h4>
                  <div className="grid grid-cols-2 gap-1">
                    {categorySkills.map((skill) => {
                      const levelInfo = selectedLevels.length > 0
                        ? skill.levels?.find(l => l.level_number === selectedLevels[0])
                        : null;
                      const reqCount = selectedLevels.length > 0
                        ? skill.levels?.filter(l => selectedLevels.includes(l.level_number)).reduce((sum, l) => sum + (l.requirements?.length || 0), 0)
                        : skill.levels?.reduce((sum, l) => sum + (l.requirements?.length || 0), 0) || 0;
                      return (
                        <label key={skill.id} className="flex items-start gap-2 text-sm p-1 hover:bg-slate-50 rounded">
                          <input
                            type="checkbox"
                            checked={form.focus_skills.includes(skill.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setForm({ ...form, focus_skills: [...form.focus_skills, skill.id] });
                              } else {
                                setForm({ ...form, focus_skills: form.focus_skills.filter((id) => id !== skill.id) });
                              }
                            }}
                            className="rounded mt-0.5"
                          />
                          <span>
                            <span className="font-medium">{skill.skill_name}</span>
                            {selectedLevels.length > 0 ? (
                              <span className="text-slate-500 text-xs ml-1">
                                (L{selectedLevels.join(',L')}: {reqCount} requirements)
                              </span>
                            ) : (
                              <span className="text-slate-500 text-xs ml-1">
                                ({reqCount} total requirements)
                              </span>
                            )}
                          </span>
                        </label>
                      );
                    })}
                  </div>
                </div>
              ))}
              {Object.keys(groupedSkills).length === 0 && (
                <p className="text-sm text-slate-500 text-center py-4">
                  {selectedLevels.length > 0 ? `No skills found for selected levels` : 'Select levels to filter skills'}
                </p>
              )}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Notes</label>
            <textarea
              className="input-field h-24"
              placeholder="Any additional notes..."
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {saving ? <Loader2 className="animate-spin" size={20} /> : <Save size={20} />}
          {saving ? 'Creating...' : 'Create Term Plan'}
        </button>
      </form>

      {/* Add Location Modal */}
      {showLocationModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Add New Location</h3>
              <button onClick={() => setShowLocationModal(false)} className="text-slate-400 hover:text-slate-600">
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleCreateLocation} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Location Name</label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="e.g., Kelowna Lakefront"
                  value={newLocation.name}
                  onChange={(e) => setNewLocation({ ...newLocation, name: e.target.value })}
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">City</label>
                  <input
                    type="text"
                    className="input-field"
                    placeholder="e.g., Kelowna"
                    value={newLocation.city}
                    onChange={(e) => setNewLocation({ ...newLocation, city: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Province</label>
                  <input
                    type="text"
                    className="input-field"
                    placeholder="e.g., BC"
                    value={newLocation.province}
                    onChange={(e) => setNewLocation({ ...newLocation, province: e.target.value })}
                  />
                </div>
              </div>
              <button type="submit" className="btn-primary w-full">Add Location</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
