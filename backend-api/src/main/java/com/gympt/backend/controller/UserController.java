package com.gympt.backend.controller;

import com.gympt.backend.dto.UserProfileRequest;
import com.gympt.backend.dto.UserProfileResponse;
import com.gympt.backend.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/users")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Users", description = "User profile management endpoints")
@SecurityRequirement(name = "bearerAuth")
public class UserController {

    private final UserService userService;

    @GetMapping("/{userId}")
    @PreAuthorize("hasRole('USER') and #userId.toString() == authentication.name")
    @Operation(summary = "Get user profile")
    public ResponseEntity<UserProfileResponse> getProfile(@PathVariable UUID userId) {
        log.info("GET /api/v1/users/{} - userId: {}", userId, userId);
        UserProfileResponse response = userService.getProfile(userId);
        return ResponseEntity.ok(response);
    }

    @PutMapping("/{userId}")
    @PreAuthorize("hasRole('USER') and #userId.toString() == authentication.name")
    @Operation(summary = "Update user profile")
    public ResponseEntity<UserProfileResponse> updateProfile(
            @PathVariable UUID userId,
            @Valid @RequestBody UserProfileRequest request
    ) {
        log.info("PUT /api/v1/users/{} - userId: {}", userId, userId);
        UserProfileResponse response = userService.updateProfile(userId, request);
        return ResponseEntity.ok(response);
    }

    @DeleteMapping("/{userId}")
    @PreAuthorize("hasRole('USER') and #userId.toString() == authentication.name")
    @Operation(summary = "Delete user account")
    public ResponseEntity<Void> deleteAccount(@PathVariable UUID userId) {
        log.info("DELETE /api/v1/users/{} - userId: {}", userId, userId);
        userService.deleteAccount(userId);
        return ResponseEntity.noContent().build();
    }
}
