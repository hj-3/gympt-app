package com.gympt.backend.controller;

import com.gympt.backend.domain.WorkoutSession;
import com.gympt.backend.repository.WorkoutSessionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/api/v1/reports")
@RequiredArgsConstructor
public class WorkoutReportController {

    private final WorkoutSessionRepository workoutSessionRepository;

    @GetMapping("/{sessionId}")
    @Transactional(readOnly = true)
    public ResponseEntity<Map<String, Object>> getReport(
            @PathVariable String sessionId,
            @AuthenticationPrincipal UserDetails userDetails) {

        log.info("Get report for session: {}", sessionId);

        UUID sessionUuid;
        try {
            sessionUuid = UUID.fromString(sessionId);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().build();
        }

        Optional<WorkoutSession> sessionOpt = workoutSessionRepository.findById(sessionUuid);
        if (sessionOpt.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        return ResponseEntity.ok(buildReportMap(sessionOpt.get()));
    }

    @GetMapping("/user/{userId}")
    @Transactional(readOnly = true)
    public ResponseEntity<Map<String, Object>> getReports(
            @PathVariable String userId,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int limit,
            @AuthenticationPrincipal UserDetails userDetails) {

        log.info("Get reports for user: {}, page: {}, limit: {}", userId, page, limit);

        UUID userUuid;
        try {
            userUuid = UUID.fromString(userId);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().build();
        }

        PageRequest pageable = PageRequest.of(
            Math.max(page - 1, 0), limit, Sort.by("startTime").descending()
        );
        Page<WorkoutSession> sessionPage = workoutSessionRepository.findByUserIdAndStatus(
            userUuid, WorkoutSession.SessionStatus.COMPLETED, pageable
        );

        List<Map<String, Object>> items = sessionPage.getContent().stream()
            .map(this::buildReportMap)
            .collect(Collectors.toList());

        Map<String, Object> response = new HashMap<>();
        response.put("items", items);
        response.put("total", sessionPage.getTotalElements());
        response.put("page", page);
        response.put("limit", limit);
        response.put("totalPages", sessionPage.getTotalPages());

        return ResponseEntity.ok(response);
    }

    private Map<String, Object> buildReportMap(WorkoutSession session) {
        int durationMinutes = session.getTotalDuration() != null ? session.getTotalDuration() / 60 : 0;
        BigDecimal caloriesBurned = session.getCaloriesBurned() != null ? session.getCaloriesBurned() : BigDecimal.ZERO;
        BigDecimal avgScore = session.getAvgPostureScore() != null ? session.getAvgPostureScore() : BigDecimal.ZERO;
        int totalReps = session.getTotalReps() != null ? session.getTotalReps() : 0;
        String exerciseName = session.getExerciseName() != null ? session.getExerciseName() : "운동";
        String completedAt = session.getEndTime() != null
            ? session.getEndTime().toString()
            : session.getStartTime().toString();

        Map<String, Object> summary = new HashMap<>();
        summary.put("totalDuration", durationMinutes);
        summary.put("exercisesCompleted", 1);
        summary.put("averagePostureScore", avgScore);
        summary.put("caloriesBurned", caloriesBurned);
        summary.put("totalReps", totalReps);
        summary.put("exerciseName", exerciseName);

        List<Map<String, Object>> exercises = new ArrayList<>();
        if (session.getExerciseType() != null) {
            Map<String, Object> ex = new HashMap<>();
            ex.put("name", exerciseName);
            ex.put("reps", totalReps);
            ex.put("sets", 1);
            ex.put("duration", durationMinutes);
            ex.put("postureScore", avgScore);
            exercises.add(ex);
        }

        Map<String, Object> report = new HashMap<>();
        report.put("reportId", session.getId().toString());
        report.put("sessionId", session.getId().toString());
        report.put("completedAt", completedAt);
        report.put("summary", summary);
        report.put("exercises", exercises);
        report.put("insights", List.of(
            String.format("총 %d회의 %s을 완료했습니다.", totalReps, exerciseName),
            String.format("평균 자세 점수 %.1f점입니다.", avgScore)
        ));
        report.put("recommendations", Collections.emptyList());

        return report;
    }
}
