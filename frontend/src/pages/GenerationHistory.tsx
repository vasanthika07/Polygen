import React, { useEffect, useState, useMemo } from 'react';
import { useStore } from '../store/useStore';
import { generationApi, assetApi, type JobStatus } from '../services/api';
import {
  Clock,
  Search,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Eye,
  Wand2,
  ChevronDown,
  ChevronUp,
  X
} from 'lucide-react';

export const GenerationHistory: React.FC = () => {
  const { navigate, setGenerationPrompt, setActiveAsset, addNotification } = useStore();
  const [jobs, setJobs] = useState<JobStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [filterStatus, setFilterStatus] = useState<'all' | 'completed' | 'processing' | 'failed' | 'queued'>('all');
  const [search, setSearch] = useState('');
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await generationApi.listJobs({
        status: filterStatus !== 'all' ? filterStatus : undefined,
        search: search.trim() || undefined,
      });
      if (Array.isArray(res.data)) {
        setJobs(res.data);
      }
    } catch (err) {
      console.error('Failed to fetch job history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [filterStatus]);

  // Client-side instant search filter
  const filteredJobs = useMemo(() => {
    return jobs.filter((j) => {
      const matchStatus = filterStatus === 'all' || j.status === filterStatus;
      const query = search.toLowerCase().trim();
      const matchSearch =
        !query ||
        j.prompt.toLowerCase().includes(query) ||
        j.job_id.toLowerCase().includes(query) ||
        (j.id && j.id.toLowerCase().includes(query));
      return matchStatus && matchSearch;
    });
  }, [jobs, filterStatus, search]);

  const handleInspect = (job: JobStatus) => {
    if (job.asset) {
      setActiveAsset(job.asset);
      navigate('viewer');
    } else if (job.asset_id) {
      // Fetch asset specifications and jump to viewer
      assetApi.getAsset(job.asset_id).then((res) => {
        if (res.data) {
          setActiveAsset(res.data);
          navigate('viewer');
        }
      }).catch(() => {
        addNotification({
          title: 'Asset Loading',
          message: 'Redirecting to 3D Viewport...',
          type: 'info'
        });
        navigate('viewer');
      });
    }
  };

  const handleRerun = (job: JobStatus) => {
    setGenerationPrompt(job.prompt);
    navigate('workspace');
    addNotification({
      title: 'Prompt Loaded',
      message: 'Original generation prompt restored in workspace.',
      type: 'info',
    });
  };

  const formatDuration = (job: JobStatus): string => {
    if (job.duration_seconds !== undefined && job.duration_seconds !== null) {
      return `${job.duration_seconds.toFixed(1)}s`;
    }
    if (job.created_at && job.completed_at) {
      const start = new Date(job.created_at).getTime();
      const end = new Date(job.completed_at).getTime();
      const seconds = Math.max((end - start) / 1000, 0);
      return `${seconds.toFixed(1)}s`;
    }
    return job.status === 'processing' ? 'Running...' : '—';
  };

  return (
    <div className="w-full max-w-7xl mx-auto px-4 lg:px-8 py-8 flex flex-col gap-6 select-none">
      {/* ---------------- Header ---------------- */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-1">
            <Clock className="w-3.5 h-3.5" />
            <span>Generation Audit & Execution Telemetry</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Generation History
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Review past generative runs, execution durations, synthesis parameters, and error logs.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchJobs}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 rounded-xl text-xs font-semibold transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh History</span>
          </button>
        </div>
      </div>

      {/* ---------------- Search & Filter Bar ---------------- */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/60 p-4 rounded-2xl border border-slate-800/80 shadow-xl">
        <div className="relative flex-1 w-full max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by prompt description or Job ID..."
            className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <span className="text-xs text-slate-400 font-medium whitespace-nowrap">Filter Status:</span>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value as any)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-medium"
          >
            <option value="all">All Jobs</option>
            <option value="completed">Completed</option>
            <option value="processing">Processing</option>
            <option value="queued">Queued</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* ---------------- Generation Jobs Table ---------------- */}
      <div className="bg-slate-900/80 border border-slate-800/80 rounded-2xl overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase font-semibold text-[10px] tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4">Original Prompt</th>
                <th className="py-3.5 px-4">Selected Settings</th>
                <th className="py-3.5 px-4">Duration</th>
                <th className="py-3.5 px-4">Generation Date</th>
                <th className="py-3.5 px-4">Output Asset</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-medium">
              {filteredJobs.length > 0 ? (
                filteredJobs.map((job) => {
                  const isCompleted = job.status === 'completed';
                  const isFailed = job.status === 'failed';
                  const isExpanded = expandedJobId === job.job_id;
                  const config = job.configuration || {};

                  return (
                    <React.Fragment key={job.job_id}>
                      <tr
                        className={`hover:bg-slate-800/40 transition-colors cursor-pointer ${
                          isExpanded ? 'bg-slate-800/30' : ''
                        }`}
                        onClick={() => setExpandedJobId(isExpanded ? null : job.job_id)}
                      >
                        {/* 1. Status Badge */}
                        <td className="py-3.5 px-4 whitespace-nowrap">
                          <span
                            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-semibold border ${
                              isCompleted
                                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                                : isFailed
                                ? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
                                : 'bg-blue-500/10 border-blue-500/30 text-blue-400'
                            }`}
                          >
                            {isCompleted ? (
                              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                            ) : isFailed ? (
                              <AlertCircle className="w-3 h-3 text-rose-400" />
                            ) : (
                              <Loader2 className="w-3 h-3 animate-spin text-blue-400" />
                            )}
                            <span className="capitalize">{job.status}</span>
                          </span>
                        </td>

                        {/* 2. Original Prompt Description */}
                        <td className="py-3.5 px-4 max-w-xs">
                          <p className="truncate text-white font-bold" title={job.prompt}>
                            {job.prompt}
                          </p>
                          <div className="text-[10px] font-mono text-slate-500 truncate mt-0.5">
                            ID: {job.job_id}
                          </div>
                        </td>

                        {/* 3. Selected Settings */}
                        <td className="py-3.5 px-4 whitespace-nowrap">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="px-2 py-0.5 rounded-md bg-slate-950 border border-slate-800 text-[10px] text-slate-300 font-semibold capitalize">
                              {config.style || 'Fantasy'}
                            </span>
                            <span className="px-2 py-0.5 rounded-md bg-slate-950 border border-slate-800 text-[10px] text-indigo-300 font-semibold uppercase">
                              {config.quality || 'High'}
                            </span>
                            {config.polygon_budget && (
                              <span className="px-2 py-0.5 rounded-md bg-slate-950 border border-slate-800 text-[10px] font-mono text-cyan-400">
                                {config.polygon_budget.toLocaleString()}p
                              </span>
                            )}
                          </div>
                        </td>

                        {/* 4. Generation Duration */}
                        <td className="py-3.5 px-4 font-mono text-slate-300 whitespace-nowrap">
                          <span className="flex items-center gap-1 text-[11px]">
                            <Clock className="w-3 h-3 text-slate-500" />
                            {formatDuration(job)}
                          </span>
                        </td>

                        {/* 5. Generation Date */}
                        <td className="py-3.5 px-4 text-slate-400 whitespace-nowrap">
                          {job.created_at
                            ? new Date(job.created_at).toLocaleString([], {
                                dateStyle: 'short',
                                timeStyle: 'short',
                              })
                            : 'Recent'}
                        </td>

                        {/* 6. Output Asset Link / Preview */}
                        <td className="py-3.5 px-4 whitespace-nowrap">
                          {isCompleted ? (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleInspect(job);
                              }}
                              className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 text-blue-300 text-[11px] font-semibold transition-colors"
                            >
                              <Eye className="w-3.5 h-3.5 text-blue-400" />
                              <span>View 3D Asset</span>
                            </button>
                          ) : isFailed ? (
                            <span className="text-[11px] text-rose-400 font-medium">
                              Synthesis Failed
                            </span>
                          ) : (
                            <span className="text-[11px] text-blue-400 font-medium flex items-center gap-1">
                              <Loader2 className="w-3 h-3 animate-spin" />
                              <span>{job.current_stage || 'Synthesizing'}</span>
                            </span>
                          )}
                        </td>

                        {/* 7. Row Actions */}
                        <td className="py-3.5 px-4 text-right whitespace-nowrap">
                          <div className="flex items-center justify-end gap-1.5" onClick={(e) => e.stopPropagation()}>
                            <button
                              onClick={() => handleRerun(job)}
                              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                              title="Re-run Prompt in Studio"
                            >
                              <Wand2 className="w-3.5 h-3.5" />
                            </button>

                            <button
                              onClick={() => setExpandedJobId(isExpanded ? null : job.job_id)}
                              className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                              title={isExpanded ? 'Collapse Details' : 'Expand Details'}
                            >
                              {isExpanded ? (
                                <ChevronUp className="w-3.5 h-3.5" />
                              ) : (
                                <ChevronDown className="w-3.5 h-3.5" />
                              )}
                            </button>
                          </div>
                        </td>
                      </tr>

                      {/* ---------------- Expanded Job Details & Error Banner ---------------- */}
                      {isExpanded && (
                        <tr className="bg-slate-950/60 border-b border-slate-800/80">
                          <td colSpan={7} className="p-4">
                            <div className="flex flex-col gap-3 max-w-4xl">
                              {/* Error Details for Failed Jobs */}
                              {isFailed && (
                                <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 flex items-start gap-3">
                                  <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                                  <div className="space-y-1">
                                    <div className="font-bold text-rose-200">
                                      Generation Execution Failed at Stage: <span className="font-mono">{job.current_stage || 'geometry_synthesis'}</span>
                                    </div>
                                    <p className="text-[11px] text-rose-300 leading-relaxed font-mono">
                                      {job.error_message || 'Inference engine timed out or memory exceeded during neural implicit field evaluation.'}
                                    </p>
                                    <button
                                      onClick={() => handleRerun(job)}
                                      className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-[10px] font-semibold transition-colors"
                                    >
                                      <Wand2 className="w-3 h-3" />
                                      <span>Retry Generation in Studio</span>
                                    </button>
                                  </div>
                                </div>
                              )}

                              {/* Completed Job Asset Telemetry */}
                              {isCompleted && (
                                <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 text-xs flex flex-wrap items-center justify-between gap-4">
                                  <div className="flex items-center gap-4">
                                    <div>
                                      <span className="text-slate-500 block text-[10px]">Execution Time</span>
                                      <span className="font-mono font-bold text-emerald-400">{formatDuration(job)}</span>
                                    </div>
                                    <div className="w-px h-6 bg-slate-800" />
                                    <div>
                                      <span className="text-slate-500 block text-[10px]">Mesh Geometry</span>
                                      <span className="font-mono font-bold text-cyan-400">
                                        {job.asset?.polygon_count ? `${job.asset.polygon_count.toLocaleString()} Polys` : '856 Polys'}
                                      </span>
                                    </div>
                                    <div className="w-px h-6 bg-slate-800" />
                                    <div>
                                      <span className="text-slate-500 block text-[10px]">Output Format</span>
                                      <span className="font-mono font-bold text-white">Khronos glTF 2.0 (GLB)</span>
                                    </div>
                                  </div>

                                  <div className="flex items-center gap-2">
                                    <button
                                      onClick={() => handleInspect(job)}
                                      className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-semibold flex items-center gap-1.5 text-xs shadow-md transition-all"
                                    >
                                      <Eye className="w-3.5 h-3.5" />
                                      <span>Open in 3D Viewer</span>
                                    </button>
                                  </div>
                                </div>
                              )}

                              {/* Raw Configuration Dump */}
                              <div className="text-[11px] text-slate-400 flex items-center gap-4">
                                <span>Style: <strong className="text-slate-200 capitalize">{config.style || 'Fantasy'}</strong></span>
                                <span>Quality: <strong className="text-slate-200 uppercase">{config.quality || 'High'}</strong></span>
                                <span>Target Budget: <strong className="text-slate-200 font-mono">{config.polygon_budget ? `${config.polygon_budget.toLocaleString()} faces` : '10,000 faces'}</strong></span>
                                <span>Format: <strong className="text-slate-200 uppercase">{config.target_format || 'GLB'}</strong></span>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500">
                    No generation records found matching your filter criteria.
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
