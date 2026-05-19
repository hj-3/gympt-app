package com.gympt.backend.dto;

import com.gympt.backend.user.User;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserProfileResponse {

    private UUID id;
    private String email;
    private String name;
    private Integer age;
    private User.Gender gender;
    private User.FitnessLevel fitnessLevel;
    private User.Role role;
    private User.UserStatus status;
    private Instant lastLoginAt;
    private Instant createdAt;
    private Instant updatedAt;

    public static UserProfileResponse from(User user) {
        return UserProfileResponse.builder()
            .id(user.getId())
            .email(user.getEmail())
            .name(user.getName())
            .age(user.getAge())
            .gender(user.getGender())
            .fitnessLevel(user.getFitnessLevel())
            .role(user.getRole())
            .status(user.getStatus())
            .lastLoginAt(user.getLastLoginAt())
            .createdAt(user.getCreatedAt())
            .updatedAt(user.getUpdatedAt())
            .build();
    }
}
