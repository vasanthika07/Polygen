import React, { useState } from 'react';
import { useStore } from '../store/useStore';
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
  RefreshCw
} from 'lucide-react';

export const UserSettings: React.FC = () => {
  const { user, settings, updateSettings, addNotification } = useStore();

  const [defaultStyle, setDefaultStyle] = useState(settings.defaultStyle || 'medieval fantasy');
  const [defaultQuality, setDefaultQuality] = useState(settings.defaultQuality || 'high');
  const [polygonBudget, setPolygonBudget] = useState(settings.defaultPolygonBudget || 10000);
  const [textureRes, setTextureRes] = useState(settings.defaultTextureResolution || 1024);
  const [aiBackend, setAiBackend] = useState(settings.aiBackendPreference || 'local_shape');
  const [apiKey, setApiKey] = useState(settings.apiKey || 'poly_live_sec_8f9104bd39');
  const [copiedKey, setCopiedKey] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

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

  const handleSave = (e: React.FormEvent) => {
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
      message: 'Your generative defaults have been updated.',
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
            <span>Preferences & Configuration</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            User Settings
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Manage your account credentials, generative pipeline defaults, and API integrations.
          </p>
        </div>

        <button
          onClick={handleSave}
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-xs rounded-xl shadow-lg shadow-blue-500/25 transition-all self-start md:self-auto"
        >
          <Save className="w-4 h-4" />
          <span>{savedSuccess ? 'Settings Saved!' : 'Save Preferences'}</span>
        </button>
      </div>

      <form onSubmit={handleSave} className="flex flex-col gap-6">
        {/* Section 1: User Profile */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col gap-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <UserIcon className="w-4 h-4 text-blue-400" />
            <span>Account Profile</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-medium text-slate-400 block mb-1.5">Username</label>
              <input
                type="text"
                disabled
                value={user?.username || 'mesh_creator'}
                className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-300 disabled:opacity-60"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-400 block mb-1.5">Email Address</label>
              <input
                type="email"
                disabled
                value={user?.email || 'creator@polygen.ai'}
                className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-slate-300 disabled:opacity-60"
              />
            </div>
          </div>
        </div>

        {/* Section 2: Generation Defaults */}
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
                  className={`py-2 px-3 rounded-xl border text-xs font-semibold transition-all ${textureRes === res
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

        {/* Section 3: AI Engine Backend Preference */}
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
                className={`p-3.5 rounded-xl border text-left transition-all ${aiBackend === engine.id
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

        {/* Section 4: API Key Management */}
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

        {/* Section 5: Storage Quota */}
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
      </form>
    </div>
  );
};
