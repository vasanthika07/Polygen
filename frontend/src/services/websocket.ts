import { useStore } from '../store/useStore';
import { assetApi, generationApi } from './api';

export class JobWebSocket {
  private socket: WebSocket | null = null;
  private jobId: string;
  private pingInterval: any = null;
  private pollInterval: any = null;
  private isDone = false;

  constructor(jobId: string) {
    this.jobId = jobId;
  }

  connect() {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws/jobs/${this.jobId}`;

      console.log(`[JobWebSocket] Connecting to WebSocket: ${wsUrl}`);
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        console.log(`[JobWebSocket] Connected for job: ${this.jobId}`);
        this.stopPolling();
        // Send keepalive ping every 15 seconds
        this.pingInterval = setInterval(() => {
          if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send('ping');
          }
        }, 15000);
      };

      this.socket.onmessage = async (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'pong') return;

          console.log('[JobWebSocket] Stage update:', data);
          const { stage, progress, message, data: extraData } = data;

          useStore.getState().updateGenerationProgress({
            stage,
            progress,
            message,
            data: extraData,
          });

          // When generation is completed, fetch the asset and set it active in the viewer
          if (stage === 'completed') {
            this.isDone = true;
            if (extraData?.asset_id) {
              try {
                const res = await assetApi.getAsset(extraData.asset_id);
                const asset = res.data;
                useStore.getState().setActiveAsset(asset);
                useStore.getState().addAsset(asset);
              } catch (e) {
                console.error('[JobWebSocket] Failed to fetch completed asset:', e);
              }
            }
            this.disconnect();
          } else if (stage === 'failed') {
            this.isDone = true;
            this.disconnect();
          }
        } catch (e) {
          console.error('[JobWebSocket] Error parsing message:', e);
        }
      };

      this.socket.onerror = (err) => {
        console.warn('[JobWebSocket] Error encountered, falling back to HTTP polling:', err);
        this.startPolling();
      };

      this.socket.onclose = () => {
        console.log(`[JobWebSocket] Closed for job ${this.jobId}`);
        if (!this.isDone) {
          this.startPolling();
        }
        this.cleanupSocket();
      };
    } catch (err) {
      console.warn('[JobWebSocket] Initialization failed, falling back to HTTP polling:', err);
      this.startPolling();
    }
  }

  startPolling() {
    if (this.pollInterval || this.isDone) return;
    console.log(`[JobWebSocket] Engaging HTTP polling fallback for job: ${this.jobId}`);

    const poll = async () => {
      if (this.isDone) return;
      try {
        const res = await generationApi.getJobStatus(this.jobId);
        const job = res.data;
        if (!job) return;

        useStore.getState().updateGenerationProgress({
          stage: job.current_stage || job.status,
          progress: job.progress || 0,
          message: job.error_message || `Pipeline stage: ${job.current_stage}`,
          data: { asset_id: job.asset_id },
        });

        if (job.status === 'completed') {
          this.isDone = true;
          this.stopPolling();
          if (job.asset_id) {
            try {
              const aRes = await assetApi.getAsset(job.asset_id);
              useStore.getState().setActiveAsset(aRes.data);
              useStore.getState().addAsset(aRes.data);
            } catch (err) {
              console.error('[JobWebSocket] Polling failed to fetch completed asset:', err);
            }
          }
        } else if (job.status === 'failed') {
          this.isDone = true;
          this.stopPolling();
        }
      } catch (err) {
        console.error('[JobWebSocket] Polling error:', err);
      }
    };

    poll();
    this.pollInterval = setInterval(poll, 1500);
  }

  stopPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  disconnect() {
    this.isDone = true;
    if (this.socket) {
      try {
        this.socket.close();
      } catch {
        // ignore
      }
      this.socket = null;
    }
    this.cleanupSocket();
    this.stopPolling();
  }

  private cleanupSocket() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }
}
