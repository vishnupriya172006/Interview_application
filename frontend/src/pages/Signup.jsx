import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert, Mail, Lock, User, Building, ChevronRight, AlertCircle } from 'lucide-react';

const Signup = () => {
  const { signup } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [password, setPassword] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!fullName || !email || !password) {
      setError('Please fill in all required fields.');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    setLoading(true);
    setError('');

    const res = await signup(email, password, fullName, companyName);
    if (res.success) {
      navigate('/dashboard');
    } else {
      setError(res.error);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-950 bg-grid text-dark-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md space-y-8 relative">
        {/* Glow ball */}
        <div className="absolute -top-12 -left-12 w-48 h-48 bg-brand-500/10 rounded-full blur-3xl animate-glow-pulse"></div>
        <div className="absolute -bottom-12 -right-12 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl animate-glow-pulse"></div>

        {/* Form Container */}
        <div className="glass p-8 rounded-2xl relative border border-dark-800 glow-indigo">
          {/* Header */}
          <div className="text-center space-y-3 mb-8">
            <Link to="/" className="inline-flex items-center gap-2 mb-2">
              <ShieldAlert className="h-10 w-10 text-brand-500" />
            </Link>
            <h2 className="text-2xl font-bold tracking-tight">Create your account</h2>
            <p className="text-sm text-dark-300">Set up a secure recruiter profile to begin screening.</p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-rose-500/15 border border-rose-500/20 text-rose-400 text-sm mb-6">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-1">
              <label className="text-xs font-semibold uppercase tracking-wider text-dark-300">Full Name</label>
              <div className="relative">
                <User className="absolute left-3 top-3 h-5 w-5 text-dark-300" />
                <input
                  type="text"
                  required
                  placeholder="John Doe"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 rounded-xl bg-dark-900 border border-dark-800 focus:border-brand-500 focus:outline-none text-sm transition-colors"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold uppercase tracking-wider text-dark-300">Work Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-5 w-5 text-dark-300" />
                <input
                  type="email"
                  required
                  placeholder="john@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 rounded-xl bg-dark-900 border border-dark-800 focus:border-brand-500 focus:outline-none text-sm transition-colors"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold uppercase tracking-wider text-dark-300">Company Name</label>
              <div className="relative">
                <Building className="absolute left-3 top-3 h-5 w-5 text-dark-300" />
                <input
                  type="text"
                  placeholder="Enterprise Inc."
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 rounded-xl bg-dark-900 border border-dark-800 focus:border-brand-500 focus:outline-none text-sm transition-colors"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold uppercase tracking-wider text-dark-300">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-5 w-5 text-dark-300" />
                <input
                  type="password"
                  required
                  placeholder="•••••••• (Min 6 chars)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 rounded-xl bg-dark-900 border border-dark-800 focus:border-brand-500 focus:outline-none text-sm transition-colors"
                />
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
                  Register & Continue
                  <ChevronRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          {/* Toggle form mode */}
          <div className="text-center mt-6 text-sm text-dark-300 border-t border-dark-800/80 pt-6">
            <p>
              Already have an account?{' '}
              <Link to="/login" className="text-brand-400 hover:text-brand-300 font-semibold transition-colors">
                Sign in instead
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Signup;
