import React, { useState, useEffect } from 'react';
import { api, API_URL } from '../context/AuthContext';
import RecruiterLayout from '../components/RecruiterLayout';
import { 
  Search, 
  Filter, 
  FileDown, 
  ArrowUpRight, 
  AlertCircle, 
  X,
  User,
  Calendar,
  Clock,
  ShieldCheck,
  TrendingDown
} from 'lucide-react';

const Reports = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [riskFilter, setRiskFilter] = useState('all');
  
  // Selected report detail modal state
  const [selectedReportId, setSelectedReportId] = useState(null);
  const [reportDetail, setReportDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const response = await api.get('/reports/');
        setReports(response.data);
      } catch (err) {
        console.error('Error fetching reports list:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchReports();
  }, []);

  // Fetch specific details when clicking "View"
  const handleViewDetails = async (reportId) => {
    setSelectedReportId(reportId);
    setDetailLoading(true);
    try {
      const response = await api.get(`/reports/${reportId}`);
      setReportDetail(response.data);
    } catch (err) {
      console.error('Error fetching report details:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  // Close modal
  const handleCloseDetail = () => {
    setSelectedReportId(null);
    setReportDetail(null);
  };

  // Filter and search reports
  const filteredReports = reports.filter((rep) => {
    // Note: Since report schema returns interview_id, to search by candidate name/email
    // we query details or fall back to matching paths/emails in local state if available.
    // If pdf_path contains candidate info, we can match against pdf_path, or report details.
    // For robust matching, we scan report metadata.
    const riskMatch = riskFilter === 'all' || rep.risk_level.toLowerCase() === riskFilter.toLowerCase();
    
    // We can extract/deduce info from pdf_path (which contains meeting_id)
    const matchesSearch = rep.pdf_path.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          rep.risk_level.toLowerCase().includes(searchTerm.toLowerCase());
                          
    return riskMatch && matchesSearch;
  });

  return (
    <RecruiterLayout>
      <div className="space-y-8 pb-12">
        {/* Header */}
        <div>
          <h2 className="text-3xl font-extrabold tracking-tight">Integrity Assessment Reports</h2>
          <p className="text-sm text-dark-300">Review, query, and download complete analytical reports for concluded sessions.</p>
        </div>

        {/* Filter bar */}
        <div className="flex flex-col sm:flex-row gap-4 items-center justify-between bg-dark-900/60 p-4 rounded-xl border border-dark-800">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3 top-3 h-4.5 w-4.5 text-dark-300" />
            <input
              type="text"
              placeholder="Search reports or risk level..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 rounded-lg bg-dark-950 border border-dark-800 focus:border-brand-500 focus:outline-none text-xs transition-colors"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <Filter className="h-4.5 w-4.5 text-dark-300" />
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
              className="w-full sm:w-40 px-3 py-2.5 rounded-lg bg-dark-950 border border-dark-800 focus:border-brand-500 focus:outline-none text-xs transition-colors"
            >
              <option value="all">All Risk Levels</option>
              <option value="low">Low Risk</option>
              <option value="medium">Medium Risk</option>
              <option value="high">High Risk</option>
            </select>
          </div>
        </div>

        {/* Main List */}
        {loading ? (
          <div className="flex h-[40vh] items-center justify-center text-brand-500">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-t-transparent border-brand-500"></div>
          </div>
        ) : filteredReports.length === 0 ? (
          <div className="glass p-12 text-center border border-dark-800 rounded-xl space-y-3">
            <AlertCircle className="h-10 w-10 text-dark-300 mx-auto" />
            <p className="text-sm font-semibold">No integrity reports found matching criteria.</p>
            <p className="text-xs text-dark-300">Complete an active interview room session to automatically compile reports.</p>
          </div>
        ) : (
          <div className="glass border border-dark-800 rounded-xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-dark-900/60 text-xs font-semibold uppercase tracking-wider text-dark-300 border-b border-dark-800">
                    <th className="px-6 py-4">Report File</th>
                    <th className="px-6 py-4">Integrity Index</th>
                    <th className="px-6 py-4">Risk Evaluation</th>
                    <th className="px-6 py-4">Date Compiled</th>
                    <th className="px-6 py-4 text-center">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-dark-800/80 text-sm">
                  {filteredReports.map((rep) => {
                    const dateObj = new Date(rep.generated_at);
                    const isHigh = rep.risk_level === 'high';
                    const isMed = rep.risk_level === 'medium';
                    
                    return (
                      <tr key={rep.id} className="hover:bg-dark-900/10 transition-colors">
                        <td className="px-6 py-4 font-mono text-xs max-w-[240px] truncate">
                          {osBasename(rep.pdf_path)}
                        </td>
                        <td className="px-6 py-4 font-bold text-dark-100">{rep.integrity_score.toFixed(1)}/100</td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                            isHigh 
                              ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' 
                              : (isMed ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20')
                          }`}>
                            {rep.risk_level} Risk
                          </span>
                        </td>
                        <td className="px-6 py-4">{dateObj.toLocaleString()}</td>
                        <td className="px-6 py-4 text-center space-x-2">
                          <button
                            onClick={() => handleViewDetails(rep.id)}
                            className="inline-flex items-center gap-1 bg-dark-800 border border-dark-700 hover:bg-dark-700 text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
                          >
                            View Stats
                            <ArrowUpRight className="h-3.5 w-3.5" />
                          </button>
                          <a
                            href={`${API_URL}/reports/${rep.id}/download`}
                            download
                            className="inline-flex items-center gap-1 bg-brand-600/10 hover:bg-brand-600 text-brand-400 hover:text-white border border-brand-500/20 hover:border-brand-600 text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
                          >
                            <FileDown className="h-3.5 w-3.5" />
                            PDF
                          </a>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Analytical details Modal Drawer */}
        {selectedReportId && (
          <div className="fixed inset-0 z-50 flex items-center justify-end bg-dark-950/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-xl h-full bg-dark-900 border-l border-dark-800 rounded-2xl flex flex-col justify-between p-6 relative overflow-hidden shadow-2xl">
              <button 
                onClick={handleCloseDetail}
                className="absolute top-6 right-6 text-dark-300 hover:text-dark-50"
              >
                <X className="h-6 w-6" />
              </button>

              {detailLoading ? (
                <div className="flex-1 flex items-center justify-center text-brand-500">
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-t-transparent border-brand-500"></div>
                </div>
              ) : reportDetail ? (
                <div className="flex-1 flex flex-col justify-between space-y-6 overflow-y-auto pr-1">
                  {/* Modal Header */}
                  <div className="space-y-2 border-b border-dark-800/80 pb-4">
                    <h3 className="text-xl font-bold tracking-tight">Integrity Log breakdown</h3>
                    <p className="text-xs text-dark-300">Detailed metric summary logs for review.</p>
                  </div>

                  {/* Section 1: Candidate Card */}
                  <div className="p-4 rounded-xl bg-dark-950/40 border border-dark-800 grid grid-cols-2 gap-4 text-xs">
                    <div className="space-y-1">
                      <p className="text-dark-300 font-semibold flex items-center gap-1"><User className="h-3.5 w-3.5" /> Candidate Name</p>
                      <p className="font-semibold text-dark-100">{reportDetail.interview.candidate_name}</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-dark-300 font-semibold flex items-center gap-1"><Clock className="h-3.5 w-3.5" /> Meeting Code</p>
                      <p className="font-mono text-dark-100">{reportDetail.interview.meeting_id}</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-dark-300 font-semibold flex items-center gap-1"><Calendar className="h-3.5 w-3.5" /> Scheduled Date</p>
                      <p className="text-dark-100">{new Date(reportDetail.interview.scheduled_at).toLocaleString()}</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-dark-300 font-semibold flex items-center gap-1">🛡️ Integrity score</p>
                      <p className="font-bold text-dark-100">{reportDetail.report.integrity_score.toFixed(1)}/100</p>
                    </div>
                  </div>

                  {/* Section 2: AI analytics grid */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-dark-300">Multimodal Log breakdown</h4>
                    <div className="grid grid-cols-2 gap-4">
                      {/* Deepfake */}
                      <div className="p-3 bg-dark-950/40 border border-dark-800 rounded-xl space-y-1">
                        <p className="text-[10px] font-semibold text-dark-300">AVG DEEPFAKE CONFIDENCE</p>
                        <p className="text-lg font-bold text-indigo-400">{reportDetail.stats.avg_deepfake.toFixed(1)}%</p>
                      </div>
                      
                      {/* Gaze deviation */}
                      <div className="p-3 bg-dark-950/40 border border-dark-800 rounded-xl space-y-1">
                        <p className="text-[10px] font-semibold text-dark-300">TIME LOOKING AWAY</p>
                        <p className="text-lg font-bold text-indigo-400">{reportDetail.stats.gaze_away_ratio.toFixed(1)}%</p>
                      </div>

                      {/* Phone visibility */}
                      <div className="p-3 bg-dark-950/40 border border-dark-800 rounded-xl space-y-1">
                        <p className="text-[10px] font-semibold text-dark-300">PHONE VISIBILITY ALARMS</p>
                        <p className="text-lg font-bold text-rose-400">{reportDetail.stats.phone_detections} events</p>
                      </div>

                      {/* Liveness checkpoint */}
                      <div className="p-3 bg-dark-950/40 border border-dark-800 rounded-xl space-y-1">
                        <p className="text-[10px] font-semibold text-dark-300">LIVENESS ANOMALIES</p>
                        <p className="text-lg font-bold text-rose-400">{reportDetail.stats.liveness_anomalies} flags</p>
                      </div>
                    </div>
                  </div>

                  {/* Section 3: Alarm timeline list */}
                  <div className="flex-1 flex flex-col min-h-0">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-dark-300 mb-2">High Severity Alarm Events</h4>
                    <div className="flex-1 overflow-y-auto space-y-2 pr-1 border border-dark-800 rounded-xl p-3 bg-dark-950/20">
                      {reportDetail.events.length === 0 ? (
                        <p className="text-xs text-dark-300 text-center py-4">No major integrity alarms recorded.</p>
                      ) : (
                        reportDetail.events.map(e => (
                          <div 
                            key={e.id}
                            className={`p-2.5 rounded-lg border text-xs space-y-1 ${
                              e.severity === 'high' 
                                ? 'bg-rose-500/5 border-rose-500/10 text-rose-400' 
                                : 'bg-amber-500/5 border-amber-500/10 text-amber-400'
                            }`}
                          >
                            <div className="flex justify-between font-bold">
                              <span>{e.event_type.replace('_', ' ').toUpperCase()}</span>
                              <span className="font-mono text-[10px] opacity-85">
                                {new Date(e.timestamp).toLocaleTimeString()}
                              </span>
                            </div>
                            <p className="opacity-95 text-[11px] leading-relaxed">{e.details}</p>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Actions footer */}
                  <div className="pt-4 border-t border-dark-800">
                    <a
                      href={`${API_URL}/reports/${reportDetail.report.id}/download`}
                      download
                      className="w-full flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-700 font-bold py-3.5 rounded-xl transition-all text-white glow-indigo"
                    >
                      <FileDown className="h-5 w-5" />
                      Download Official Integrity Certificate
                    </a>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-dark-300 text-center py-10">Failed to render report details.</p>
              )}
            </div>
          </div>
        )}
      </div>
    </RecruiterLayout>
  );
};

// Simple helper to extract base filename from path
function osBasename(path) {
  if (!path) return '';
  return path.split(/[\\/]/).pop();
}

export default Reports;
