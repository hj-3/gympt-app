package com.gympt.backend.controller;

import com.gympt.backend.domain.WorkoutGoal;
import com.gympt.backend.dto.WorkoutGoalRequest;
import com.gympt.backend.dto.WorkoutGoalResponse;
import com.gympt.backend.service.WorkoutGoalService;
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
@RequestMapping("/api/v1/goals")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Workout Goals", description = "Workout goal management endpoints")
@SecurityRequirement(name = "bearerAuth")
public class WorkoutGoalController {

    private final WorkoutGoalService workoutGoalService;

    @PostMapping
    @PreAuthorize("hasRole('USER')")
    @Operation(summary = "Create a new workout goal")
    public ResponseEntity<WorkoutGoalResponse> createGoal(
            @Valid @RequestBody WorkoutGoalRequest request,
            Authentication authentication
    ) {
        UUID userId = UUID.fromString(authentication.getName());
        log.info("POST /api/v1/goals - userId: {}", userId);
        WorkoutGoalResponse response = workoutGoalService.createGoal(userId, request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping
    @PreAuthorize("hasRole('USER')")
    @Operation(summary = "Get all workout goals for the user")
    public ResponseEntity<List<WorkoutGoalResponse>> getGoals(Authentication authentication) {
        UUID userId = UUID.fromString(authentication.getName());
        log.info("GET /api/v1/goals - userId: {}", userId);
        List<WorkoutGoalResponse> response = workoutGoalService.getGoals(userId);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/{goalId}")
    @PreAuthorize("hasRole('USER')")
    @Operation(summary = "Get a specific workout goal")
    public ResponseEntity<WorkoutGoalResponse> getGoal(@PathVariable UUID goalId) {
        log.info("GET /api/v1/goals/{} - goalId: {}", goalId, goalId);
        WorkoutGoalResponse response = workoutGoalService.getGoal(goalId);
        return ResponseEntity.ok(response);
    }

    @PatchMapping("/{goalId}/status")
    @PreAuthorize("hasRole('USER')")
    @Operation(summary = "Update workout goal status")
    public ResponseEntity<WorkoutGoalResponse> updateGoalStatus(
            @PathVariable UUID goalId,
            @RequestParam WorkoutGoal.GoalStatus status
    ) {
        log.info("PATCH /api/v1/goals/{}/status - goalId: {}, status: {}", goalId, goalId, status);
        WorkoutGoalResponse response = workoutGoalService.updateGoalStatus(goalId, status);
        return ResponseEntity.ok(response);
    }

    @DeleteMapping("/{goalId}")
    @PreAuthorize("hasRole('USER')")
    @Operation(summary = "Delete a workout goal")
    public ResponseEntity<Void> deleteGoal(@PathVariable UUID goalId) {
        log.info("DELETE /api/v1/goals/{} - goalId: {}", goalId, goalId);
        workoutGoalService.deleteGoal(goalId);
        return ResponseEntity.noContent().build();
    }
}
