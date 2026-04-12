import { useState, useEffect } from 'react';
import { ChevronDown, FileText, Download, Loader2, Zap, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { getSections, getLocations, createMeeting, generateMeeting, pollForMeetingComplete } from '../utils/api';

export default function SingleMeeting() {
  const navigate = useNavigate();
  const [sections, setSections] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [meeting, setMeeting] = useState(null);
  const [showPlan, setShowPlan] = useState(false);
  
  const [formData, setFormData] = useState({
    section_id: 1,
    location_id: 1,
    meeting_date: new Date().toISOString().split('T')[0],
    title: '',
    duration_minutes: 90,
    badges_covered: [],
    skills_covered: []
  });

  useEffect(() => {
    Promise.all([getSections(), getLocations()]).then(([secRes, locRes]) => {
      setSections(secRes.data);
      setLocations(locRes.data);
      setLoading(false);
    });
  }, []);

  async function handleCreateMeeting() {
    if (!formData.title) {
      alert('Please enter a meeting title');
      return;
    }
    
    setSaving(true);
    try {
      // Create a temporary term plan to hold this meeting (or use existing logic)
      // Actually, let's create a simple meeting directly via the API
      const res = await createMeeting({
        term_plan_id: null, // Will be set if we create a term plan
        week_number: 1,
        meeting_date: formData.meeting_date,
        title: formData.title,
        duration_minutes: formData.duration_minutes,
        badges_covered: formData.badges_covered,
        skills_covered: formData.skills_covered
      });
      setMeeting(res.data);
    } catch (err) {
      console.error('Error creating meeting:', err);
      alert('Failed to create meeting. Make sure you have a term plan first, or create a standalone meeting capability.');
    } finally {
      setSaving(false);
    }
  }

  async function handleGenerate() {
    if (!meeting) return;
    
    setGenerating(true);
    try {
      // Start generation (returns immediately)
      await generateMeeting(meeting.id);
      
      // Poll until generation is complete
      const updatedMeeting = await pollForMeetingComplete(meeting.id);
      setMeeting(updatedMeeting);
    } catch (err) {
      console.error('Error generating meeting:', err);
      alert('Failed to generate meeting plan: ' + err.message);
    } finally {
      setGenerating(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-scout-blue" size={32} />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <button
        onClick={() => navigate('/my-plans')}
        className="flex items-center gap-2 text-slate-600 hover:text-slate-800 mb-4"
      >
        <ArrowLeft size={20} />
        Back to My Plans
      </button>
      
      <h2 className="text-2xl font-bold text-slate-800 mb-6">Plan a Single Meeting</h2>
      
      {!meeting ? (
        <div className="card">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Meeting Title
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="input-field w-full"
                placeholder="e.g., Introduction to Knots"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Section
                </label>
                <select
                  value={formData.section_id}
                  onChange={(e) => setFormData({ ...formData, section_id: parseInt(e.target.value) })}
                  className="input-field w-full"
                >
                  {sections.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Duration (minutes)
                </label>
                <select
                  value={formData.duration_minutes}
                  onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value) })}
                  className="input-field w-full"
                >
                  <option value={60}>60 min</option>
                  <option value={90}>90 min</option>
                  <option value={120}>120 min</option>
                </select>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Date
                </label>
                <input
                  type="date"
                  value={formData.meeting_date}
                  onChange={(e) => setFormData({ ...formData, meeting_date: e.target.value })}
                  className="input-field w-full"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Location
                </label>
                <select
                  value={formData.location_id}
                  onChange={(e) => setFormData({ ...formData, location_id: parseInt(e.target.value) })}
                  className="input-field w-full"
                >
                  {locations.map(l => (
                    <option key={l.id} value={l.id}>{l.name}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <button
              onClick={handleCreateMeeting}
              disabled={saving || !formData.title}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {saving ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Zap size={18} />
                  Create Meeting
                </>
              )}
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-slate-800">{meeting.title}</h3>
                <p className="text-sm text-slate-600">
                  {meeting.meeting_date} • {meeting.duration_minutes} minutes
                </p>
              </div>
              <div className="flex gap-2">
                {!meeting.generated_plan ? (
                  <button
                    onClick={handleGenerate}
                    disabled={generating}
                    className="btn-primary flex items-center gap-2"
                  >
                    {generating ? (
                      <>
                        <Loader2 size={18} className="animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Zap size={18} />
                        Generate Plan
                      </>
                    )}
                  </button>
                ) : (
                  <div className="flex gap-2">
                    <button
                      onClick={() => setShowPlan(!showPlan)}
                      className="btn-secondary flex items-center gap-2"
                    >
                      {showPlan ? 'Hide Plan' : 'View Plan'}
                    </button>
                    <a
                      href={`/api/meetings/${meeting.id}/pdf`}
                      target="_blank"
                      className="btn-secondary flex items-center gap-2"
                    >
                      <Download size={16} />
                      PDF
                    </a>
                    <a
                      href={`/api/meetings/${meeting.id}/md`}
                      target="_blank"
                      className="btn-secondary flex items-center gap-2"
                    >
                      <FileText size={16} />
                      MD
                    </a>
                  </div>
                )}
              </div>
            </div>
            
            {showPlan && meeting.generated_plan && (
              <div className="p-4 bg-slate-100 rounded-lg">
                <pre className="whitespace-pre-wrap text-sm text-slate-700">{meeting.generated_plan}</pre>
              </div>
            )}
          </div>
          
          <button
            onClick={() => setMeeting(null)}
            className="text-scout-blue hover:underline"
          >
            ← Create another meeting
          </button>
        </div>
      )}
    </div>
  );
}