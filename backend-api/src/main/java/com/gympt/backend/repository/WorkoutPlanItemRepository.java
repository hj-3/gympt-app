package com.gympt.backend.repository;

import com.gympt.backend.domain.WorkoutPlanItem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface WorkoutPlanItemRepository extends JpaRepository<WorkoutPlanItem, UUID> {
}
