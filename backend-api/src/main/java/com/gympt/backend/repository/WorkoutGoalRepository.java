package com.gympt.backend.repository;

import com.gympt.backend.domain.WorkoutGoal;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface WorkoutGoalRepository extends JpaRepository<WorkoutGoal, UUID> {

    List<WorkoutGoal> findByUserIdOrderByCreatedAtDesc(UUID userId);

    List<WorkoutGoal> findByUserIdAndStatus(UUID userId, WorkoutGoal.GoalStatus status);
}
