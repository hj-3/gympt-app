package com.gympt.backend.domain;

import com.gympt.backend.common.BaseEntity;
import jakarta.persistence.*;
import lombok.*;

import java.util.UUID;

@Entity
@Table(name = "workout_plan_items",
    indexes = {
        @Index(name = "idx_workout_plan_item_plan", columnList = "workout_plan_id"),
        @Index(name = "idx_workout_plan_item_exercise", columnList = "exercise_id")
    }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class WorkoutPlanItem extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "workout_plan_id", nullable = false)
    private WorkoutPlan workoutPlan;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "exercise_id", nullable = false)
    private Exercise exercise;

    @Column(nullable = false)
    private Integer sets;

    @Column(nullable = false)
    private Integer reps;

    @Column
    private Integer duration; // in seconds

    @Column(name = "rest_time")
    private Integer restTime; // in seconds

    @Column(name = "item_order", nullable = false)
    private Integer order;

    @Column(length = 1000)
    private String notes;
}
