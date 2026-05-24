"""KVS Stream Consumer for processing video frames."""
import asyncio
import logging
import base64
from typing import Optional, Callable
import cv2
import numpy as np
import boto3
from botocore.exceptions import ClientError

from ..config.settings import settings

logger = logging.getLogger(__name__)


class KVSStreamConsumer:
    """Consumer for AWS Kinesis Video Streams."""

    def __init__(self, channel_name: str, session_id: str):
        """
        Initialize KVS stream consumer.

        Args:
            channel_name: KVS signaling channel name
            session_id: Workout session ID
        """
        self.channel_name = channel_name
        self.session_id = session_id
        self.kvs_client = boto3.client('kinesisvideo', region_name=settings.aws_region)
        self.is_consuming = False
        self.frame_counter = 0

    async def start_consuming(
        self,
        frame_callback: Callable[[np.ndarray, int], None]
    ) -> None:
        """
        Start consuming video frames from KVS stream.

        Args:
            frame_callback: Async callback function to process frames
        """
        self.is_consuming = True
        logger.info(f"Starting KVS stream consumer for channel: {self.channel_name}")

        try:
            # Get stream ARN
            stream_arn = await self._get_stream_arn()

            # Get data endpoint
            data_endpoint = await self._get_data_endpoint(stream_arn)

            # Get media stream
            await self._consume_media_stream(data_endpoint, stream_arn, frame_callback)

        except Exception as e:
            logger.error(f"Error consuming KVS stream: {e}")
            raise
        finally:
            self.is_consuming = False

    async def stop_consuming(self) -> None:
        """Stop consuming video frames."""
        self.is_consuming = False
        logger.info(f"Stopped KVS stream consumer for channel: {self.channel_name}")

    async def _get_stream_arn(self) -> str:
        """Get KVS stream ARN from channel name."""
        try:
            response = self.kvs_client.describe_signaling_channel(
                ChannelName=self.channel_name
            )
            return response['ChannelInfo']['ChannelARN']
        except ClientError as e:
            logger.error(f"Failed to get stream ARN: {e}")
            raise

    async def _get_data_endpoint(self, stream_arn: str) -> str:
        """Get data endpoint for the stream."""
        try:
            response = self.kvs_client.get_data_endpoint(
                StreamARN=stream_arn,
                APIName='GET_MEDIA'
            )
            return response['DataEndpoint']
        except ClientError as e:
            logger.error(f"Failed to get data endpoint: {e}")
            raise

    async def _consume_media_stream(
        self,
        data_endpoint: str,
        stream_arn: str,
        frame_callback: Callable
    ) -> None:
        """
        Consume media stream and process frames.

        Args:
            data_endpoint: KVS data endpoint
            stream_arn: Stream ARN
            frame_callback: Callback to process frames
        """
        kvs_media_client = boto3.client(
            'kinesis-video-media',
            endpoint_url=data_endpoint,
            region_name=settings.aws_region
        )

        try:
            response = kvs_media_client.get_media(
                StreamARN=stream_arn,
                StartSelector={'StartSelectorType': 'NOW'}
            )

            # Process streaming payload
            stream = response['Payload']

            while self.is_consuming:
                try:
                    # Read chunk from stream
                    chunk = await asyncio.to_thread(stream.read, 65536)
                    if not chunk:
                        break

                    # Decode frame from chunk
                    frame = self._decode_frame(chunk)

                    if frame is not None:
                        self.frame_counter += 1

                        # Sample frames based on sample rate
                        if self.frame_counter % settings.frame_sample_rate == 0:
                            await frame_callback(frame, self.frame_counter)

                except Exception as e:
                    logger.error(f"Error processing frame: {e}")
                    await asyncio.sleep(0.1)

        except ClientError as e:
            logger.error(f"Failed to get media stream: {e}")
            raise
        finally:
            if 'stream' in locals():
                stream.close()

    def _decode_frame(self, chunk: bytes) -> Optional[np.ndarray]:
        """
        Decode video frame from chunk.

        Args:
            chunk: Raw video data chunk

        Returns:
            Decoded frame as numpy array, or None if decoding failed
        """
        try:
            # Decode JPEG/H264 frame
            nparr = np.frombuffer(chunk, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return frame
        except Exception as e:
            logger.debug(f"Failed to decode frame: {e}")
            return None


class KVSWebRTCConsumer:
    """Consumer for KVS WebRTC streams."""

    def __init__(self, channel_name: str, session_id: str):
        """
        Initialize WebRTC consumer.

        Args:
            channel_name: Signaling channel name
            session_id: Session identifier
        """
        self.channel_name = channel_name
        self.session_id = session_id
        self.kvs_client = boto3.client('kinesisvideo', region_name=settings.aws_region)
        self.kvs_signaling_client = None
        self.is_consuming = False

    async def start_consuming(
        self,
        frame_callback: Callable[[np.ndarray, int], None]
    ) -> None:
        """
        Start consuming WebRTC stream.

        Args:
            frame_callback: Callback to process frames
        """
        self.is_consuming = True
        logger.info(f"Starting WebRTC consumer for channel: {self.channel_name}")

        try:
            # Get signaling channel endpoints
            endpoints = await self._get_signaling_endpoints()

            # Get ICE server config
            ice_servers = await self._get_ice_server_config(endpoints['HTTPS'])

            # Connect as VIEWER
            # Note: Actual WebRTC connection requires WebRTC library
            # This is a placeholder for the WebRTC connection logic
            logger.info(f"WebRTC endpoints: {endpoints}")
            logger.info(f"ICE servers configured: {len(ice_servers)}")

            # TODO: Implement actual WebRTC peer connection
            # using aiortc or similar library for Python

        except Exception as e:
            logger.error(f"Error in WebRTC consumer: {e}")
            raise
        finally:
            self.is_consuming = False

    async def stop_consuming(self) -> None:
        """Stop consuming WebRTC stream."""
        self.is_consuming = False
        logger.info("Stopped WebRTC consumer")

    async def _get_signaling_endpoints(self) -> dict:
        """Get signaling channel endpoints."""
        try:
            # Get channel ARN
            response = self.kvs_client.describe_signaling_channel(
                ChannelName=self.channel_name
            )
            channel_arn = response['ChannelInfo']['ChannelARN']

            # Get endpoints
            response = self.kvs_client.get_signaling_channel_endpoint(
                ChannelARN=channel_arn,
                SingleMasterChannelEndpointConfiguration={
                    'Protocols': ['WSS', 'HTTPS'],
                    'Role': 'VIEWER'
                }
            )

            endpoints = {}
            for endpoint in response['ResourceEndpointList']:
                protocol = endpoint['Protocol']
                endpoints[protocol] = endpoint['ResourceEndpoint']

            return endpoints

        except ClientError as e:
            logger.error(f"Failed to get signaling endpoints: {e}")
            raise

    async def _get_ice_server_config(self, https_endpoint: str) -> list:
        """Get ICE server configuration."""
        try:
            kvs_signaling = boto3.client(
                'kinesis-video-signaling',
                endpoint_url=https_endpoint,
                region_name=settings.aws_region
            )

            response = kvs_signaling.get_ice_server_config(
                ChannelARN=await self._get_channel_arn()
            )

            ice_servers = []
            for server in response.get('IceServerList', []):
                ice_servers.append({
                    'urls': server.get('Uris', []),
                    'username': server.get('Username'),
                    'credential': server.get('Password')
                })

            return ice_servers

        except ClientError as e:
            logger.error(f"Failed to get ICE server config: {e}")
            raise

    async def _get_channel_arn(self) -> str:
        """Get channel ARN."""
        response = self.kvs_client.describe_signaling_channel(
            ChannelName=self.channel_name
        )
        return response['ChannelInfo']['ChannelARN']
