/**
 * AWS Kinesis Video Streams WebRTC Client
 */
import { SignalingClient, Role } from 'amazon-kinesis-video-streams-webrtc';
import { KinesisVideo, KinesisVideoSignalingChannels } from '@aws-sdk/client-kinesis-video';
import { KinesisVideoSignaling } from '@aws-sdk/client-kinesis-video-signaling';

interface KVSConfig {
  region: string;
  channelName: string;
  clientId: string;
  role: 'MASTER' | 'VIEWER';
  credentials: {
    accessKeyId: string;
    secretAccessKey: string;
    sessionToken?: string;
  };
}

interface IceServer {
  urls: string | string[];
  username?: string;
  credential?: string;
}

export class KVSWebRTCClient {
  private signalingClient: SignalingClient | null = null;
  private peerConnection: RTCPeerConnection | null = null;
  private localStream: MediaStream | null = null;
  private remoteStream: MediaStream | null = null;
  private dataChannel: RTCDataChannel | null = null;
  private config: KVSConfig;

  constructor(config: KVSConfig) {
    this.config = config;
  }

  /**
   * Initialize KVS WebRTC connection
   */
  async connect(localStream: MediaStream): Promise<void> {
    this.localStream = localStream;

    try {
      // 1. Get signaling channel endpoints
      const endpoints = await this.getSignalingChannelEndpoints();

      // 2. Get ICE server configuration
      const iceServers = await this.getIceServerConfig();

      // 3. Create peer connection
      this.peerConnection = new RTCPeerConnection({
        iceServers,
        iceTransportPolicy: 'all',
      });

      // 4. Add local stream tracks
      localStream.getTracks().forEach(track => {
        if (this.peerConnection && this.localStream) {
          this.peerConnection.addTrack(track, this.localStream);
        }
      });

      // 5. Set up peer connection event handlers
      this.setupPeerConnectionHandlers();

      // 6. Create signaling client
      this.signalingClient = new SignalingClient({
        channelARN: await this.getChannelARN(),
        channelEndpoint: endpoints.HTTPS,
        role: this.config.role === 'MASTER' ? Role.MASTER : Role.VIEWER,
        region: this.config.region,
        credentials: {
          accessKeyId: this.config.credentials.accessKeyId,
          secretAccessKey: this.config.credentials.secretAccessKey,
          sessionToken: this.config.credentials.sessionToken,
        },
        clientId: this.config.clientId,
      });

      // 7. Set up signaling client event handlers
      this.setupSignalingHandlers();

      // 8. Open signaling connection
      await this.signalingClient.open();

      console.log('KVS WebRTC connection established');
    } catch (error) {
      console.error('Failed to connect to KVS WebRTC:', error);
      throw error;
    }
  }

  /**
   * Disconnect from KVS WebRTC
   */
  async disconnect(): Promise<void> {
    if (this.dataChannel) {
      this.dataChannel.close();
      this.dataChannel = null;
    }

    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }

    if (this.signalingClient) {
      this.signalingClient.close();
      this.signalingClient = null;
    }

    if (this.localStream) {
      this.localStream.getTracks().forEach(track => track.stop());
      this.localStream = null;
    }

    this.remoteStream = null;

