package com.gympt.backend.repository;

import com.gympt.backend.domain.WorkoutSession;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;

@Repository
public interface WorkoutSessionRepository extends JpaRepository<WorkoutSession, UUID> {

    List<WorkoutSession> findByUserIdOrderByStartTimeDesc(UUID userId);

    List<WorkoutSession> findByUserIdAndStatus(UUID userId, WorkoutSession.SessionStatus status);

    @Query("SELECT ws FROM WorkoutSession ws WHERE ws.user.id = :userId " +
           "AND ws.startTime BETWEEN :startDate AND :endDate")
    List<WorkoutSession> findByUserIdAndDateRange(
        UUID userId,
        Instant startDate,
        Instant endDate
    );

    @Query("SELECT ws FROM WorkoutSession ws WHERE ws.user.id = :userId " +
           "AND ws.startTime > :startTime ORDER BY ws.startTime DESC")
    List<WorkoutSession> findByUserIdAndStartTimeAfter(UUID userId, LocalDateTime startTime);
}
