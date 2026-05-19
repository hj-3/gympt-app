package com.gympt.backend.controller;

import com.gympt.backend.dto.EndWorkoutSessionRequest;
import com.gympt.backend.dto.WorkoutSessionRequest;
import com.gympt.backend.dto.WorkoutSessionResponse;
import com.gympt.backend.service.WorkoutSessionService;
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
@RequestMapping("/api/v1/sessions")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Workout Sessions", description = "Workout session tracking endpoints")
@SecurityRequirement(name = "bearerAuth")
public class WorkoutSessionController {

    private final WorkoutSessionService workoutSessionService;

    @PostMapping("/start")
    @PreAuthorize("hasRole('USER')")
    @Operation(summary = "Start a new workout session")
    public ResponseEntity<WorkoutSessionResponse> startSession(
            @Valid @RequestBody WorkoutSessionRequest request,
            Authentication authentication
    ) {
        UUID userId = UUID.fromString(authentication.getName());
        log.info("POST /api/v1/sessions/start - userId: {}", userId);
        WorkoutSessionResponse response = workoutSessionService.startSession(userId, request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @PutMapping("/{sessionId}/end")
    @PreAuthorize("hasRole('USER')")
    @Operation(summary = "End a workout session")
    public ResponseEntity<WorkoutSessionResponse> endSession(
            @PathVariable UUID sessionId,
            @Valid @RequestBody EndWorkoutSessionRequest request
    ) {
        log.info("PUT /api/v1/sessions/{}/end - sessionId: {}", sessionId, sessionId);
        WorkoutSessionResponse response = workoutSessionService.endSession(sessionId, request);
        return ResponseEntity.ok(response);
    }

    @GetMapping
    @PreAuthorize("hasRole('USER')")
    @Operation(summary = "Get all workout sessions for the user")
    public ResponseEntity<List<WorkoutSessionResponse>> getUserSessions(Authentication authentication) {
        UUID userId = UUID.fromString(authentication.getName());
        log.info("GET /api/v1/sessions - userId: {}", userId);
        List<WorkoutSessionResponse> response = workoutSessionService.getUserSessions(userId);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/{sessionId}")
    @PreAuthorize("hasRole('USER')")
    @Operation(summary = "Get a specific workout session")
    public ResponseEntity<WorkoutSessionResponse> getSession(@PathVariable UUID sessionId) {
        log.info("GET /api/v1/sessions/{} - sessionId: {}", sessionId, sessionId);
        WorkoutSessionResponse response = workoutSessionService.getSession(sessionId);
        return ResponseEntity.ok(response);
    }

    @PutMapping("/{sessionId}/cancel")
    @PreAuthorize("hasRole('USER')")
    @Operation(summary = "Cancel a workout session")
    public ResponseEntity<WorkoutSessionResponse> cancelSession(@PathVariable UUID sessionId) {
        log.info("PUT /api/v1/sessions/{}/cancel - sessionId: {}", sessionId, sessionId);
        WorkoutSessionResponse response = workoutSessionService.cancelSession(sessionId);
        return ResponseEntity.ok(response);
    }
}
