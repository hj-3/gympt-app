package com.gympt.backend.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.services.sqs.SqsClient;
import software.amazon.awssdk.services.sqs.model.SendMessageRequest;

import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class SqsService {

    private final SqsClient sqsClient;
    private final ObjectMapper objectMapper;

    @Value("${app.aws.sqs.recommendation-update-queue-url:}")
    private String recommendationUpdateQueueUrl;

    @Value("${app.aws.sqs.notification-queue-url:}")
    private String notificationQueueUrl;

    public void publishRecommendationUpdateEvent(UUID userId, UUID sessionId) {
        if (recommendationUpdateQueueUrl == null || recommendationUpdateQueueUrl.isBlank()) {
            log.warn("recommendation-update-queue-url not configured, skipping SQS publish");
            return;
        }
        try {
            String body = objectMapper.writeValueAsString(Map.of(
                "userId", userId.toString(),
                "sessionId", sessionId.toString()
            ));
            sqsClient.sendMessage(SendMessageRequest.builder()
                .queueUrl(recommendationUpdateQueueUrl)
                .messageBody(body)
                .build());
            log.info("Published recommendation update event for user={} session={}", userId, sessionId);
        } catch (Exception e) {
            log.error("Failed to publish recommendation update event: {}", e.getMessage());
        }
    }

    public void publishWorkoutCompletedNotification(UUID userId, UUID sessionId) {
        if (notificationQueueUrl == null || notificationQueueUrl.isBlank()) {
            log.warn("notification-queue-url not configured, skipping workout completed notification");
            return;
        }
        try {
            String body = objectMapper.writeValueAsString(Map.of(
                "type", "WORKOUT_COMPLETED",
                "userId", userId.toString(),
                "sessionId", sessionId.toString(),
                "timestamp", java.time.Instant.now().toString()
            ));
            sqsClient.sendMessage(SendMessageRequest.builder()
                .queueUrl(notificationQueueUrl)
                .messageBody(body)
                .build());
            log.info("Published workout completed notification for user={} session={}", userId, sessionId);
        } catch (Exception e) {
            log.error("Failed to publish workout completed notification: {}", e.getMessage());
        }
    }
}
