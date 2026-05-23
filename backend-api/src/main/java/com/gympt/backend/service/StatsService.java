package com.gympt.backend.service;

import com.gympt.backend.domain.WorkoutSession;
import com.gympt.backend.dto.StatsResponse;
import com.gympt.backend.repository.WorkoutSessionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.TextStyle;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class StatsService {

    private final WorkoutSessionRepository workoutSessionRepository;

    @Transactional(readOnly = true)
    public StatsResponse getUserStats(UUID userId) {
        log.info("Fetching stats for user: {}", userId);

        // Get all completed sessions for the user
        List<WorkoutSession> sessions = workoutSessionRepository.findByUserIdAndStatus(
            userId,
            WorkoutSession.SessionStatus.COMPLETED
        );

        // Calculate total minutes
        int totalMinutes = sessions.stream()
            .mapToInt(s -> s.getDurationMinutes() != null ? s.getDurationMinutes() : 0)
            .sum();

        // Calculate average posture score
        BigDecimal avgPostureScore = sessions.stream()
            .filter(s -> s.getAvgPostureScore() != null)
            .map(WorkoutSession::getAvgPostureScore)
            .reduce(BigDecimal.ZERO, BigDecimal::add)
            .divide(
                BigDecimal.valueOf(sessions.isEmpty() ? 1 : sessions.size()),
                2,
                RoundingMode.HALF_UP
            );

        // Get weekly workouts (last 7 days)
        LocalDateTime weekAgo = LocalDateTime.now().minusDays(7);
        int weeklyWorkouts = (int) sessions.stream()
            .filter(s -> s.getStartTime() != null && s.getStartTime().isAfter(weekAgo))
            .count();

        // Get recent sessions (last 5)
        List<StatsResponse.RecentSessionDto> recentSessions = sessions.stream()
            .sorted(Comparator.comparing(WorkoutSession::getStartTime).reversed())
            .limit(5)
            .map(this::mapToRecentSession)
            .collect(Collectors.toList());

        // Get weekly data
        List<StatsResponse.WeeklyDataDto> weeklyData = generateWeeklyData(sessions);

        return StatsResponse.builder()
            .totalMinutes(totalMinutes)
            .completedSessions(sessions.size())
            .avgPostureScore(avgPostureScore)
            .weeklyWorkouts(weeklyWorkouts)
            .recentSessions(recentSessions)
            .weeklyData(weeklyData)
            .todayRoutine(null) // TODO: Implement when routine feature is ready
            .build();
    }

    @Transactional(readOnly = true)
    public StatsResponse getWeeklyProgress(UUID userId) {
        LocalDateTime weekAgo = LocalDateTime.now().minusDays(7);
        List<WorkoutSession> sessions = workoutSessionRepository.findByUserIdAndStartTimeAfter(
            userId,
            weekAgo
        );

        List<StatsResponse.WeeklyDataDto> weeklyData = generateWeeklyData(sessions);

        return StatsResponse.builder()
            .weeklyData(weeklyData)
            .weeklyWorkouts(sessions.size())
            .build();
    }

    private StatsResponse.RecentSessionDto mapToRecentSession(WorkoutSession session) {
        return StatsResponse.RecentSessionDto.builder()
            .id(session.getId().toString())
            .exerciseName(session.getExerciseType() != null ? session.getExerciseType().name() : "Unknown")
            .duration(session.getDurationMinutes())
            .postureScore(session.getAvgPostureScore())
            .completedAt(session.getEndTime() != null ? session.getEndTime().toString() : "")
            .build();
    }

    private List<StatsResponse.WeeklyDataDto> generateWeeklyData(List<WorkoutSession> sessions) {
        LocalDate today = LocalDate.now();
        Map<LocalDate, List<WorkoutSession>> sessionsByDate = sessions.stream()
            .filter(s -> s.getStartTime() != null)
            .collect(Collectors.groupingBy(s -> s.getStartTime().toLocalDate()));

        List<StatsResponse.WeeklyDataDto> weeklyData = new ArrayList<>();
        for (int i = 6; i >= 0; i--) {
            LocalDate date = today.minusDays(i);
            List<WorkoutSession> daySessions = sessionsByDate.getOrDefault(date, Collections.emptyList());

            int minutes = daySessions.stream()
                .mapToInt(s -> s.getDurationMinutes() != null ? s.getDurationMinutes() : 0)
                .sum();

            weeklyData.add(StatsResponse.WeeklyDataDto.builder()
                .day(date.getDayOfWeek().getDisplayName(TextStyle.SHORT, Locale.KOREAN))
                .minutes(minutes)
                .sessions(daySessions.size())
                .build());
        }

        return weeklyData;
    }
}
