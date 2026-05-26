package com.gympt.backend.repository;

import com.gympt.backend.entity.WorkoutRecommendation;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface WorkoutRecommendationRepository extends JpaRepository<WorkoutRecommendation, UUID> {

    @Query("SELECT wr FROM WorkoutRecommendation wr WHERE wr.user.id = :userId ORDER BY wr.createdAt DESC")
    List<WorkoutRecommendation> findByUser_IdOrderByCreatedAtDesc(@Param("userId") UUID userId, Pageable pageable);

    @Query("SELECT wr FROM WorkoutRecommendation wr WHERE wr.user.id = :userId ORDER BY wr.createdAt DESC")
    List<WorkoutRecommendation> findByUser_IdOrderByCreatedAtDesc(@Param("userId") UUID userId);
}