    console.log('KVS WebRTC disconnected');
  }

  /**
   * Get signaling channel ARN
   */
  private async getChannelARN(): Promise<string> {
    const kinesisVideoClient = new KinesisVideo({
      region: this.config.region,
      credentials: this.config.credentials,
    });

    const response = await kinesisVideoClient.describeSignalingChannel({
      ChannelName: this.config.channelName,
    });

    if (!response.ChannelInfo?.ChannelARN) {
      throw new Error('Channel ARN not found');
    }

    return response.ChannelInfo.ChannelARN;
  }

  /**
   * Get signaling channel endpoints
   */
  private async getSignalingChannelEndpoints(): Promise<{ HTTPS: string; WSS: string }> {
    const kinesisVideoClient = new KinesisVideo({
      region: this.config.region,
      credentials: this.config.credentials,
    });

    const channelARN = await this.getChannelARN();

    const response = await kinesisVideoClient.getSignalingChannelEndpoint({
      ChannelARN: channelARN,
      SingleMasterChannelEndpointConfiguration: {
        Protocols: ['WSS', 'HTTPS'],
        Role: this.config.role,
      },
    });

    const endpoints: { HTTPS: string; WSS: string } = { HTTPS: '', WSS: '' };

    response.ResourceEndpointList?.forEach((endpoint: any) => {
      if (endpoint.Protocol === 'HTTPS' && endpoint.ResourceEndpoint) {
        endpoints.HTTPS = endpoint.ResourceEndpoint;
      } else if (endpoint.Protocol === 'WSS' && endpoint.ResourceEndpoint) {
        endpoints.WSS = endpoint.ResourceEndpoint;
      }
    });

    if (!endpoints.HTTPS || !endpoints.WSS) {
      throw new Error('Failed to get signaling channel endpoints');
    }

    return endpoints;
  }

  /**
   * Get ICE server configuration
   */
  private async getIceServerConfig(): Promise<IceServer[]> {
    const kinesisVideoSignalingClient = new KinesisVideoSignaling({
      region: this.config.region,
      credentials: this.config.credentials,
      endpoint: (await this.getSignalingChannelEndpoints()).HTTPS,
    });

    const channelARN = await this.getChannelARN();

    const response = await kinesisVideoSignalingClient.getIceServerConfig({
      ChannelARN: channelARN,
    });

    const iceServers: IceServer[] = [];

    response.IceServerList?.forEach((iceServer: any) => {
      iceServers.push({
        urls: iceServer.Uris || [],
        username: iceServer.Username,
        credential: iceServer.Password,
      });
    });

    // Add Google STUN server as fallback
    iceServers.push({
      urls: 'stun:stun.l.google.com:19302',
    });

    return iceServers;
  }

  /**
   * Set up peer connection event handlers
   */
  private setupPeerConnectionHandlers(): void {
    if (!this.peerConnection) return;

    // ICE candidate handler
    this.peerConnection.onicecandidate = (event) => {
      if (event.candidate && this.signalingClient) {
        this.signalingClient.sendIceCandidate(event.candidate);
      }
    };

    // Track handler for remote stream
    this.peerConnection.ontrack = (event) => {
      console.log('Received remote track:', event.track.kind);
      if (!this.remoteStream) {
        this.remoteStream = new MediaStream();
      }
      this.remoteStream.addTrack(event.track);
    };

    // Connection state handler
    this.peerConnection.onconnectionstatechange = () => {
      console.log('Peer connection state:', this.peerConnection?.connectionState);
    };

    // ICE connection state handler
    this.peerConnection.oniceconnectionstatechange = () => {
      console.log('ICE connection state:', this.peerConnection?.iceConnectionState);
    };

    // Data channel handler
    if (this.config.role === 'MASTER') {
      this.dataChannel = this.peerConnection.createDataChannel('kvsDataChannel');
      this.setupDataChannelHandlers(this.dataChannel);
    } else {
      this.peerConnection.ondatachannel = (event) => {
        this.dataChannel = event.channel;
        this.setupDataChannelHandlers(this.dataChannel);
      };
    }
  }

  /**
   * Set up data channel event handlers
   */
  private setupDataChannelHandlers(dataChannel: RTCDataChannel): void {
    dataChannel.onopen = () => {
      console.log('Data channel opened');
    };

    dataChannel.onmessage = (event) => {
      console.log('Data channel message:', event.data);
    };

    dataChannel.onerror = (error) => {
      console.error('Data channel error:', error);
    };

    dataChannel.onclose = () => {
      console.log('Data channel closed');
    };
  }

  /**
   * Set up signaling client event handlers
   */
  private setupSignalingHandlers(): void {
    if (!this.signalingClient || !this.peerConnection) return;

    const pc = this.peerConnection;

    // Handle SDP offer (for VIEWER role)
    this.signalingClient.on('sdpOffer', async (offer: RTCSessionDescriptionInit) => {
      console.log('Received SDP offer');
      await pc.setRemoteDescription(offer);
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);

      if (this.signalingClient && answer) {
        this.signalingClient.sendSdpAnswer(answer as any);
      }
    });

    // Handle SDP answer (for MASTER role)
    this.signalingClient.on('sdpAnswer', async (answer: RTCSessionDescriptionInit) => {
      console.log('Received SDP answer');
      await pc.setRemoteDescription(answer);
    });

    // Handle ICE candidate
    this.signalingClient.on('iceCandidate', async (candidate: RTCIceCandidateInit) => {
      console.log('Received ICE candidate');
      await pc.addIceCandidate(candidate);
    });

    // Handle signaling client errors
    this.signalingClient.on('error', (error: Error) => {
      console.error('Signaling client error:', error);
    });

    // Handle signaling client close
    this.signalingClient.on('close', () => {
      console.log('Signaling client closed');
    });

    // If MASTER, create and send offer
    if (this.config.role === 'MASTER') {
      this.signalingClient.on('open', async () => {
        console.log('Signaling client opened as MASTER');
        const offer = await pc.createOffer({
          offerToReceiveAudio: true,
          offerToReceiveVideo: true,
        });
        await pc.setLocalDescription(offer);

        if (this.signalingClient && offer) {
          this.signalingClient.sendSdpOffer(offer as any);
        }
      });
    } else {
      this.signalingClient.on('open', () => {
        console.log('Signaling client opened as VIEWER');
      });
    }
  }

  /**
   * Send data through data channel
   */
  sendData(data: string): void {
    if (this.dataChannel && this.dataChannel.readyState === 'open') {
      this.dataChannel.send(data);
    } else {
      console.warn('Data channel not open');
    }
  }

  /**
   * Get remote stream
   */
  getRemoteStream(): MediaStream | null {
    return this.remoteStream;
  }

  /**
   * Get connection state
   */
  getConnectionState(): RTCPeerConnectionState | null {
    return this.peerConnection?.connectionState || null;
  }
}

export default KVSWebRTCClient;
