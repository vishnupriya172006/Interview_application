import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert, Mail, Lock, ChevronRight, AlertCircle } from 'lucide-react';

const Login = () => {
  const { login, forgotPassword } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [resetSent, setResetSent] = useState(false);
  const [showForgot, setShowForgot] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || (!showForgot && !password)) {
      setError('Please fill in all required fields.');
      return;
    }

    setLoading(true);
    setError('');

    if (showForgot) {
      // Forgot password request
      const res = await forgotPassword(email);
      if (res.success) {
        setResetSent(true);
        setError('');
      } else {
        setError(res.error);
      }
      setLoading(false);
    } else {
      // Normal Login
      const res = await login(email, password);
      if (res.success) {
        navigate('/dashboard');
      } else {
        setError(res.error);
        setLoading(false);
      }
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
            <h2 className="text-2xl font-bold tracking-tight">
              {showForgot ? 'Reset password' : 'Sign in to InterviewGuard'}
            </h2>
            <p className="text-sm text-dark-300">
              {showForgot 
                ? 'Enter your email to request recovery details.' 
                : 'Access recruiter tools and live integrity monitors.'
              }
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-rose-500/15 border border-rose-500/20 text-rose-400 text-sm mb-6">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Password Reset Confirmation */}
          {resetSent && showForgot && (
            <div className="p-4 rounded-lg bg-emerald-500/15 border border-emerald-500/20 text-emerald-400 text-sm mb-6 space-y-2">
              <p className="font-bold">Recovery Instructions Sent</p>
              <p className="text-xs opacity-90 leading-relaxed">
                If the email is registered in our database, password reset instructions have been logged. Please inspect your SMTP server console logs for simulated recovery link coordinates.
              </p>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-dark-300">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-5 w-5 text-dark-300" />
                <input
                  type="email"
                  required
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 rounded-xl bg-dark-900 border border-dark-800 focus:border-brand-500 focus:outline-none text-sm transition-colors"
                />
              </div>
            </div>

            {!showForgot && (
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-xs font-semibold uppercase tracking-wider text-dark-300">Password</label>
                  <button 
                    type="button"
                    onClick={() => { setShowForgot(true); setError(''); setResetSent(false); }}
                    className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
                  >
                    Forgot password?
                  </button>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-5 w-5 text-dark-300" />
                  <input
                    type="password"
                    required
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 pr-4 py-3 rounded-xl bg-dark-900 border border-dark-800 focus:border-brand-500 focus:outline-none text-sm transition-colors"
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:bg-brand-600/40 text-sm font-bold py-3.5 rounded-xl transition-all glow-indigo"
            >
              {loading ? (
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-t-transparent border-white"></div>
              ) : (
                <>
                  {showForgot ? 'Send Recovery Code' : 'Secure Sign In'}
                  <ChevronRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          {/* Toggle Form Mode */}
          <div className="text-center mt-6 text-sm text-dark-300 border-t border-dark-800/80 pt-6">
            {showForgot ? (
              <button 
                onClick={() => { setShowForgot(false); setError(''); }}
                className="text-brand-400 hover:text-brand-300 transition-colors"
              >
                Back to secure sign in
              </button>
            ) : (
              <p>
                Don't have an account?{' '}
                <Link to="/signup" className="text-brand-400 hover:text-brand-300 font-semibold transition-colors">
                  Create one now
                </Link>
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
