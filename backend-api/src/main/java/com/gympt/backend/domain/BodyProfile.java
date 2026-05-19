package com.gympt.backend.domain;

import com.gympt.backend.common.BaseEntity;
import com.gympt.backend.user.User;
import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(name = "body_profiles",
    indexes = {
        @Index(name = "idx_body_profile_user_date", columnList = "user_id, measurement_date")
    }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class BodyProfile extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(nullable = false, precision = 5, scale = 2)
    private BigDecimal height; // in cm

    @Column(nullable = false, precision = 5, scale = 2)
    private BigDecimal weight; // in kg

    @Column(name = "body_fat", precision = 5, scale = 2)
    private BigDecimal bodyFat; // percentage

    @Column(name = "muscle_mass", precision = 5, scale = 2)
    private BigDecimal muscleMass; // in kg

    @Enumerated(EnumType.STRING)
    @Column(name = "posture_type", length = 50)
    private PostureType postureType;

    @Column(name = "measurement_date", nullable = false)
    private LocalDate measurementDate;

    public enum PostureType {
        NORMAL,
        FORWARD_HEAD,
        ROUNDED_SHOULDERS,
        ANTERIOR_PELVIC_TILT,
        POSTERIOR_PELVIC_TILT,
        SCOLIOSIS,
        KYPHOSIS,
        LORDOSIS
    }
}
