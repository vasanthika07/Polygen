import React, { useEffect, useState } from 'react';
import { useStore } from '../store/useStore';
import { generationApi, type JobStatus } from '../services/api';
import { 
  Clock, 
  Search, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  Eye, 
  Wand2
} from 'lucide-react';

export const GenerationHistory: React.FC = () => {
  const { navigate, setGenerationPrompt, setActiveAsset } = useStore();
  const [jobs, setJobs] = useState<JobStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [filterStatus, setFilterStatus] = useState<'all' | 'completed' | 'processing' | 'failed'>('all');
  const [search, setSearch] = useState('');

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await generationApi.listJobs();
      if (Array.isArray(res.data)) {
        setJobs(res.data);
      }
    } catch (err) {
      console.error('Failed to fetch job history:', err);
      // Fallback mock history if backend endpoint returns empty
      if (jobs.length === 0) {
        setJobs([
          {
            job_id: 'job_sword_01',
            prompt: 'A rusted medieval broadsword with a glowing blue sapphire in the hilt.',
            status: 'completed',
            progress: 100,
            stage: 'completed',
            created_at: new Date(Date.now() - 3600000).toISOString(),
            asset: {
              asset_id: 'asset_sword_01',
              asset_name: 'Medieval Broadsword',
              glb_url: '/models/sample_sword.glb',
              polygon_count: 856,
              file_size: 3567096,
              created_at: new Date(Date.now() - 3600000).toISOString(),
            }
          },
          {
            job_id: 'job_chair_02',
            prompt: 'A rustic oak wooden chair with carved armrests.',
            status: 'completed',
            progress: 100,
            stage: 'completed',
            created_at: new Date(Date.now() - 7200000).toISOString(),
            asset: {
              asset_id: 'asset_chair_02',
              asset_name: 'Rustic Oak Wooden Chair',
              glb_url: '/models/sample_chair.glb',
              polygon_count: 536,
              file_size: 3491948,
              created_at: new Date(Date.now() - 7200000).toISOString(),
            }
          },
          {
            job_id: 'job_robot_03',
            prompt: 'A futuristic metallic battle robot with neon green visor.',
            status: 'completed',
            progress: 100,
            stage: 'completed',
            created_at: new Date(Date.now() - 14400000).toISOString(),
            asset: {
              asset_id: 'asset_robot_03',
              asset_name: 'Futuristic Battle Robot',
              glb_url: '/models/sample_robot.glb',
              polygon_count: 548,
              file_size: 4026384,
              created_at: new Date(Date.now() - 14400000).toISOString(),
            }
          },
          {
            job_id: 'job_sculpture_04',
            prompt: 'An ancient carved stone sculpture covered in moss.',
            status: 'completed',
            progress: 100,
            stage: 'completed',
            created_at: new Date(Date.now() - 28800000).toISOString(),
            asset: {
              asset_id: 'asset_sculpture_04',
              asset_name: 'Ancient Mossy Stone Sculpture',
              glb_url: '/models/sample_sculpture.glb',
              polygon_count: 5120,
              file_size: 3719040,
              created_at: new Date(Date.now() - 28800000).toISOString(),
            }
          }
        ]);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const filteredJobs = jobs.filter((j) => {
    const matchStatus = filterStatus === 'all' || j.status === filterStatus;
    const matchSearch = j.prompt.toLowerCase().includes(search.toLowerCase()) || j.job_id.toLowerCase().includes(search.toLowerCase());
    return matchStatus && matchSearch;
  });

  const handleInspect = (job: JobStatus) => {
    if (job.asset) {
      setActiveAsset(job.asset);
      navigate('viewer');
    }
  };

  const handleRerun = (job: JobStatus) => {
    setGenerationPrompt(job.prompt);
    navigate('workspace');
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 lg:px-8 py-8 flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Clock className="w-3.5 h-3.5" />
            <span>Generation Audit & Logs</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Generation History
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Review past synthesis jobs, inspect parameters, retry prompts, or load models in the 3D viewer.
          </p>
        </div>

        <button
          onClick={fetchJobs}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-xl text-xs font-semibold transition-colors self-start md:self-auto"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Jobs</span>
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-2xl border border-slate-800/80">
        <div className="relative flex-1 max-w-md w-full">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by prompt text or Job ID..."
            className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <span className="text-xs text-slate-400 font-medium">Status:</span>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as any)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          >
            <option value="all">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="processing">Processing</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* History Table */}
      <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase font-semibold text-[10px] tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4">Job ID</th>
                <th className="py-3.5 px-4">Prompt Description</th>
                <th className="py-3.5 px-4">Mesh Polygons</th>
                <th className="py-3.5 px-4">Created At</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {filteredJobs.length > 0 ? (
                filteredJobs.map((job) => {
                  const isCompleted = job.status === 'completed';
                  const isFailed = job.status === 'failed';

                  return (
                    <tr key={job.job_id} className="hover:bg-slate-800/40 transition-colors">
                      {/* Status */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold border ${
                          isCompleted
                            ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                            : isFailed
                            ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                            : 'bg-blue-500/10 border-blue-500/30 text-blue-400'
                        }`}>
                          {isCompleted ? (
                            <CheckCircle2 className="w-3 h-3" />
                          ) : isFailed ? (
                            <AlertCircle className="w-3 h-3" />
                          ) : (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          )}
                          <span className="capitalize">{job.status}</span>
                        </span>
                      </td>

                      {/* Job ID */}
                      <td className="py-3.5 px-4 font-mono text-[11px] text-slate-400">
                        {job.job_id.slice(0, 14)}...
                      </td>

                      {/* Prompt */}
                      <td className="py-3.5 px-4 max-w-sm">
                        <p className="truncate text-slate-100 font-semibold" title={job.prompt}>
                          {job.prompt}
                        </p>
                      </td>

                      {/* Polygons */}
                      <td className="py-3.5 px-4 font-mono text-cyan-400">
                        {job.asset?.polygon_count ? `${job.asset.polygon_count.toLocaleString()} polys` : '—'}
                      </td>

                      {/* Created At */}
                      <td className="py-3.5 px-4 text-slate-400 whitespace-nowrap">
                        {job.created_at ? new Date(job.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : 'Just now'}
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-2">
                          {job.asset && (
                            <button
                              onClick={() => handleInspect(job)}
                              className="p-1.5 rounded-lg bg-blue-600/20 text-blue-400 hover:bg-blue-600 hover:text-white transition-colors"
                              title="Inspect Model in 3D Viewport"
                            >
                              <Eye className="w-3.5 h-3.5" />
                            </button>
                          )}
                          <button
                            onClick={() => handleRerun(job)}
                            className="p-1.5 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
                            title="Re-run Prompt in Studio"
                          >
                            <Wand2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No generation records match your filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
