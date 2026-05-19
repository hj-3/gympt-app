package com.gympt.backend.service;

import com.gympt.backend.domain.WorkoutGoal;
import com.gympt.backend.dto.WorkoutGoalRequest;
import com.gympt.backend.dto.WorkoutGoalResponse;
import com.gympt.backend.exception.ResourceNotFoundException;
import com.gympt.backend.repository.WorkoutGoalRepository;
import com.gympt.backend.user.User;
import com.gympt.backend.user.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class WorkoutGoalService {

    private final WorkoutGoalRepository workoutGoalRepository;
    private final UserRepository userRepository;

    @Transactional
    public WorkoutGoalResponse createGoal(UUID userId, WorkoutGoalRequest request) {
        log.info("Creating workout goal for user: {}", userId);

        User user = userRepository.findById(userId)
            .orElseThrow(() -> new ResourceNotFoundException("User", "id", userId));

        WorkoutGoal goal = WorkoutGoal.builder()
            .user(user)
            .goalType(request.getGoalType())
            .targetValue(request.getTargetValue())
            .targetDate(request.getTargetDate())
            .description(request.getDescription())
            .status(WorkoutGoal.GoalStatus.ACTIVE)
            .build();

        goal = workoutGoalRepository.save(goal);
        log.info("Workout goal created with id: {}", goal.getId());

        return WorkoutGoalResponse.from(goal);
    }

    @Transactional(readOnly = true)
    public List<WorkoutGoalResponse> getGoals(UUID userId) {
        log.info("Getting workout goals for user: {}", userId);

        List<WorkoutGoal> goals = workoutGoalRepository.findByUserIdOrderByCreatedAtDesc(userId);

        return goals.stream()
            .map(WorkoutGoalResponse::from)
            .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public WorkoutGoalResponse getGoal(UUID goalId) {
        log.info("Getting workout goal: {}", goalId);

        WorkoutGoal goal = workoutGoalRepository.findById(goalId)
            .orElseThrow(() -> new ResourceNotFoundException("WorkoutGoal", "id", goalId));

        return WorkoutGoalResponse.from(goal);
    }

    @Transactional
    public WorkoutGoalResponse updateGoalStatus(UUID goalId, WorkoutGoal.GoalStatus status) {
        log.info("Updating workout goal status: {} to {}", goalId, status);

        WorkoutGoal goal = workoutGoalRepository.findById(goalId)
            .orElseThrow(() -> new ResourceNotFoundException("WorkoutGoal", "id", goalId));

        goal.setStatus(status);
        goal = workoutGoalRepository.save(goal);

        log.info("Workout goal status updated: {}", goalId);
        return WorkoutGoalResponse.from(goal);
    }

    @Transactional
    public void deleteGoal(UUID goalId) {
        log.info("Deleting workout goal: {}", goalId);

        WorkoutGoal goal = workoutGoalRepository.findById(goalId)
            .orElseThrow(() -> new ResourceNotFoundException("WorkoutGoal", "id", goalId));

        workoutGoalRepository.delete(goal);
        log.info("Workout goal deleted: {}", goalId);
    }
}
