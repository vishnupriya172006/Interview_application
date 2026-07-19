import React, { useState } from 'react';
import { api } from '../context/AuthContext';
import RecruiterLayout from '../components/RecruiterLayout';
import { CalendarPlus, Clipboard, CheckCircle2, ChevronRight, AlertCircle } from 'lucide-react';

const Schedule = () => {
  const [candidateName, setCandidateName] = useState('');
  const [candidateEmail, setCandidateEmail] = useState('');
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [duration, setDuration] = useState('30');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successData, setSuccessData] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleSchedule = async (e) => {
    e.preventDefault();
    if (!candidateName || !candidateEmail || !date || !time) {
      setError('Please fill in all fields.');
      return;
    }

    setLoading(true);
    setError('');
    setSuccessData(null);
    setCopied(false);

    try {
      // Combine date and time to ISO String
      const scheduledDateTime = new Date(`${date}T${time}`).toISOString();

      const response = await api.post('/interviews/schedule', {
        candidate_name: candidateName,
        candidate_email: candidateEmail,
        scheduled_at: scheduledDateTime,
        duration_minutes: parseInt(duration)
      });

      setSuccessData(response.data);
      // Reset form fields
      setCandidateName('');
      setCandidateEmail('');
      setDate('');
      setTime('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to schedule interview. Ensure fields are correct.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!successData) return;
    const link = `${window.location.origin}/meeting-check?room=${successData.meeting_id}`;
    navigator.clipboard.writeText(link);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <RecruiterLayout>
      <div className="max-w-3xl mx-auto space-y-8">
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight">Schedule Interview</h2>
          <p className="text-sm text-dark-300">Invite a candidate to join a live monitored session.</p>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-rose-500/15 border border-rose-500/20 text-rose-400 text-sm">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Success Confirmation panel */}
        {successData && (
          <div className="glass p-6 rounded-xl border border-emerald-500/20 bg-emerald-500/5 space-y-4 glow-emerald">
            <div className="flex items-center gap-2 text-emerald-400 font-bold">
              <CheckCircle2 className="h-5 w-5" />
              <span>Interview Scheduled Successfully!</span>
            </div>
            <p className="text-sm text-dark-100">
              An invitation with the scheduled meeting card was dispatched to <b>{successData.candidate_email}</b>.
            </p>
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 p-3 bg-dark-900 rounded-lg border border-dark-800 text-xs font-mono">
              <span className="flex-1 truncate">
                {window.location.origin}/meeting-check?room={successData.meeting_id}
              </span>
              <button 
                onClick={copyToClipboard}
                className="bg-brand-600 hover:bg-brand-700 font-sans font-bold px-4 py-2 rounded transition-colors text-white"
              >
                {copied ? 'Copied!' : 'Copy Link'}
              </button>
            </div>
            <div className="grid grid-cols-2 gap-4 text-xs text-dark-300">
              <div>
                <p className="font-semibold text-dark-100">Candidate Name:</p>
                <p>{successData.candidate_name}</p>
              </div>
              <div>
                <p className="font-semibold text-dark-100">Meeting ID Code:</p>
                <p className="font-mono">{successData.meeting_id}</p>
              </div>
            </div>
          </div>
        )}

        {/* Form Container */}
        <div className="glass p-8 rounded-xl border border-dark-800">
          <form onSubmit={handleSchedule} className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* Candidate name */}
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-dark-300">Candidate Name</label>
                <input
                  type="text"
                  required
                  placeholder="Jane Smith"
                  value={candidateName}
                  onChange={(e) => setCandidateName(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-dark-900 border border-dark-800 focus:border-brand-500 focus:outline-none text-sm transition-colors"
                />
              </div>

              {/* Candidate email */}
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-dark-300">Candidate Email</label>
                <input
                  type="email"
                  required
                  placeholder="jane.smith@gmail.com"
                  value={candidateEmail}
                  onChange={(e) => setCandidateEmail(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-dark-900 border border-dark-800 focus:border-brand-500 focus:outline-none text-sm transition-colors"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
              {/* Date */}
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-dark-300">Date</label>
                <input
                  type="date"
                  required
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-dark-900 border border-dark-800 focus:border-brand-500 focus:outline-none text-sm transition-colors"
                />
              </div>

              {/* Time */}
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-dark-300">Time</label>
                <input
                  type="time"
                  required
                  value={time}
                  onChange={(e) => setTime(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-dark-900 border border-dark-800 focus:border-brand-500 focus:outline-none text-sm transition-colors"
                />
              </div>

              {/* Duration */}
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-dark-300">Duration</label>
                <select
                  value={duration}
                  onChange={(e) => setDuration(e.target.value)}
                  className="w-full px-4 py-3 rounded-xl bg-dark-900 border border-dark-800 focus:border-brand-500 focus:outline-none text-sm transition-colors"
                >
                  <option value="15">15 Minutes</option>
                  <option value="30">30 Minutes</option>
                  <option value="45">45 Minutes</option>
                  <option value="60">60 Minutes</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:bg-brand-600/40 text-sm font-bold py-3.5 rounded-xl transition-all glow-indigo mt-4"
            >
              {loading ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-t-transparent border-white"></div>
              ) : (
                <>
                  <CalendarPlus className="h-5 w-5" />
                  Schedule & Send Invitation
                  <ChevronRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </RecruiterLayout>
  );
};

export default Schedule;
