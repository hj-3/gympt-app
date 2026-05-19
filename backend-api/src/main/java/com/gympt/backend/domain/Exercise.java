package com.gympt.backend.domain;

import com.gympt.backend.common.BaseEntity;
import jakarta.persistence.*;
import lombok.*;

import java.util.UUID;

@Entity
@Table(name = "exercises",
    indexes = {
        @Index(name = "idx_exercise_category", columnList = "category"),
        @Index(name = "idx_exercise_difficulty", columnList = "difficulty")
    }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Exercise extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, length = 200)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 30)
    private ExerciseCategory category;

    @Column(length = 2000)
    private String description;

    @Column(name = "video_url", length = 500)
    private String videoUrl;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private Difficulty difficulty = Difficulty.BEGINNER;

    @Column(name = "calories_per_minute", precision = 5, scale = 2)
    private java.math.BigDecimal caloriesPerMinute;

    public enum ExerciseCategory {
        CARDIO,
        STRENGTH,
        FLEXIBILITY,
        BALANCE,
        POSTURE_CORRECTION,
        CORE,
        UPPER_BODY,
        LOWER_BODY,
        FULL_BODY
    }

    public enum Difficulty {
        BEGINNER,
        INTERMEDIATE,
        ADVANCED,
        EXPERT
    }
}
