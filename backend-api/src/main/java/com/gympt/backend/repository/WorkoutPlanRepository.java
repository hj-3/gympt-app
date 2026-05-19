package com.gympt.backend.repository;

import com.gympt.backend.domain.WorkoutPlan;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface WorkoutPlanRepository extends JpaRepository<WorkoutPlan, UUID> {

    List<WorkoutPlan> findByUserIdOrderByCreatedAtDesc(UUID userId);

    List<WorkoutPlan> findByUserIdAndStatus(UUID userId, WorkoutPlan.PlanStatus status);

    @Query("SELECT wp FROM WorkoutPlan wp LEFT JOIN FETCH wp.items WHERE wp.id = :id")
    WorkoutPlan findByIdWithItems(UUID id);
}
