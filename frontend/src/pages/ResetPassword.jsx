import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert } from 'lucide-react';

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { resetPassword } = useAuth();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const token = searchParams.get('token');

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    if (!token) return setError('This password reset link is invalid or incomplete.');
    if (password.length < 8) return setError('Use a password with at least 8 characters.');
    if (password !== confirmPassword) return setError('The passwords do not match.');

    setLoading(true);
    const result = await resetPassword(token, password);
    setLoading(false);
    if (!result.success) return setError(result.error);
    navigate('/login', { replace: true, state: { resetComplete: true } });
  };

  return (
    <div className="min-h-screen bg-dark-950 text-dark-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md glass p-8 rounded-2xl border border-dark-800 space-y-6">
        <div className="text-center space-y-3">
          <ShieldAlert className="h-10 w-10 text-brand-500 mx-auto" />
          <h1 className="text-2xl font-bold">Set a new password</h1>
          <p className="text-sm text-dark-300">Reset links expire after one hour.</p>
        </div>
        {error && <p role="alert" className="text-sm text-rose-400">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block text-sm space-y-2">
            <span>New password</span>
            <input type="password" autoComplete="new-password" required minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} className="w-full rounded-lg bg-dark-900 border border-dark-700 p-3" />
          </label>
          <label className="block text-sm space-y-2">
            <span>Confirm new password</span>
            <input type="password" autoComplete="new-password" required minLength={8} value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} className="w-full rounded-lg bg-dark-900 border border-dark-700 p-3" />
          </label>
          <button disabled={loading} className="w-full rounded-lg bg-brand-600 hover:bg-brand-700 disabled:opacity-60 p-3 font-bold">
            {loading ? 'Updating…' : 'Update password'}
          </button>
        </form>
        <Link to="/login" className="block text-center text-sm text-brand-400 hover:text-brand-300">Back to sign in</Link>
      </div>
    </div>
  );
};

export default ResetPassword;
