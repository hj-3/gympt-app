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
}
