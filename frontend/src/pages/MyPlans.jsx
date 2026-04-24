import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ChevronDown, ChevronUp, FileText, Download, Loader2, Zap, Eye, EyeOff, Trash2, RotateCcw, AlertTriangle, Settings, X } from 'lucide-react';
import { getTermPlans, getMeetings, getOASSkills, generateMeeting, generateAllMeetings, pollForMeetingComplete, pollForAllMeetingsComplete, updateMeeting, deleteTermPlan, restoreTermPlan, deleteMeeting, restoreMeeting } from '../utils/api';

// Confirmation Dialog Component
function ConfirmDialog({ isOpen, title, message, onConfirm, onCancel, confirmText = "Delete", confirmVariant = "danger" }) {
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
        <div className="flex items-center gap-3 mb-4">
          <AlertTriangle className={confirmVariant === "danger" ? "text-red-500" : "text-yellow-500"} size={24} />
          <h3 className="text-lg font-semibold text-slate-800">{title}</h3>
        </div>
        <p className="text-slate-600 mb-6">{message}</p>
        <div className="flex justify-end gap-3">
          <button onClick={onCancel} className="btn-secondary">Cancel</button>
          <button 
            onClick={onConfirm}
            className={confirmVariant === "danger" 
              ? "bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg flex items-center gap-2"
              : "bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-lg flex items-center gap-2"
            }
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function MyPlans() {
  const [searchParams] = useSearchParams();
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedPlan, setExpandedPlan] = useState(null);
  const [expandedMeeting, setExpandedMeeting] = useState(null);
  const [meetings, setMeetings] = useState([]);
  const [meetingsLoading, setMeetingsLoading] = useState(false);
  const [generating, setGenerating] = useState({});
  const [generatingAll, setGeneratingAll] = useState(false);
  const [editingTitle, setEditingTitle] = useState(null);
  const [titleValue, setTitleValue] = useState('');
  const [editingMeeting, setEditingMeeting] = useState(null); // For the edit modal
  const [availableSkills, setAvailableSkills] = useState([]); // For skills selection in modal
  const [skillsLoading, setSkillsLoading] = useState(false);

  // Delete dialog state
  const [deleteDialog, setDeleteDialog] = useState({ open: false, type: null, item: null });
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    loadPlans();
  }, []);

  useEffect(() => {
    const viewId = searchParams.get('view');
    if (viewId && plans.length > 0) {
      setExpandedPlan(parseInt(viewId));
    }
  }, [searchParams, plans]);

  async function loadPlans() {
    try {
      const res = await getTermPlans();
      setPlans(res.data);
    } catch (err) {
      console.error('Error loading plans:', err);
    } finally {
      setLoading(false);
    }
  }

  async function togglePlan(planId) {
    if (expandedPlan === planId) {
      setExpandedPlan(null);
      setMeetings([]);
      return;
    }
    setExpandedPlan(planId);
    setMeetingsLoading(true);
    try {
      const res = await getMeetings(planId);
      setMeetings(res.data);
    } catch (err) {
      console.error('Error loading meetings:', err);
    } finally {
      setMeetingsLoading(false);
    }
  }

  async function handleGenerate(meetingId) {
    setGenerating({ ...generating, [meetingId]: true });
    try {
      // Start generation (returns immediately)
      await generateMeeting(meetingId);
      // Poll until complete
      await pollForMeetingComplete(meetingId);
      // Refresh meetings
      const res = await getMeetings(expandedPlan);
      setMeetings(res.data);
    } catch (err) {
      console.error('Error generating meeting:', err);
      alert('Failed to generate meeting: ' + err.message);
    } finally {
      setGenerating({ ...generating, [meetingId]: false });
    }
  }

  async function handleGenerateAll() {
    if (!expandedPlan) return;
    if (!confirm('Generate all meetings for this term plan? This may take a while.')) return;
    
    setGeneratingAll(true);
    try {
      // Start generation (returns immediately)
      await generateAllMeetings(expandedPlan);
      // Poll until all complete
      await pollForAllMeetingsComplete(expandedPlan);
      // Refresh meetings
      const res = await getMeetings(expandedPlan);
      setMeetings(res.data);
    } catch (err) {
      console.error('Error generating all meetings:', err);
      alert('Failed to generate meetings: ' + err.message);
    } finally {
      setGeneratingAll(false);
    }
  }

  function startEditTitle(meeting) {
    setEditingTitle(meeting.id);
    setTitleValue(meeting.title || '');
  }

  async function saveTitle(meetingId) {
    try {
      await updateMeeting(meetingId, { title: titleValue });
      const res = await getMeetings(expandedPlan);
      setMeetings(res.data);
      setEditingTitle(null);
    } catch (err) {
      console.error('Error updating title:', err);
    }
  }

  // Edit meeting modal handlers
  function openEditMeetingModal(meeting) {
    setEditingMeeting({
      ...meeting,
      skills_covered: meeting.skills_covered || [],
    });
    // Load available skills for selection
    setSkillsLoading(true);
    getOASSkills()
      .then((res) => setAvailableSkills(res.data))
      .catch((err) => console.error('Error loading skills:', err))
      .finally(() => setSkillsLoading(false));
  }

  function closeEditMeetingModal() {
    setEditingMeeting(null);
  }

  async function saveMeetingEdits() {
    if (!editingMeeting) return;
    try {
      await updateMeeting(editingMeeting.id, {
        title: editingMeeting.title,
        duration_minutes: editingMeeting.duration_minutes,
        skills_covered: editingMeeting.skills_covered,
        is_fun_night: editingMeeting.is_fun_night,
      });
      const res = await getMeetings(expandedPlan);
      setMeetings(res.data);
      setEditingMeeting(null);
    } catch (err) {
      console.error('Error updating meeting:', err);
    }
  }

  // Delete handlers
  function openDeleteDialog(type, item) {
    setDeleteDialog({ open: true, type, item });
  }

  function closeDeleteDialog() {
    setDeleteDialog({ open: false, type: null, item: null });
  }

  async function handleDeleteConfirm() {
    const { type, item } = deleteDialog;
    setDeleting(true);
    
    try {
      if (type === 'term') {
        await deleteTermPlan(item.id);
        await loadPlans();
        if (expandedPlan === item.id) {
          setExpandedPlan(null);
          setMeetings([]);
        }
      } else if (type === 'meeting') {
        await deleteMeeting(item.id);
        const res = await getMeetings(expandedPlan);
        setMeetings(res.data);
      }
      closeDeleteDialog();
    } catch (err) {
      console.error('Error deleting:', err);
      alert('Failed to delete. Please try again.');
    } finally {
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-scout-blue" size={32} />
      </div>
    );
  }

  if (plans.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText size={48} className="mx-auto text-slate-300 mb-4" />
        <h3 className="text-xl font-semibold text-slate-700 mb-2">No Term Plans Yet</h3>
        <p className="text-slate-600 mb-4">Create your first term plan to get started.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-slate-800">My Term Plans</h2>

      {plans.map((plan) => (
        <div key={plan.id} className="card">
          {/* Plan Header */}
          <button
            onClick={() => togglePlan(plan.id)}
            className="w-full flex items-center justify-between text-left"
          >
            <div>
              <h3 className="font-semibold text-slate-800">{plan.name}</h3>
              <p className="text-sm text-slate-600">
                {plan.start_date} to {plan.end_date} ({plan.total_weeks} weeks)
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  openDeleteDialog('term', plan);
                }}
                className="text-red-500 hover:bg-red-50 p-1 rounded"
                title="Delete term plan"
              >
                <Trash2 size={18} />
              </button>
              {expandedPlan === plan.id ? (
                <ChevronUp size={20} className="text-slate-400" />
              ) : (
                <ChevronDown size={20} className="text-slate-400" />
              )}
            </div>
          </button>

          {/* Expanded Content */}
          {expandedPlan === plan.id && (
            <div className="mt-4 pt-4 border-t">
              {meetingsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="animate-spin text-scout-blue" size={24} />
                </div>
              ) : (
                <>
                  {/* Downloads */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    <a
                      href={`/api/term-plans/${plan.id}/pdf`}
                      target="_blank"
                      className="btn-secondary flex items-center gap-2 text-sm"
                    >
                      <Download size={16} />
                      PDF
                    </a>
                    <a
                      href={`/api/term-plans/${plan.id}/md`}
                      target="_blank"
                      className="btn-secondary flex items-center gap-2 text-sm"
                    >
                      <FileText size={16} />
                      Markdown
                    </a>
                    <button
                      onClick={handleGenerateAll}
                      disabled={generatingAll}
                      className="btn-primary flex items-center gap-2 text-sm"
                    >
                      {generatingAll ? (
                        <>
                          <Loader2 size={16} className="animate-spin" />
                          Generating All...
                        </>
                      ) : (
                        <>
                          <Zap size={16} />
                          Generate All Meetings
                        </>
                      )}
                    </button>
                  </div>

                  {/* Meetings */}
                  <h4 className="font-medium text-slate-700 mb-3">Meeting Schedule</h4>
                  <div className="space-y-2">
                    {meetings
                      .sort((a, b) => a.week_number - b.week_number)
                      .map((meeting) => (
                        <div
                          key={meeting.id}
                          className="border rounded-lg p-3 bg-slate-50"
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              {editingTitle === meeting.id ? (
                                <div className="flex gap-2 mb-2">
                                  <input
                                    type="text"
                                    value={titleValue}
                                    onChange={(e) => setTitleValue(e.target.value)}
                                    className="input-field text-sm"
                                    placeholder="Meeting title"
                                  />
                                  <button
                                    onClick={() => saveTitle(meeting.id)}
                                    className="text-xs bg-green-500 text-white px-2 py-1 rounded"
                                  >
                                    Save
                                  </button>
                                  <button
                                    onClick={() => setEditingTitle(null)}
                                    className="text-xs bg-gray-300 px-2 py-1 rounded"
                                  >
                                    Cancel
                                  </button>
                                </div>
                              ) : (
                                <>
                                  <p className="font-medium text-slate-800">
                                    Week {meeting.week_number}: {meeting.title}
                                    {meeting.is_fun_night && <span className="ml-2 text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded">🎉 Fun Night</span>}
                                  </p>
                                  {!meeting.generated_plan && (
                                    <button
                                      onClick={() => openEditMeetingModal(meeting)}
                                      className="text-xs text-scout-blue hover:underline flex items-center gap-1"
                                    >
                                      <Settings size={10} /> Edit meeting details
                                    </button>
                                  )}
                                </>
                              )}
                              <p className="text-sm text-slate-600">
                                {meeting.meeting_date} • {meeting.duration_minutes} min
                              </p>
                              <p className="text-sm text-slate-500 mt-1">
                                {meeting.generated_plan ? '✅ Generated' : '❌ Not generated'}
                              </p>
                            </div>
                            <div className="flex flex-col gap-1">
                              {meeting.generated_plan && (
                                <button
                                  onClick={() => setExpandedMeeting(expandedMeeting === meeting.id ? null : meeting.id)}
                                  className="text-xs bg-scout-light text-white px-2 py-1 rounded hover:bg-scout-blue flex items-center gap-1"
                                >
                                  {expandedMeeting === meeting.id ? <EyeOff size={12} /> : <Eye size={12} />}
                                  {expandedMeeting === meeting.id ? 'Hide' : 'View'}
                                </button>
                              )}
                              {!meeting.generated_plan && (
                                <button
                                  onClick={() => handleGenerate(meeting.id)}
                                  disabled={generating[meeting.id]}
                                  className="btn-primary text-xs py-1 px-2 flex items-center gap-1"
                                >
                                  {generating[meeting.id] ? (
                                    <Loader2 className="animate-spin" size={12} />
                                  ) : (
                                    <Zap size={12} />
                                  )}
                                  Generate
                                </button>
                              )}
                              {meeting.generated_plan && (
                                <div className="flex gap-1">
                                  <a
                                    href={`/api/meetings/${meeting.id}/pdf`}
                                    target="_blank"
                                    className="text-xs bg-white border px-2 py-1 rounded hover:bg-gray-50"
                                  >
                                    PDF
                                  </a>
                                  <a
                                    href={`/api/meetings/${meeting.id}/md`}
                                    target="_blank"
                                    className="text-xs bg-white border px-2 py-1 rounded hover:bg-gray-50"
                                  >
                                    MD
                                  </a>
                                </div>
                              )}
                              {/* Delete meeting button */}
                              <button
                                onClick={() => openDeleteDialog('meeting', meeting)}
                                className="text-xs text-red-500 hover:bg-red-50 px-2 py-1 rounded flex items-center gap-1"
                                title="Delete meeting"
                              >
                                <Trash2 size={12} />
                                Delete
                              </button>
                            </div>
                          </div>
                          
                          {/* Inline Meeting Plan Content */}
                          {expandedMeeting === meeting.id && meeting.generated_plan && (
                            <div className="mt-3 p-3 bg-slate-100 rounded-lg text-sm">
                              <p className="whitespace-pre-wrap text-slate-700">{meeting.generated_plan}</p>
                            </div>
                          )}
                        </div>
                      ))}
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      ))}

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={deleteDialog.open}
        title={deleteDialog.type === 'term' ? "Delete Term Plan?" : "Delete Meeting?"}
        message={
          deleteDialog.type === 'term'
            ? `Are you sure you want to delete "${deleteDialog.item?.name}"? This term plan and all its meetings will be soft-deleted and can be restored within 30 days.`
            : `Are you sure you want to delete the meeting "${deleteDialog.item?.title}"? This will be soft-deleted and can be restored within 30 days.`
        }
        onConfirm={handleDeleteConfirm}
        onCancel={closeDeleteDialog}
        confirmText={deleting ? "Deleting..." : "Delete"}
        confirmVariant="danger"
      />

      {/* Edit Meeting Modal */}
      {editingMeeting && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Edit Meeting: Week {editingMeeting.week_number}</h3>
              <button onClick={closeEditMeetingModal} className="text-slate-400 hover:text-slate-600">
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Meeting Title</label>
                <input
                  type="text"
                  className="input-field"
                  value={editingMeeting.title || ''}
                  onChange={(e) => setEditingMeeting({ ...editingMeeting, title: e.target.value })}
                  placeholder="e.g., Navigation Basics"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Duration (minutes)</label>
                <select
                  className="input-field"
                  value={editingMeeting.duration_minutes || 90}
                  onChange={(e) => setEditingMeeting({ ...editingMeeting, duration_minutes: parseInt(e.target.value) })}
                >
                  <option value="60">60 minutes</option>
                  <option value="90">90 minutes</option>
                  <option value="120">2 hours</option>
                </select>
              </div>

              <div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editingMeeting.is_fun_night || false}
                    onChange={(e) => setEditingMeeting({ ...editingMeeting, is_fun_night: e.target.checked })}
                    className="rounded"
                  />
                  <span className="text-sm font-medium text-slate-700">🎉 Fun Night (skip OAS skills)</span>
                </label>
                <p className="text-xs text-slate-500 mt-1">
                  Fun nights generate themed activities without OAS skill requirements
                </p>
              </div>

              {!editingMeeting.is_fun_night && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">OAS Skills</label>
                  <p className="text-xs text-slate-500 mb-2">Select skills to focus on for this meeting (optional)</p>
                  {skillsLoading ? (
                    <div className="flex items-center justify-center py-4">
                      <Loader2 className="animate-spin text-scout-blue" size={16} />
                      <span className="ml-2 text-sm text-slate-500">Loading skills...</span>
                    </div>
                  ) : (
                    <div className="max-h-40 overflow-y-auto border rounded-lg p-2 space-y-1">
                      {availableSkills.length === 0 ? (
                        <p className="text-xs text-slate-500 text-center py-2">No skills available</p>
                      ) : (
                        availableSkills.map((skill) => (
                          <label key={skill.id} className="flex items-start gap-2 p-1 hover:bg-slate-50 rounded cursor-pointer">
                            <input
                              type="checkbox"
                              checked={editingMeeting.skills_covered?.includes(skill.id) || false}
                              onChange={(e) => {
                                const checked = e.target.checked;
                                setEditingMeeting({
                                  ...editingMeeting,
                                  skills_covered: checked
                                    ? [...(editingMeeting.skills_covered || []), skill.id]
                                    : (editingMeeting.skills_covered || []).filter(id => id !== skill.id)
                                });
                              }}
                              className="mt-1 rounded"
                            />
                            <span className="text-sm">
                              <span className="font-medium">{skill.skill_name}</span>
                              <span className="text-slate-500 text-xs ml-1">({skill.category})</span>
                            </span>
                          </label>
                        ))
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button onClick={closeEditMeetingModal} className="btn-secondary">
                Cancel
              </button>
              <button onClick={saveMeetingEdits} className="btn-primary">
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}