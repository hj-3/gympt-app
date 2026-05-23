package com.gympt.backend.controller;

import com.gympt.backend.dto.StatsResponse;
import com.gympt.backend.service.StatsService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/stats")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Statistics", description = "User statistics and analytics endpoints")
public class StatsController {

    private final StatsService statsService;

    @GetMapping("/{userId}")
    @Operation(summary = "Get user statistics")
    public ResponseEntity<StatsResponse> getStats(@PathVariable UUID userId) {
        log.info("GET /api/v1/stats/{}", userId);
        StatsResponse stats = statsService.getUserStats(userId);
        return ResponseEntity.ok(stats);
    }

    @GetMapping("/{userId}/weekly")
    @Operation(summary = "Get weekly progress")
    public ResponseEntity<StatsResponse> getWeeklyProgress(@PathVariable UUID userId) {
        log.info("GET /api/v1/stats/{}/weekly", userId);
        StatsResponse stats = statsService.getWeeklyProgress(userId);
        return ResponseEntity.ok(stats);
    }
}
