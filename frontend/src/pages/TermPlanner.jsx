import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Save, Loader2 } from 'lucide-react';
import { getSections, getLocations, getOASSkills, createTermPlan } from '../utils/api';

export default function TermPlanner() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [sections, setSections] = useState([]);
  const [locations, setLocations] = useState([]);
  const [skills, setSkills] = useState([]);
  
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
      // Calculate total weeks from dates
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
        {/* Basic Info */}
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
          </div>
        </div>

        {/* Dates */}
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

        {/* Theme & Skills */}
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
            <label className="block text-sm font-medium text-slate-700 mb-1">Focus OAS Skills</label>
            <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto border rounded-lg p-2">
              {skills.map((skill) => (
                <label key={skill.id} className="flex items-center gap-2 text-sm">
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
                    className="rounded"
                  />
                  {skill.skill_name}
                </label>
              ))}
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

        {/* Submit */}
        <button
          type="submit"
          disabled={saving}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {saving ? <Loader2 className="animate-spin" size={20} /> : <Save size={20} />}
          {saving ? 'Creating...' : 'Create Term Plan'}
        </button>
      </form>
    </div>
  );
}