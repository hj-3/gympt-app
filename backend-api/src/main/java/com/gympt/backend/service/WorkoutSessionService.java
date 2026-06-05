package com.gympt.backend.service;

import com.gympt.backend.domain.WorkoutPlan;
import com.gympt.backend.domain.WorkoutSession;
import com.gympt.backend.dto.EndWorkoutSessionRequest;
import com.gympt.backend.dto.WorkoutSessionRequest;
import com.gympt.backend.dto.WorkoutSessionResponse;
import com.gympt.backend.exception.ResourceNotFoundException;
import com.gympt.backend.exception.ValidationException;
import com.gympt.backend.repository.WorkoutPlanRepository;
import com.gympt.backend.repository.WorkoutSessionRepository;
import com.gympt.backend.user.User;
import com.gympt.backend.user.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import java.time.Instant;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class WorkoutSessionService {

    private final WorkoutSessionRepository workoutSessionRepository;
    private final WorkoutPlanRepository workoutPlanRepository;
    private final UserRepository userRepository;
    private final SqsService sqsService;

    @Transactional
    public WorkoutSessionResponse startSession(UUID userId, WorkoutSessionRequest request) {
        log.info("Starting workout session for user: {}", userId);

        User user = userRepository.findById(userId)
            .orElseThrow(() -> new ResourceNotFoundException("User", "id", userId));

        WorkoutPlan workoutPlan = null;
        if (request.getWorkoutPlanId() != null) {
            workoutPlan = workoutPlanRepository.findById(request.getWorkoutPlanId())
                .orElseThrow(() -> new ResourceNotFoundException("WorkoutPlan", "id", request.getWorkoutPlanId()));

            // Verify workout plan belongs to user
            if (!workoutPlan.getUser().getId().equals(userId)) {
                throw new ValidationException("Workout plan does not belong to user");
            }
        }

        WorkoutSession session = WorkoutSession.builder()
            .user(user)
            .workoutPlan(workoutPlan)
            .startTime(Instant.now())
            .status(WorkoutSession.SessionStatus.IN_PROGRESS)
            .notes(request.getNotes())
            .build();

        session = workoutSessionRepository.save(session);
        log.info("Workout session started with id: {}", session.getId());

        return WorkoutSessionResponse.from(session);
    }

    @Transactional
    public WorkoutSessionResponse endSession(UUID sessionId, EndWorkoutSessionRequest request) {
        log.info("Ending workout session: {}", sessionId);

        WorkoutSession session = workoutSessionRepository.findById(sessionId)
            .orElseThrow(() -> new ResourceNotFoundException("WorkoutSession", "id", sessionId));

        if (session.getStatus() != WorkoutSession.SessionStatus.IN_PROGRESS) {
            throw new ValidationException("Workout session is not in progress");
        }

        session.setEndTime(Instant.now());
        session.setStatus(WorkoutSession.SessionStatus.COMPLETED);

        if (request.getTotalDuration() != null) {
            session.setTotalDuration(request.getTotalDuration());
        }
        if (request.getCaloriesBurned() != null) {
            session.setCaloriesBurned(request.getCaloriesBurned());
        }
        if (request.getNotes() != null) {
            session.setNotes(request.getNotes());
        }

        session = workoutSessionRepository.save(session);
        log.info("Workout session ended: {}", sessionId);

        final UUID finalSessionId = session.getId();
        final UUID finalUserId = session.getUser().getId();
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCommit() {
                sqsService.publishRecommendationUpdateEvent(finalUserId, finalSessionId);
                sqsService.publishWorkoutCompletedNotification(finalUserId, finalSessionId);
            }
        });

        return WorkoutSessionResponse.from(session);
    }

    @Transactional(readOnly = true)
    public List<WorkoutSessionResponse> getUserSessions(UUID userId) {
        log.info("Getting workout sessions for user: {}", userId);

        List<WorkoutSession> sessions = workoutSessionRepository.findByUserIdOrderByStartTimeDesc(userId);

        return sessions.stream()
            .map(WorkoutSessionResponse::from)
            .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public WorkoutSessionResponse getSession(UUID sessionId) {
        log.info("Getting workout session: {}", sessionId);

        WorkoutSession session = workoutSessionRepository.findById(sessionId)
            .orElseThrow(() -> new ResourceNotFoundException("WorkoutSession", "id", sessionId));

        return WorkoutSessionResponse.from(session);
    }

    @Transactional
    public WorkoutSessionResponse cancelSession(UUID sessionId) {
        log.info("Cancelling workout session: {}", sessionId);

        WorkoutSession session = workoutSessionRepository.findById(sessionId)
            .orElseThrow(() -> new ResourceNotFoundException("WorkoutSession", "id", sessionId));

        if (session.getStatus() != WorkoutSession.SessionStatus.IN_PROGRESS) {
            throw new ValidationException("Only in-progress sessions can be cancelled");
        }

        session.setStatus(WorkoutSession.SessionStatus.CANCELLED);
        session.setEndTime(Instant.now());
        session = workoutSessionRepository.save(session);

        log.info("Workout session cancelled: {}", sessionId);
        return WorkoutSessionResponse.from(session);
    }
}
