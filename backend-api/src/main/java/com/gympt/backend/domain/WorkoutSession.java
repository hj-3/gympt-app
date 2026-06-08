package com.gympt.backend.domain;

import com.gympt.backend.common.BaseEntity;
import com.gympt.backend.user.User;
import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "workout_sessions",
    indexes = {
        @Index(name = "idx_workout_session_user", columnList = "user_id"),
        @Index(name = "idx_workout_session_plan", columnList = "workout_plan_id"),
        @Index(name = "idx_workout_session_start_time", columnList = "start_time")
    }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class WorkoutSession extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "workout_plan_id")
    private WorkoutPlan workoutPlan;

    @Column(name = "start_time", nullable = false)
    private Instant startTime;

    @Column(name = "end_time")
    private Instant endTime;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private SessionStatus status = SessionStatus.IN_PROGRESS;

    @Column(name = "total_duration")
    private Integer totalDuration; // in seconds

    @Column(name = "calories_burned", precision = 10, scale = 2)
    private BigDecimal caloriesBurned;

    @Column(length = 2000)
    private String notes;

    @Column(name = "exercise_type", length = 50)
    private String exerciseType;

    @Column(name = "exercise_name", length = 100)
    private String exerciseName;

    @Column(name = "total_reps")
    private Integer totalReps;

    @Column(name = "avg_posture_score", precision = 5, scale = 2)
    private BigDecimal avgPostureScore;

    @Column(name = "recommendation_id")
    private UUID recommendationId;

    public enum SessionStatus {
        IN_PROGRESS,
        COMPLETED,
        CANCELLED,
        PAUSED
    }
}
