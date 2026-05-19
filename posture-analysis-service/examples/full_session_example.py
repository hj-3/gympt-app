"""
Example: Full session workflow with all P0 features.

This demonstrates:
1. Starting a session
2. Processing frames with MediaPipe
3. Counting reps
4. Logging to DynamoDB
5. Ending session with S3 upload and SQS publish
"""
import asyncio
import numpy as np
import cv2
from pathlib import Path

from app.streaming.frame_processor_v2 import EnhancedFrameProcessor


async def main():
    """Run a complete posture analysis session."""

    # Initialize processor
    processor = EnhancedFrameProcessor()
    print("✓ Frame processor initialized")

    # Start session
    user_id = "demo_user"
    exercise_type = "squat"

    session_id = await processor.start_session(user_id, exercise_type)
    print(f"✓ Session started: {session_id}")

    # Simulate processing video frames
    print("\nProcessing frames...")

    # Create sample frames (in real app, these come from webcam/video)
    sample_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    sample_frame[:, :] = [100, 100, 100]  # Gray background

    # Process 10 frames
    for i in range(10):
        response = await processor.process_frame(
            frame=sample_frame,
            session_id=session_id,
            exercise_type=exercise_type
        )

        if response.status == "success":
            print(f"  Frame {i+1}: Score={response.score:.1f}, "
                  f"Reps={response.rep_count}, Issues={len(response.issues)}")

            if response.feedback:
                print(f"    💬 Feedback: {response.feedback}")
        else:
            print(f"  Frame {i+1}: Error - {response.error}")

        # Small delay to simulate real-time processing
        await asyncio.sleep(0.1)

    # End session
    print("\nEnding session...")
    summary = await processor.end_session(session_id)

    if summary:
        print(f"✓ Session completed successfully")
        print(f"\n📊 Session Summary:")
        print(f"  - Total Reps: {summary.total_reps}")
        print(f"  - Average Score: {summary.avg_score:.2f}/10")
        print(f"  - Duration: {summary.duration_seconds:.1f}s")
        print(f"  - Issues Detected: {summary.issues_detected}")
        print(f"  - Frames Processed: {summary.total_frames_processed}")

        if summary.s3_result_key:
            print(f"  - S3 Results: {summary.s3_result_key}")

        if summary.issues_summary:
            print(f"\n  Issue Breakdown:")
            for issue_type, count in summary.issues_summary.items():
                print(f"    - {issue_type}: {count}")
    else:
        print("⚠ Session ended but no summary available (Redis may not be running)")

    # Cleanup
    await processor.cleanup()
    print("\n✓ Cleanup complete")


if __name__ == "__main__":
    print("=" * 60)
    print("GYMPT Posture Analysis - Full Session Demo")
    print("=" * 60)
    print()

    asyncio.run(main())

    print()
    print("=" * 60)
    print("Demo Complete")
    print("=" * 60)
