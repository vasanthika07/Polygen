import React, { useState, useEffect } from 'react';
import { useStore } from '../store/useStore';
import { authApi, extractErrorMessage } from '../services/api';
import { 
  Box, 
  Lock, 
  Mail, 
  ArrowRight, 
  AlertCircle, 
  Eye, 
  EyeOff, 
  Sparkles,
  Loader2,
  ShieldCheck
} from 'lucide-react';

export const Login: React.FC = () => {
  const { navigate, setSession, addNotification } = useStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Restore remembered login on mount
  useEffect(() => {
    const remembered = localStorage.getItem('polygen_remembered_login');
    if (remembered) {
      setEmail(remembered);
      setRememberMe(true);
    }
  }, []);

  const handleFillDemo = () => {
    setEmail('demo_creator@polygen.ai');
    setPassword('PolyGen2026Secure!');
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanIdentifier = email.trim();

    if (!cleanIdentifier) {
      setError('Please provide your email address or username.');
      return;
    }

    if (!password) {
      setError('Please enter your account password.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await authApi.login({
        username_or_email: cleanIdentifier,
        password: password,
      });

      const { access_token, refresh_token, user } = res.data;
      setSession(access_token, refresh_token || null, user);

      // Handle remember me
      if (rememberMe) {
        localStorage.setItem('polygen_remembered_login', cleanIdentifier);
      } else {
        localStorage.removeItem('polygen_remembered_login');
      }

      addNotification({
        title: 'Authentication Successful',
        message: `Welcome back, ${user.username || user.name}! Your generative studio is active.`,
        type: 'success',
      });

      navigate('dashboard');
    } catch (err: any) {
      console.error('Login error:', err);
      const errorMsg = extractErrorMessage(
        err,
        'Authentication failed: incorrect email/username or password. Please verify credentials or use the demo account.'
      );
      setError(errorMsg);
      addNotification({
        title: 'Sign In Failed',
        message: errorMsg,
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full min-h-[calc(100vh-80px)] flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full bg-slate-900/90 backdrop-blur-2xl border border-slate-800 rounded-3xl p-8 shadow-2xl relative overflow-hidden">
        {/* Glow backdrop */}
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-48 h-48 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

        {/* Brand Header */}
        <div className="flex flex-col items-center text-center mb-6">
          <div 
            onClick={() => navigate('landing')}
            className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-violet-600 flex items-center justify-center text-white shadow-xl shadow-blue-500/25 mb-4 cursor-pointer hover:scale-105 transition-transform"
          >
            <Box className="w-7 h-7" />
          </div>
          <h2 className="text-2xl font-extrabold text-white">Sign in to PolyGen</h2>
          <p className="text-xs text-slate-400 mt-1">
            Access your spatial asset library and generative 3D pipeline
          </p>
        </div>

        {/* Security / Backend Storage Info Badge */}
        <div className="mb-5 p-2.5 bg-slate-950/70 border border-slate-800/80 rounded-xl flex items-center gap-2.5 text-[11px] text-slate-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>
            Secure backend authentication with salted bcrypt hashing & JWT sessions.
          </span>
        </div>

        {/* Demo Credentials Quick Fill Banner */}
        <div className="p-3 mb-5 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-blue-300">
            <Sparkles className="w-4 h-4 shrink-0 text-blue-400" />
            <div>
              <span className="font-semibold">Demo Account</span>
              <span className="block text-[10px] text-blue-400/80">demo_creator@polygen.ai</span>
            </div>
          </div>
          <button
            type="button"
            onClick={handleFillDemo}
            className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-semibold text-[11px] shadow-sm transition-all"
          >
            Auto Fill
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3 mb-5 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-2 text-xs text-rose-400">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">
              Email Address or Username
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                required
                disabled={loading}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="creator@polygen.ai or username"
                className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all disabled:opacity-60"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-slate-300">Password</label>
              <button
                type="button"
                onClick={() => addNotification({ title: 'Password Requirements', message: 'Minimum 8 characters with at least one uppercase letter (A-Z), lowercase letter (a-z), and number or symbol.', type: 'info' })}
                className="text-[11px] text-blue-400 hover:text-blue-300 transition-colors"
              >
                Requirements
              </button>
            </div>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                disabled={loading}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-10 pr-10 py-2.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all disabled:opacity-60"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-[10px] text-slate-500 mt-1">
              Minimum 8 characters (requires A-Z, a-z, and 0-9 or symbol)
            </p>
          </div>

          <div className="flex items-center gap-2 mt-1">
            <input
              type="checkbox"
              id="remember"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="rounded bg-slate-950 border-slate-800 text-blue-600 focus:ring-0"
            />
            <label htmlFor="remember" className="text-xs text-slate-400 cursor-pointer">
              Remember this account on this device
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-2 w-full flex items-center justify-center gap-2 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-blue-500/25 transition-all disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Authenticating with Backend...</span>
              </>
            ) : (
              <>
                <span>Sign In Securely</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        {/* Footer Link */}
        <div className="mt-6 pt-6 border-t border-slate-800/80 text-center text-xs text-slate-400">
          Don't have an account?{' '}
          <button
            onClick={() => navigate('register')}
            className="text-blue-400 hover:text-blue-300 font-semibold transition-colors"
          >
            Create account
          </button>
        </div>
      </div>
    </div>
  );
};
