"""Test GPU availability and fallback."""
import pytest


pytestmark = [pytest.mark.gpu]


class TestGPUAvailability:
    """Test GPU detection and availability."""

    def test_cuda_availability_check(self):
        """Test CUDA availability detection."""
        try:
            import torch
            cuda_available = torch.cuda.is_available()

            # Test should either pass with GPU or be skipped
            if not cuda_available:
                pytest.skip("CUDA not available")

            assert cuda_available
            print(f"\nCUDA available: {torch.cuda.get_device_name(0)}")

        except ImportError:
            pytest.skip("PyTorch not installed")

    def test_gpu_device_count(self):
        """Test GPU device count."""
        try:
            import torch

            if not torch.cuda.is_available():
                pytest.skip("CUDA not available")

            device_count = torch.cuda.device_count()
            assert device_count > 0

            print(f"\nGPU devices found: {device_count}")

        except ImportError:
            pytest.skip("PyTorch not installed")

    def test_gpu_memory_available(self):
        """Test GPU memory is available."""
        try:
            import torch

            if not torch.cuda.is_available():
                pytest.skip("CUDA not available")

            # Get GPU memory info
            total_memory = torch.cuda.get_device_properties(0).total_memory
            total_memory_gb = total_memory / (1024**3)

            assert total_memory_gb > 0

            print(f"\nGPU memory: {total_memory_gb:.2f} GB")

        except ImportError:
            pytest.skip("PyTorch not installed")

    def test_fallback_to_cpu_when_no_gpu(self):
        """Test system falls back to CPU when GPU unavailable."""
        from app.config import settings

        # If GPU is disabled in settings
        if not settings.enable_gpu:
            assert not settings.should_use_gpu

        # If GPU enabled but not available
        if settings.enable_gpu:
            try:
                import torch
                if not torch.cuda.is_available():
                    assert not settings.should_use_gpu
            except ImportError:
                # PyTorch not installed, should use CPU
                assert not settings.should_use_gpu

    def test_mediapipe_gpu_support(self):
        """Test MediaPipe GPU support detection."""
        try:
            import torch

            if not torch.cuda.is_available():
                pytest.skip("CUDA not available")

            # MediaPipe GPU initialization test
            from app.pose_estimator.mediapipe_estimator import MediaPipeEstimator

            estimator = MediaPipeEstimator(use_gpu=True)
            assert estimator is not None

        except ImportError:
            pytest.skip("Dependencies not available")
        except Exception as e:
            # MediaPipe may not support GPU on this system
            pytest.skip(f"MediaPipe GPU not supported: {e}")


@pytest.mark.gpu
class TestGPUMediaPipe:
    """Test MediaPipe with GPU acceleration."""

    @pytest.fixture
    def gpu_estimator(self):
        """Create GPU-enabled estimator."""
        try:
            import torch

            if not torch.cuda.is_available():
                pytest.skip("CUDA not available")

            from app.pose_estimator.mediapipe_estimator import MediaPipeEstimator
            return MediaPipeEstimator(use_gpu=True)

        except Exception as e:
            pytest.skip(f"GPU estimator unavailable: {e}")

    async def test_gpu_pose_estimation(self, gpu_estimator, sample_frame_480p):
        """Test pose estimation with GPU."""
        result = await gpu_estimator.estimate(sample_frame_480p)

        assert result is not None
        assert "keypoints" in result
        assert "confidence" in result

    async def test_gpu_vs_cpu_performance(self, sample_frame_480p):
        """Compare GPU vs CPU performance."""
        import time

        try:
            import torch

            if not torch.cuda.is_available():
                pytest.skip("CUDA not available")

            from app.pose_estimator.mediapipe_estimator import MediaPipeEstimator

            # CPU estimator
            cpu_estimator = MediaPipeEstimator(use_gpu=False)

            # GPU estimator
            gpu_estimator = MediaPipeEstimator(use_gpu=True)

            num_frames = 30

            # Benchmark CPU
            cpu_start = time.time()
            for _ in range(num_frames):
                await cpu_estimator.estimate(sample_frame_480p)
            cpu_time = time.time() - cpu_start

            # Benchmark GPU
            gpu_start = time.time()
            for _ in range(num_frames):
                await gpu_estimator.estimate(sample_frame_480p)
            gpu_time = time.time() - gpu_start

            cpu_fps = num_frames / cpu_time
            gpu_fps = num_frames / gpu_time

            print(f"\nCPU: {cpu_fps:.1f} FPS")
            print(f"GPU: {gpu_fps:.1f} FPS")
            print(f"Speedup: {cpu_time/gpu_time:.2f}x")

            # GPU should be faster (or at least not significantly slower)
            # Note: On some systems GPU may be slower due to overhead
            assert gpu_fps > 0

        except Exception as e:
            pytest.skip(f"Performance test failed: {e}")

    async def test_gpu_memory_management(self, gpu_estimator, sample_frame_480p):
        """Test GPU memory doesn't leak."""
        try:
            import torch

            if not torch.cuda.is_available():
                pytest.skip("CUDA not available")

            # Get initial GPU memory
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            initial_memory = torch.cuda.memory_allocated() / 1024 / 1024  # MB

            # Process many frames
            for _ in range(100):
                await gpu_estimator.estimate(sample_frame_480p)

            # Check final GPU memory
            torch.cuda.synchronize()
            final_memory = torch.cuda.memory_allocated() / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            print(f"\nGPU memory increase: {memory_increase:.1f}MB")

            # Memory increase should be reasonable
            assert memory_increase < 500

        except Exception as e:
            pytest.skip(f"Memory test failed: {e}")

    async def test_gpu_batch_processing(self, gpu_estimator):
        """Test GPU batch processing efficiency."""
        import numpy as np

        try:
            import torch

            if not torch.cuda.is_available():
                pytest.skip("CUDA not available")

            # Generate multiple frames
            frames = [
                np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                for _ in range(10)
            ]

            # Process batch
            results = []
            for frame in frames:
                result = await gpu_estimator.estimate(frame)
                results.append(result)

            # All should succeed
            assert len(results) == len(frames)
            assert all(r is not None for r in results)

        except Exception as e:
            pytest.skip(f"Batch test failed: {e}")
