import React, { useState, useEffect } from 'react';
import { useStore } from '../store/useStore';
import { authApi } from '../services/api';
import {
  Settings,
  User as UserIcon,
  Key,
  HardDrive,
  Sliders,
  Cpu,
  Copy,
  Check,
  Save,
  RefreshCw,
  Lock,
  ShieldCheck,
  AlertCircle,
  Loader2
} from 'lucide-react';

export const UserSettings: React.FC = () => {
  const { user, updateUser, settings, updateSettings, addNotification } = useStore();

  // User Profile Form
  const [displayName, setDisplayName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [isUpdatingProfile, setIsUpdatingProfile] = useState(false);
  const [profileSuccess, setProfileSuccess] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);

  // Change Password Form
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  // Settings & Preferences
  const [defaultStyle, setDefaultStyle] = useState(settings.defaultStyle || 'medieval fantasy');
  const [defaultQuality, setDefaultQuality] = useState(settings.defaultQuality || 'high');
  const [polygonBudget, setPolygonBudget] = useState(settings.defaultPolygonBudget || 10000);
  const [textureRes, setTextureRes] = useState(settings.defaultTextureResolution || 1024);
  const [aiBackend, setAiBackend] = useState(settings.aiBackendPreference || 'local_shape');
  const [apiKey, setApiKey] = useState(settings.apiKey || 'poly_live_sec_8f9104bd39');
  const [copiedKey, setCopiedKey] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (user) {
      setDisplayName(user.name || '');
      setEmail(user.email || '');
    }
  }, [user]);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileError(null);
    setProfileSuccess(false);

    if (!email.trim()) {
      setProfileError('Email address cannot be empty');
      return;
    }

    setIsUpdatingProfile(true);
    try {
      const res = await authApi.updateProfile({
        name: displayName.trim() || undefined,
        email: email.trim(),
      });
      updateUser(res.data);
      setProfileSuccess(true);
      addNotification({
        title: 'Profile Updated',
        message: 'Your account profile details have been saved.',
        type: 'success',
      });
      setTimeout(() => setProfileSuccess(false), 4000);
    } catch (err: any) {
      console.error('Update profile error:', err);
      const msg = err.response?.data?.detail || 'Failed to update profile';
      setProfileError(msg);
      addNotification({
        title: 'Profile Update Failed',
        message: msg,
        type: 'error',
      });
    } finally {
      setIsUpdatingProfile(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(false);

    if (!currentPassword) {
      setPasswordError('Please enter your current password');
      return;
    }
    if (newPassword.length < 8) {
      setPasswordError('New password must be at least 8 characters long');
      return;
    }
    if (newPassword !== confirmNewPassword) {
      setPasswordError('New passwords do not match');
      return;
    }

    setIsChangingPassword(true);
    try {
      await authApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmNewPassword('');
      addNotification({
        title: 'Password Changed',
        message: 'Your account credentials have been securely updated.',
        type: 'success',
      });
      setTimeout(() => setPasswordSuccess(false), 4000);
    } catch (err: any) {
      console.error('Change password error:', err);
      const msg = err.response?.data?.detail || 'Failed to update password';
      setPasswordError(msg);
      addNotification({
        title: 'Password Change Failed',
        message: msg,
        type: 'error',
      });
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleCopyKey = () => {
    navigator.clipboard.writeText(apiKey);
    setCopiedKey(true);
    addNotification({
      title: 'API Key Copied',
      message: 'Secret key copied to clipboard.',
      type: 'info',
    });
    setTimeout(() => setCopiedKey(false), 2000);
  };

  const handleRegenerateKey = () => {
    const newKey = `poly_live_sec_${Math.random().toString(36).substring(2, 10)}${Math.random().toString(36).substring(2, 6)}`;
    setApiKey(newKey);
    updateSettings({ apiKey: newKey });
    addNotification({
      title: 'API Key Rotated',
      message: 'Generated a new production authentication token.',
      type: 'warning',
    });
  };

  const handleSavePreferences = (e: React.FormEvent) => {
    e.preventDefault();
    updateSettings({
      defaultStyle,
      defaultQuality,
      defaultPolygonBudget: polygonBudget,
      defaultTextureResolution: textureRes,
      aiBackendPreference: aiBackend,
      apiKey,
    });
    setSavedSuccess(true);
    addNotification({
      title: 'Settings Saved',
      message: 'Your generative pipeline defaults have been updated.',
      type: 'success',
    });
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 lg:px-8 py-8 flex flex-col gap-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Settings className="w-3.5 h-3.5" />
            <span>Preferences & Account Settings</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            User Settings
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Manage your account credentials, security profile, and 3D generative defaults.
          </p>
        </div>

        <button
          onClick={handleSavePreferences}
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-blue-500/25 transition-all self-start md:self-auto"
        >
          <Save className="w-4 h-4" />
          <span>{savedSuccess ? 'Defaults Saved!' : 'Save Defaults'}</span>
        </button>
      </div>

      <div className="flex flex-col gap-6">
        {/* Section 1: User Profile & Account Info */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <UserIcon className="w-4 h-4 text-blue-400" />
              <span>Account Profile</span>
            </h3>
            {user?.id && (
              <span className="text-[10px] font-mono text-slate-500 bg-slate-950 px-2.5 py-1 rounded-lg border border-slate-800">
                User ID: {user.id.substring(0, 13)}...
              </span>
            )}
          </div>

          {profileError && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-2 text-xs text-rose-400">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{profileError}</span>
            </div>
          )}

          {profileSuccess && (
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center gap-2 text-xs text-emerald-400">
              <Check className="w-4 h-4 shrink-0" />
              <span>Profile updated successfully</span>
            </div>
          )}

          <form onSubmit={handleUpdateProfile} className="flex flex-col gap-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-medium text-slate-400 block mb-1.5">Username</label>
                <input
                  type="text"
                  disabled
                  value={user?.username || 'creator'}
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-300 disabled:opacity-50 cursor-not-allowed"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1.5">Display Name</label>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="Your Name"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1.5">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your.email@polygen.ai"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <button
                type="submit"
                disabled={isUpdatingProfile}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs rounded-xl shadow-md transition-all disabled:opacity-50"
              >
                {isUpdatingProfile ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <span>Update Profile</span>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Section 2: Security & Password Management */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Lock className="w-4 h-4 text-emerald-400" />
            <span>Password & Security</span>
          </h3>
          <p className="text-xs text-slate-400">
            Update your account password to ensure secure access to your 3D asset pipeline:
          </p>

          {passwordError && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-2 text-xs text-rose-400">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{passwordError}</span>
            </div>
          )}

          {passwordSuccess && (
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center gap-2 text-xs text-emerald-400">
              <ShieldCheck className="w-4 h-4 shrink-0" />
              <span>Password successfully updated</span>
            </div>
          )}

          <form onSubmit={handleChangePassword} className="flex flex-col gap-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1.5">Current Password</label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1.5">New Password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Min 8 characters"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-300 block mb-1.5">Confirm New Password</label>
                <input
                  type="password"
                  value={confirmNewPassword}
                  onChange={(e) => setConfirmNewPassword(e.target.value)}
                  placeholder="Repeat new password"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <button
                type="submit"
                disabled={isChangingPassword}
                className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-semibold text-xs rounded-xl shadow-md transition-all disabled:opacity-50"
              >
                {isChangingPassword ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Updating...</span>
                  </>
                ) : (
                  <span>Change Password</span>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Section 3: Generation Defaults */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-5">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Sliders className="w-4 h-4 text-indigo-400" />
            <span>Generation Defaults</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1.5">Default Style</label>
              <select
                value={defaultStyle}
                onChange={(e) => setDefaultStyle(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
              >
                <option value="medieval fantasy">Medieval Fantasy</option>
                <option value="realistic">Hyper-Realistic</option>
                <option value="stylized">Stylized</option>
                <option value="sci-fi">Sci-Fi / Cyberpunk</option>
                <option value="low-poly">Low-Poly</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-300 block mb-1.5">Default Quality Tier</label>
              <select
                value={defaultQuality}
                onChange={(e) => setDefaultQuality(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
              >
                <option value="draft">Draft (Fastest)</option>
                <option value="standard">Standard</option>
                <option value="high">High (Recommended)</option>
                <option value="ultra">Ultra</option>
              </select>
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between text-xs text-slate-300 mb-1.5">
              <span>Default Polygon Budget</span>
              <span className="font-mono text-blue-400 font-semibold">{polygonBudget.toLocaleString()} polys</span>
            </div>
            <input
              type="range"
              min={1000}
              max={50000}
              step={1000}
              value={polygonBudget}
              onChange={(e) => setPolygonBudget(parseInt(e.target.value))}
              className="w-full accent-blue-500"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-300 block mb-1.5">Default Texture Resolution</label>
            <div className="grid grid-cols-3 gap-3">
              {[512, 1024, 2048].map((res) => (
                <button
                  key={res}
                  type="button"
                  onClick={() => setTextureRes(res)}
                  className={`py-2 px-3 rounded-xl border text-xs font-semibold transition-all ${
                    textureRes === res
                      ? 'bg-blue-600 border-blue-500 text-white shadow-md'
                      : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  {res} × {res}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Section 4: AI Engine Backend Preference */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Cpu className="w-4 h-4 text-emerald-400" />
            <span>AI Backend Engine</span>
          </h3>
          <p className="text-xs text-slate-400">
            Select the underlying neural synthesis model used for mesh generation:
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {[
              { id: 'local_shape', title: 'OpenAI Shap-E', desc: 'Implicit diffusion fields with Marching Cubes' },
              { id: 'hunyuan3d', title: 'Tencent Hunyuan3D', desc: 'High-density geometric text-to-3D pipeline' },
              { id: 'triposr', title: 'TripoSR (Image-to-3D)', desc: 'Fast single-view mesh reconstruction' },
              { id: 'procedural', title: 'Procedural Volumetric', desc: 'Deterministic low-latency CSG engine' },
            ].map((engine) => (
              <button
                key={engine.id}
                type="button"
                onClick={() => setAiBackend(engine.id)}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  aiBackend === engine.id
                    ? 'bg-blue-600/20 border-blue-500 text-blue-300 shadow-md'
                    : 'bg-slate-950/80 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                <div className="text-xs font-bold text-slate-100 flex items-center justify-between">
                  <span>{engine.title}</span>
                  {aiBackend === engine.id && <Check className="w-4 h-4 text-blue-400" />}
                </div>
                <div className="text-[11px] text-slate-400 mt-1">{engine.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Section 5: API Key Management */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Key className="w-4 h-4 text-amber-400" />
            <span>Production API Access</span>
          </h3>
          <p className="text-xs text-slate-400">
            Authenticate automated CI/CD jobs, Blender plugins, or Unreal Engine SDKs:
          </p>

          <div className="flex items-center gap-2">
            <input
              type="password"
              readOnly
              value={apiKey}
              className="flex-1 bg-slate-950 font-mono text-xs text-slate-200 border border-slate-800 rounded-xl px-3.5 py-2.5 focus:outline-none"
            />
            <button
              type="button"
              onClick={handleCopyKey}
              className="p-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl transition-colors"
              title="Copy API Key"
            >
              {copiedKey ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
            </button>
            <button
              type="button"
              onClick={handleRegenerateKey}
              className="p-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl transition-colors"
              title="Regenerate Key"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Section 6: Storage Quota */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-indigo-400" />
              <span>Storage Quota</span>
            </span>
            <span className="text-xs font-mono text-slate-400">14.85 MB / 1,024 MB</span>
          </div>
          <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
            <div className="bg-gradient-to-r from-blue-500 to-indigo-500 h-full w-[1.5%]" />
          </div>
          <p className="text-[11px] text-slate-500">
            Free tier allows up to 1 GB of storage for binary GLB models and textures.
          </p>
        </div>
      </div>
    </div>
  );
};
