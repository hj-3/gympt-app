import { SignalingClient, Role } from 'amazon-kinesis-video-streams-webrtc';
import { KVSConfig, KVSConnection } from '@/types';

export class KVSWebRTCClient {
  private signalingClient: SignalingClient | null = null;
  private peerConnection: RTCPeerConnection | null = null;
  private dataChannel: RTCDataChannel | null = null;
  private localStream: MediaStream | null = null;

  constructor(private config: KVSConfig) {}

  async connect(): Promise<KVSConnection> {
    try {
      // Create Signaling Client
      this.signalingClient = new SignalingClient({
        channelARN: this.getChannelARN(),
        channelEndpoint: await this.getChannelEndpoint(),
        role: Role.MASTER,
        region: this.config.region,
        credentials: {
          accessKeyId: this.config.credentials.accessKeyId,
          secretAccessKey: this.config.credentials.secretAccessKey,
          sessionToken: this.config.credentials.sessionToken,
        },
        systemClockOffset: 0,
      });

      // Create RTCPeerConnection
      this.peerConnection = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.kinesisvideo.ap-northeast-2.amazonaws.com:443' },
        ],
      });

      // Setup event handlers
      this.setupSignalingClientHandlers();
      this.setupPeerConnectionHandlers();

      // Open signaling connection
      await this.signalingClient.open();

      // Get local media stream
      this.localStream = await this.getLocalMediaStream();

      // Add tracks to peer connection
      this.localStream.getTracks().forEach((track) => {
        this.peerConnection!.addTrack(track, this.localStream!);
      });

      // Create data channel for metadata
      this.dataChannel = this.peerConnection.createDataChannel('gympt-metadata');
      this.setupDataChannelHandlers();

      return {
        signalingClient: this.signalingClient,
        peerConnection: this.peerConnection,
        dataChannel: this.dataChannel,
      };
    } catch (error) {
      console.error('KVS WebRTC connection failed:', error);
      throw error;
    }
  }

  private setupSignalingClientHandlers() {
    if (!this.signalingClient) return;

    this.signalingClient.on('open', () => {
      console.log('Signaling client connected');
    });

    this.signalingClient.on('sdpOffer', async (offer: RTCSessionDescriptionInit) => {
      console.log('Received SDP offer');
      await this.peerConnection!.setRemoteDescription(offer);
      const answer = await this.peerConnection!.createAnswer();
      await this.peerConnection!.setLocalDescription(answer);
      this.signalingClient!.sendSdpAnswer(this.peerConnection!.localDescription!);
    });

    this.signalingClient.on('iceCandidate', (candidate: RTCIceCandidate) => {
      console.log('Received ICE candidate');
      this.peerConnection!.addIceCandidate(candidate);
    });

    this.signalingClient.on('close', () => {
      console.log('Signaling client disconnected');
    });

    this.signalingClient.on('error', (error: Error) => {
      console.error('Signaling client error:', error);
    });
  }

  private setupPeerConnectionHandlers() {
    if (!this.peerConnection) return;

    this.peerConnection.onicecandidate = (event) => {
      if (event.candidate) {
        console.log('Sending ICE candidate');
        this.signalingClient!.sendIceCandidate(event.candidate);
      }
    };

    this.peerConnection.oniceconnectionstatechange = () => {
      console.log('ICE connection state:', this.peerConnection!.iceConnectionState);
    };

    this.peerConnection.ontrack = (event) => {
      console.log('Received remote track:', event.track.kind);
    };
  }

  private setupDataChannelHandlers() {
    if (!this.dataChannel) return;

    this.dataChannel.onopen = () => {
      console.log('Data channel opened');
    };

    this.dataChannel.onclose = () => {
      console.log('Data channel closed');
    };

    this.dataChannel.onmessage = (event) => {
      console.log('Data channel message:', event.data);
    };

    this.dataChannel.onerror = (error) => {
      console.error('Data channel error:', error);
    };
  }

  private async getLocalMediaStream(): Promise<MediaStream> {
    try {
      return await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 30 },
          facingMode: 'user',
        },
        audio: false,
      });
    } catch (error) {
      console.error('Failed to get media stream:', error);
      throw error;
    }
  }

  private getChannelARN(): string {
    const accountId = '123456789012'; // Should be from config
    return `arn:aws:kinesisvideo:${this.config.region}:${accountId}:channel/${this.config.channelName}/1234567890123`;
  }

  private async getChannelEndpoint(): Promise<string> {
    // In production, this should fetch from KVS API
    return `https://v-a1b2c3d4.kinesisvideo.${this.config.region}.amazonaws.com`;
  }

  sendMetadata(data: any) {
    if (this.dataChannel?.readyState === 'open') {
      this.dataChannel.send(JSON.stringify(data));
    }
  }

  getLocalStream(): MediaStream | null {
    return this.localStream;
  }

  async disconnect() {
    // Stop local stream tracks
    if (this.localStream) {
      this.localStream.getTracks().forEach((track) => track.stop());
      this.localStream = null;
    }

    // Close data channel
    if (this.dataChannel) {
      this.dataChannel.close();
      this.dataChannel = null;
    }

    // Close peer connection
    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }

    // Close signaling client
    if (this.signalingClient) {
      this.signalingClient.close();
      this.signalingClient = null;
    }
  }
}
