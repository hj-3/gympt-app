package com.gympt.backend.user;

import com.gympt.backend.common.BaseEntity;
import jakarta.persistence.*;
import lombok.*;

import java.util.UUID;

@Entity
@Table(name = "users",
    indexes = {
        @Index(name = "idx_user_cognito_sub", columnList = "cognito_sub", unique = true),
        @Index(name = "idx_user_email", columnList = "email")
    }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class User extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "cognito_sub", nullable = false, unique = true, length = 255)
    private String cognitoSub;

    @Column(nullable = false, length = 255)
    private String email;

    @Column(nullable = false, length = 100)
    private String name;

    @Column
    private Integer age;

    @Enumerated(EnumType.STRING)
    @Column(length = 10)
    private Gender gender;

    @Enumerated(EnumType.STRING)
    @Column(name = "fitness_level", length = 20)
    private FitnessLevel fitnessLevel;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private Role role = Role.USER;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private UserStatus status = UserStatus.ACTIVE;

    @Column(name = "last_login_at")
    private java.time.Instant lastLoginAt;

    public enum Gender {
        MALE, FEMALE, OTHER
    }

    public enum FitnessLevel {
        BEGINNER, INTERMEDIATE, ADVANCED, EXPERT
    }

    public enum Role {
        USER, TRAINER, ADMIN
    }

    public enum UserStatus {
        ACTIVE, SUSPENDED, DELETED
    }
}
