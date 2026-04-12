import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ChevronDown, ChevronUp, FileText, Download, Loader2, Zap, Eye, EyeOff, Trash2, RotateCcw, AlertTriangle } from 'lucide-react';
import { getTermPlans, getMeetings, generateMeeting, generateAllMeetings, pollForMeetingComplete, pollForAllMeetingsComplete, updateMeeting, deleteTermPlan, restoreTermPlan, deleteMeeting, restoreMeeting } from '../utils/api';

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
      await updateMeeting(meetingId, titleValue);
      const res = await getMeetings(expandedPlan);
      setMeetings(res.data);
      setEditingTitle(null);
    } catch (err) {
      console.error('Error updating title:', err);
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
                                  </p>
                                  {!meeting.generated_plan && (
                                    <button
                                      onClick={() => startEditTitle(meeting)}
                                      className="text-xs text-scout-blue hover:underline"
                                    >
                                      Edit title before generating
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
    </div>
  );
}