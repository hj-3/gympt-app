package com.gympt.backend.controller;

import com.gympt.backend.dto.BodyProfileRequest;
import com.gympt.backend.dto.BodyProfileResponse;
import com.gympt.backend.service.BodyProfileService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/body-profiles")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Body Profiles", description = "Body profile and measurement endpoints")
@SecurityRequirement(name = "bearerAuth")
public class BodyProfileController {

    private final BodyProfileService bodyProfileService;

    @PostMapping
    @PreAuthorize("hasRole('USER')")
    @Operation(summary = "Create a new body profile measurement")
    public ResponseEntity<BodyProfileResponse> createBodyProfile(
            @Valid @RequestBody BodyProfileRequest request,
            Authentication authentication
    ) {
        // authentication.getName() returns DB user ID (UUID)
        UUID userId = UUID.fromString(authentication.getName());
        log.info("POST /api/v1/body-profiles - userId from JWT: {}", userId);
        BodyProfileResponse response = bodyProfileService.createBodyProfile(userId, request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/history")
    @PreAuthorize("hasRole('USER')")
    @Operation(summary = "Get body profile measurement history")
    public ResponseEntity<List<BodyProfileResponse>> getHistory(
            @RequestParam(required = false) Integer limit,
            Authentication authentication
    ) {
        UUID userId = UUID.fromString(authentication.getName());
        log.info("GET /api/v1/body-profiles/history - userId: {}, limit: {}", userId, limit);
        List<BodyProfileResponse> response = bodyProfileService.getHistory(userId, limit);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/latest")
    @PreAuthorize("hasRole('USER')")
    @Operation(summary = "Get latest body profile measurement")
    public ResponseEntity<BodyProfileResponse> getLatest(Authentication authentication) {
        UUID userId = UUID.fromString(authentication.getName());
        log.info("GET /api/v1/body-profiles/latest - userId: {}", userId);
        BodyProfileResponse response = bodyProfileService.getLatest(userId);
        return ResponseEntity.ok(response);
    }
}
