import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../context/AuthContext';
import RecruiterLayout from '../components/RecruiterLayout';
import { 
  Users, 
  Calendar, 
  CheckCircle, 
  FileSpreadsheet, 
  ArrowUpRight, 
  Plus, 
  AlertCircle,
  Clock,
  Video
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';

const Dashboard = () => {
  const navigate = useNavigate();
  const [interviews, setInterviews] = useState([]);
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const [interviewsRes, reportsRes] = await Promise.all([
          api.get('/interviews/'),
          api.get('/reports/')
        ]);
        setInterviews(interviewsRes.data);
        setReports(reportsRes.data);
      } catch (err) {
        console.error('Error fetching dashboard statistics:', err);
      } finally {
        setLoading(false);
      }
    };
    loadDashboardData();
  }, []);

  // Compute stat aggregates
  const totalInterviews = interviews.length;
  const completedInterviews = interviews.filter(i => i.status === 'completed').length;
  const upcomingInterviews = interviews.filter(i => i.status === 'scheduled').length;
  const totalReports = reports.length;

  // Process data for charts
  // 1. Chart: Integrity Score Trend over time
  const chartData = interviews
    .filter(i => i.status === 'completed' && i.integrity_score !== null)
    .slice()
    .reverse() // chronological order
    .map(i => ({
      name: i.candidate_name.split(' ')[0],
      score: i.integrity_score
    }));

  // Fallback default chart data if no completed interviews exist
  const trendData = chartData.length > 0 ? chartData : [
    { name: 'Demo 1', score: 92 },
    { name: 'Demo 2', score: 87 },
    { name: 'Demo 3', score: 65 },
    { name: 'Demo 4', score: 94 }
  ];

  // 2. Chart: Risk levels pie chart
  const riskCounts = interviews.reduce((acc, curr) => {
    if (curr.status === 'completed' && curr.risk_level) {
      acc[curr.risk_level] = (acc[curr.risk_level] || 0) + 1;
    }
    return acc;
  }, {});

  const pieData = [
    { name: 'Low Risk', value: riskCounts['low'] || 0, color: '#10B981' },
    { name: 'Medium Risk', value: riskCounts['medium'] || 0, color: '#F59E0B' },
    { name: 'High Risk', value: riskCounts['high'] || 0, color: '#EF4444' }
  ].filter(d => d.value > 0);

  const finalPieData = pieData.length > 0 ? pieData : [
    { name: 'Low Risk', value: 3, color: '#10B981' },
    { name: 'Medium Risk', value: 1, color: '#F59E0B' },
    { name: 'High Risk', value: 0, color: '#EF4444' }
  ];

  return (
    <RecruiterLayout>
      {loading ? (
        <div className="flex h-[60vh] items-center justify-center text-brand-500">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-t-transparent border-brand-500"></div>
        </div>
      ) : (
        <div className="space-y-8 pb-12">
          {/* Dashboard Header Banner */}
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h2 className="text-3xl font-extrabold tracking-tight">Recruiter Dashboard</h2>
              <p className="text-sm text-dark-300">Monitor current integrity scores and track candidate assessments.</p>
            </div>
            <Link 
              to="/schedule" 
              className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-sm font-semibold px-4 py-2.5 rounded-lg transition-colors glow-indigo"
            >
              <Plus className="h-4.5 w-4.5" />
              Schedule Interview
            </Link>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Stat 1 */}
            <div className="glass p-6 rounded-xl border border-dark-800 flex items-center justify-between">
              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wider text-dark-300">Total Scheduled</p>
                <h3 className="text-3xl font-bold">{totalInterviews}</h3>
              </div>
              <div className="h-12 w-12 rounded-lg bg-brand-500/10 flex items-center justify-center text-brand-400 border border-brand-500/20">
                <Users className="h-6 w-6" />
              </div>
            </div>

            {/* Stat 2 */}
            <div className="glass p-6 rounded-xl border border-dark-800 flex items-center justify-between">
              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wider text-dark-300">Upcoming Live</p>
                <h3 className="text-3xl font-bold text-indigo-400">{upcomingInterviews}</h3>
              </div>
              <div className="h-12 w-12 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
                <Calendar className="h-6 w-6" />
              </div>
            </div>

            {/* Stat 3 */}
            <div className="glass p-6 rounded-xl border border-dark-800 flex items-center justify-between">
              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wider text-dark-300">Completed Sessions</p>
                <h3 className="text-3xl font-bold text-emerald-400">{completedInterviews}</h3>
              </div>
              <div className="h-12 w-12 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20">
                <CheckCircle className="h-6 w-6" />
              </div>
            </div>

            {/* Stat 4 */}
            <div className="glass p-6 rounded-xl border border-dark-800 flex items-center justify-between">
              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wider text-dark-300">Integrity Reports</p>
                <h3 className="text-3xl font-bold text-amber-400">{totalReports}</h3>
              </div>
              <div className="h-12 w-12 rounded-lg bg-amber-500/10 flex items-center justify-center text-amber-400 border border-amber-500/20">
                <FileSpreadsheet className="h-6 w-6" />
              </div>
            </div>
          </div>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Trend Chart */}
            <div className="glass p-6 rounded-xl border border-dark-800 lg:col-span-2 space-y-6">
              <div>
                <h3 className="text-lg font-bold">Integrity Scores Trend</h3>
                <p className="text-xs text-dark-300">Average integrity marks across consecutive sessions.</p>
              </div>
              <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="scoreColor" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.25}/>
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                    <XAxis dataKey="name" stroke="#9ca3af" fontSize={11} tickLine={false} />
                    <YAxis stroke="#9ca3af" domain={[0, 100]} fontSize={11} tickLine={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                      labelStyle={{ color: '#f3f4f6' }}
                    />
                    <Area type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2.5} fillOpacity={1} fill="url(#scoreColor)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Risk Breakdown Chart */}
            <div className="glass p-6 rounded-xl border border-dark-800 space-y-6 flex flex-col justify-between">
              <div>
                <h3 className="text-lg font-bold">Risk Matrix Distribution</h3>
                <p className="text-xs text-dark-300">Ratio of Low vs High risk candidate validations.</p>
              </div>
              <div className="h-[220px] flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={finalPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {finalPieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }}
                    />
                    <Legend verticalAlign="bottom" height={36} iconType="circle" />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Interview List Section */}
          <div className="glass rounded-xl border border-dark-800 overflow-hidden">
            <div className="px-6 py-5 border-b border-dark-800 flex justify-between items-center">
              <div>
                <h3 className="text-lg font-bold">Scheduled Sessions</h3>
                <p className="text-xs text-dark-300">Upcoming live calls and quick meeting validation access.</p>
              </div>
            </div>
            
            {interviews.length === 0 ? (
              <div className="p-8 text-center space-y-3">
                <Clock className="h-10 w-10 text-dark-300 mx-auto" />
                <p className="text-sm font-semibold">No interviews scheduled yet.</p>
                <p className="text-xs text-dark-300">Click the button above to register your first candidate invitation.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-dark-900/60 text-xs font-semibold uppercase tracking-wider text-dark-300 border-b border-dark-800">
                      <th className="px-6 py-4">Candidate</th>
                      <th className="px-6 py-4">Meeting ID</th>
                      <th className="px-6 py-4">Scheduled Date</th>
                      <th className="px-6 py-4">Status</th>
                      <th className="px-6 py-4 text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-dark-800/80 text-sm">
                    {interviews.slice(0, 10).map((itm) => {
                      const dateObj = new Date(itm.scheduled_at);
                      const isUpcoming = itm.status === 'scheduled';
                      
                      return (
                        <tr key={itm.id} className="hover:bg-dark-900/20 transition-colors">
                          <td className="px-6 py-4">
                            <div>
                              <p className="font-semibold">{itm.candidate_name}</p>
                              <p className="text-xs text-dark-300">{itm.candidate_email}</p>
                            </div>
                          </td>
                          <td className="px-6 py-4 font-mono text-xs">{itm.meeting_id}</td>
                          <td className="px-6 py-4">{dateObj.toLocaleString()}</td>
                          <td className="px-6 py-4">
                            <span className={`inline-flex px-2 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                              itm.status === 'completed' 
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                                : 'bg-brand-500/10 text-brand-400 border border-brand-500/20'
                            }`}>
                              {itm.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-center">
                            {isUpcoming ? (
                              <button 
                                onClick={() => navigate(`/interview/${itm.meeting_id}`)}
                                className="inline-flex items-center gap-1 bg-brand-600 hover:bg-brand-700 text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
                              >
                                <Video className="h-3.5 w-3.5" />
                                Start
                              </button>
                            ) : (
                              <button 
                                onClick={() => navigate('/reports')}
                                className="inline-flex items-center gap-1 bg-dark-800 border border-dark-700 hover:bg-dark-700 text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
                              >
                                View Report
                                <ArrowUpRight className="h-3.5 w-3.5" />
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </RecruiterLayout>
  );
};

export default Dashboard;
