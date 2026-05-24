package com.gympt.backend.websocket;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PostureFeedbackMessage {
    private String sessionId;
    private String userId;
    private String exercise;
    private Integer repCount;
    private Double formScore;
    private Boolean isValid;
    private List<String> feedback;
    private Map<String, Double> angles;
    private LocalDateTime timestamp;
    private String messageType; // "feedback", "rep_complete", "session_end"
}
