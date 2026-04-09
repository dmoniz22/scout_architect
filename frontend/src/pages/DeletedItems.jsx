import { useState, useEffect } from 'react';
import { ArrowLeft, RotateCcw, Trash2, Loader2, Calendar, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { getDeletedTermPlans, getDeletedMeetings, restoreTermPlan, restoreMeeting } from '../utils/api';

export default function DeletedItems() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [termPlans, setTermPlans] = useState([]);
  const [meetings, setMeetings] = useState([]);
  const [activeTab, setActiveTab] = useState('terms');
  const [restoring, setRestoring] = useState({});

  useEffect(() => {
    loadDeletedItems();
  }, []);

  async function loadDeletedItems() {
    setLoading(true);
    try {
      const [termsRes, meetingsRes] = await Promise.all([
        getDeletedTermPlans(),
        getDeletedMeetings()
      ]);
      setTermPlans(termsRes.data);
      setMeetings(meetingsRes.data);
    } catch (err) {
      console.error('Error loading deleted items:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleRestoreTermPlan(planId) {
    setRestoring({ ...restoring, [`term-${planId}`]: true });
    try {
      await restoreTermPlan(planId);
      await loadDeletedItems();
    } catch (err) {
      console.error('Error restoring term plan:', err);
      if (err.response?.status === 410) {
        alert('This item can no longer be restored (30-day window expired)');
      } else {
        alert('Failed to restore term plan');
      }
    } finally {
      setRestoring({ ...restoring, [`term-${planId}`]: false });
    }
  }

  async function handleRestoreMeeting(meetingId) {
    setRestoring({ ...restoring, [`meeting-${meetingId}`]: true });
    try {
      await restoreMeeting(meetingId);
      await loadDeletedItems();
    } catch (err) {
      console.error('Error restoring meeting:', err);
      if (err.response?.status === 410) {
        alert('This item can no longer be restored (30-day window expired)');
      } else {
        alert('Failed to restore meeting');
      }
    } finally {
      setRestoring({ ...restoring, [`meeting-${meetingId}`]: false });
    }
  }

  function getDaysRemaining(deletedAt) {
    const deleted = new Date(deletedAt);
    const expired = new Date(deleted);
    expired.setDate(expired.getDate() + 30);
    const now = new Date();
    const daysLeft = Math.ceil((expired - now) / (1000 * 60 * 60 * 24));
    return daysLeft > 0 ? daysLeft : 0;
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-scout-blue" size={32} />
      </div>
    );
  }

  const hasItems = termPlans.length > 0 || meetings.length > 0;

  return (
    <div className="max-w-3xl mx-auto">
      <button
        onClick={() => navigate('/my-plans')}
        className="flex items-center gap-2 text-slate-600 hover:text-slate-800 mb-4"
      >
        <ArrowLeft size={20} />
        Back to My Plans
      </button>
      
      <h2 className="text-2xl font-bold text-slate-800 mb-2">Deleted Items</h2>
      <p className="text-slate-600 mb-6">
        Items deleted in the last 30 days can be restored. After 30 days, they will be permanently deleted.
      </p>

      {!hasItems ? (
        <div className="card text-center py-12">
          <Trash2 size={48} className="mx-auto text-slate-300 mb-4" />
          <h3 className="text-xl font-semibold text-slate-700 mb-2">No Deleted Items</h3>
          <p className="text-slate-600">Items you delete will appear here for 30 days.</p>
        </div>
      ) : (
        <>
          {/* Tabs */}
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setActiveTab('terms')}
              className={`px-4 py-2 rounded-lg ${
                activeTab === 'terms' 
                  ? 'bg-scout-blue text-white' 
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              Term Plans ({termPlans.length})
            </button>
            <button
              onClick={() => setActiveTab('meetings')}
              className={`px-4 py-2 rounded-lg ${
                activeTab === 'meetings' 
                  ? 'bg-scout-blue text-white' 
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              Individual Meetings ({meetings.length})
            </button>
          </div>

          {/* Term Plans Tab */}
          {activeTab === 'terms' && (
            <div className="space-y-3">
              {termPlans.map(plan => {
                const daysLeft = getDaysRemaining(plan.deleted_at);
                return (
                  <div key={plan.id} className="card flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-slate-800">{plan.name}</h3>
                      <p className="text-sm text-slate-600">
                        {plan.start_date} to {plan.end_date} ({plan.total_weeks} weeks)
                      </p>
                      <div className="flex items-center gap-4 mt-1">
                        <span className="text-xs text-slate-500 flex items-center gap-1">
                          <Clock size={12} />
                          {daysLeft} days remaining
                        </span>
                        <span className="text-xs text-slate-500 flex items-center gap-1">
                          <Calendar size={12} />
                          Deleted: {new Date(plan.deleted_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleRestoreTermPlan(plan.id)}
                      disabled={restoring[`term-${plan.id}`] || daysLeft === 0}
                      className={`btn-primary flex items-center gap-2 ${
                        daysLeft === 0 ? 'opacity-50 cursor-not-allowed' : ''
                      }`}
                    >
                      {restoring[`term-${plan.id}`] ? (
                        <Loader2 size={16} className="animate-spin" />
                      ) : (
                        <RotateCcw size={16} />
                      )}
                      Restore
                    </button>
                  </div>
                );
              })}
              {termPlans.length === 0 && (
                <p className="text-slate-500 text-center py-8">No deleted term plans</p>
              )}
            </div>
          )}

          {/* Meetings Tab */}
          {activeTab === 'meetings' && (
            <div className="space-y-3">
              {meetings.map(meeting => {
                const daysLeft = getDaysRemaining(meeting.deleted_at);
                return (
                  <div key={meeting.id} className="card flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold text-slate-800">
                        Week {meeting.week_number}: {meeting.title}
                      </h3>
                      <p className="text-sm text-slate-600">
                        {meeting.meeting_date} • {meeting.duration_minutes} min
                      </p>
                      <div className="flex items-center gap-4 mt-1">
                        <span className="text-xs text-slate-500 flex items-center gap-1">
                          <Clock size={12} />
                          {daysLeft} days remaining
                        </span>
                        <span className="text-xs text-slate-500 flex items-center gap-1">
                          <Calendar size={12} />
                          Deleted: {new Date(meeting.deleted_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleRestoreMeeting(meeting.id)}
                      disabled={restoring[`meeting-${meeting.id}`] || daysLeft === 0}
                      className={`btn-primary flex items-center gap-2 ${
                        daysLeft === 0 ? 'opacity-50 cursor-not-allowed' : ''
                      }`}
                    >
                      {restoring[`meeting-${meeting.id}`] ? (
                        <Loader2 size={16} className="animate-spin" />
                      ) : (
                        <RotateCcw size={16} />
                      )}
                      Restore
                    </button>
                  </div>
                );
              })}
              {meetings.length === 0 && (
                <p className="text-slate-500 text-center py-8">No deleted meetings</p>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}