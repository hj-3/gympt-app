package com.gympt.backend.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class StatsResponse {

    private Integer totalMinutes;
    private Integer completedSessions;
    private BigDecimal avgPostureScore;
    private Integer weeklyWorkouts;
    private List<RecentSessionDto> recentSessions;
    private List<WeeklyDataDto> weeklyData;
    private TodayRoutineDto todayRoutine;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RecentSessionDto {
        private String id;
        private String exerciseName;
        private Integer duration;
        private BigDecimal postureScore;
        private String completedAt;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class WeeklyDataDto {
        private String day;
        private Integer minutes;
        private Integer sessions;
    }

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class TodayRoutineDto {
        private String id;
        private String name;
        private Integer exerciseCount;
        private Integer estimatedDuration;
    }
}
