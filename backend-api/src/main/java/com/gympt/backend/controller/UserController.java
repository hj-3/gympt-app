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
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
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

    @GetMapping("/me")
    @Operation(summary = "Get current user profile")
    public ResponseEntity<UserProfileResponse> getCurrentUserProfile(@AuthenticationPrincipal Jwt jwt) {
        UUID userId = UUID.fromString(jwt.getSubject());
        log.info("GET /api/v1/users/me - userId from JWT: {}", userId);
        UserProfileResponse response = userService.getProfileByCognitoSub(jwt.getSubject());
        return ResponseEntity.ok(response);
    }

    @GetMapping("/{userId}")
    @Operation(summary = "Get user profile by ID")
    public ResponseEntity<UserProfileResponse> getProfile(
            @PathVariable UUID userId,
            @AuthenticationPrincipal Jwt jwt
    ) {
        UUID requesterId = UUID.fromString(jwt.getSubject());
        log.info("GET /api/v1/users/{} - requesterId: {}", userId, requesterId);
        UserProfileResponse response = userService.getProfile(userId);
        return ResponseEntity.ok(response);
    }

    @PutMapping("/me")
    @Operation(summary = "Update current user profile")
    public ResponseEntity<UserProfileResponse> updateCurrentUserProfile(
            @AuthenticationPrincipal Jwt jwt,
            @Valid @RequestBody UserProfileRequest request
    ) {
        String cognitoSub = jwt.getSubject();
        log.info("PUT /api/v1/users/me - cognitoSub: {}", cognitoSub);
        UserProfileResponse response = userService.updateProfileByCognitoSub(cognitoSub, request);
        return ResponseEntity.ok(response);
    }

    @DeleteMapping("/me")
    @Operation(summary = "Delete current user account")
    public ResponseEntity<Void> deleteCurrentAccount(@AuthenticationPrincipal Jwt jwt) {
        String cognitoSub = jwt.getSubject();
        log.info("DELETE /api/v1/users/me - cognitoSub: {}", cognitoSub);
        userService.deleteAccountByCognitoSub(cognitoSub);
        return ResponseEntity.noContent().build();
    }
}
