package com.gympt.backend.entity;

import com.gympt.backend.user.User;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "workout_recommendations")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class WorkoutRecommendation {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String recommendation;

    @Column(name = "interaction_id")
    private String interactionId;

    @Column(name = "goal")
    private String goal;

    @Column(name = "fitness_level")
    private String fitnessLevel;

    @Column(name = "days_per_week")
    private Integer daysPerWeek;

    @Column(name = "equipment_available", columnDefinition = "TEXT")
    private String equipmentAvailable;

    @Column(name = "injuries_or_limitations", columnDefinition = "TEXT")
    private String injuriesOrLimitations;

    @Column(name = "model_used")
    private String modelUsed;

    @Column(name = "session_id")
    private String sessionId;

    // Structured KVS-trackable targets as JSON: [{"exercise":"squat","sets":3,"reps":12}]
    @Column(name = "target_exercises", columnDefinition = "TEXT")
    private String targetExercises;

    // Body profile snapshot at time of recommendation
    @Column(name = "height")
    private Double height;

    @Column(name = "weight")
    private Double weight;

    @Column(name = "body_fat")
    private Double bodyFat;

    @Column(name = "muscle_mass")
    private Double muscleMass;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
}
