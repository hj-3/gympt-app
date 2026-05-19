package com.gympt.backend.domain;

import com.gympt.backend.common.BaseEntity;
import com.gympt.backend.user.User;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "workout_plans",
    indexes = {
        @Index(name = "idx_workout_plan_user", columnList = "user_id"),
        @Index(name = "idx_workout_plan_status", columnList = "status")
    }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class WorkoutPlan extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(name = "plan_name", nullable = false, length = 200)
    private String planName;

    @Column(name = "agent_generated", nullable = false)
    @Builder.Default
    private Boolean agentGenerated = false;

    @Column(name = "start_date", nullable = false)
    private LocalDate startDate;

    @Column(name = "end_date")
    private LocalDate endDate;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private PlanStatus status = PlanStatus.ACTIVE;

    @Column(length = 2000)
    private String description;

    @OneToMany(mappedBy = "workoutPlan", cascade = CascadeType.ALL, orphanRemoval = true)
    @Builder.Default
    private List<WorkoutPlanItem> items = new ArrayList<>();

    public enum PlanStatus {
        ACTIVE,
        COMPLETED,
        PAUSED,
        CANCELLED
    }

    // Helper methods
    public void addItem(WorkoutPlanItem item) {
        items.add(item);
        item.setWorkoutPlan(this);
    }

    public void removeItem(WorkoutPlanItem item) {
        items.remove(item);
        item.setWorkoutPlan(null);
    }
}
