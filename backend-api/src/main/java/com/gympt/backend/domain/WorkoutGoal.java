package com.gympt.backend.domain;

import com.gympt.backend.common.BaseEntity;
import com.gympt.backend.user.User;
import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(name = "workout_goals",
    indexes = {
        @Index(name = "idx_workout_goal_user", columnList = "user_id"),
        @Index(name = "idx_workout_goal_status", columnList = "status")
    }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class WorkoutGoal extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Enumerated(EnumType.STRING)
    @Column(name = "goal_type", nullable = false, length = 30)
    private GoalType goalType;

    @Column(name = "target_value", precision = 10, scale = 2)
    private BigDecimal targetValue;

    @Column(name = "target_date")
    private LocalDate targetDate;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private GoalStatus status = GoalStatus.ACTIVE;

    @Column(length = 1000)
    private String description;

    public enum GoalType {
        WEIGHT_LOSS,
        MUSCLE_GAIN,
        POSTURE_CORRECTION,
        FLEXIBILITY,
        ENDURANCE,
        STRENGTH
    }

    public enum GoalStatus {
        ACTIVE,
        COMPLETED,
        ABANDONED,
        ON_HOLD
    }
}
