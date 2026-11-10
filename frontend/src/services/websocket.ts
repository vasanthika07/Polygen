import { useStore } from '../store/useStore';
import { assetApi } from './api';

export class JobWebSocket {
  private socket: WebSocket | null = null;
  private jobId: string;
  private pingInterval: any = null;

  constructor(jobId: string) {
    this.jobId = jobId;
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/jobs/${this.jobId}`;

    console.log(`Connecting to WebSocket: ${wsUrl}`);
    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log(`WebSocket connected for job ${this.jobId}`);
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

        console.log('WS Stage Update:', data);
        const { stage, progress, message, data: extraData } = data;

        useStore.getState().updateGenerationProgress({
          stage,
          progress,
          message,
          data: extraData,
        });

        // When generation is completed, fetch the asset and set it active in the viewer
        if (stage === 'completed' && extraData?.asset_id) {
          try {
            const res = await assetApi.getAsset(extraData.asset_id);
            const asset = res.data;
            useStore.getState().setActiveAsset(asset);
            useStore.getState().addAsset(asset);
          } catch (e) {
            console.error('Failed to fetch completed asset:', e);
          }
          this.disconnect();
        } else if (stage === 'failed') {
          this.disconnect();
        }
      } catch (e) {
        console.error('Failed to parse WS message:', e);
      }
    };

    this.socket.onerror = (err) => {
      console.error('WebSocket error:', err);
    };

    this.socket.onclose = () => {
      console.log(`WebSocket closed for job ${this.jobId}`);
      this.cleanup();
    };
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.cleanup();
  }

  private cleanup() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }
}

