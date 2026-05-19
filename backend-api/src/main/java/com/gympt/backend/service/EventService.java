package com.gympt.backend.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.gympt.backend.domain.Report;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.services.eventbridge.EventBridgeClient;
import software.amazon.awssdk.services.eventbridge.model.PutEventsRequest;
import software.amazon.awssdk.services.eventbridge.model.PutEventsRequestEntry;
import software.amazon.awssdk.services.eventbridge.model.PutEventsResponse;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class EventService {

    private final EventBridgeClient eventBridgeClient;
    private final ObjectMapper objectMapper;

    @Value("${app.aws.eventbridge.bus-name:default}")
    private String eventBusName;

    @Value("${app.event.source:gympt.backend}")
    private String eventSource;

    public void publishPostureAnalysisRequest(UUID userId, String videoS3Key) {
        log.info("Publishing posture analysis request for user: {}, s3Key: {}", userId, videoS3Key);

        Map<String, Object> eventDetail = new HashMap<>();
        eventDetail.put("userId", userId.toString());
        eventDetail.put("videoS3Key", videoS3Key);
        eventDetail.put("timestamp", Instant.now().toString());

        publishEvent("PostureAnalysisRequested", eventDetail);
    }

    public void publishReportGeneration(UUID userId, Report.ReportType reportType) {
        log.info("Publishing report generation request for user: {}, reportType: {}", userId, reportType);

        Map<String, Object> eventDetail = new HashMap<>();
        eventDetail.put("userId", userId.toString());
        eventDetail.put("reportType", reportType.name());
        eventDetail.put("timestamp", Instant.now().toString());

        publishEvent("ReportGenerationRequested", eventDetail);
    }

    public void publishWorkoutCompleted(UUID userId, UUID sessionId) {
        log.info("Publishing workout completed event for user: {}, sessionId: {}", userId, sessionId);

        Map<String, Object> eventDetail = new HashMap<>();
        eventDetail.put("userId", userId.toString());
        eventDetail.put("sessionId", sessionId.toString());
        eventDetail.put("timestamp", Instant.now().toString());

        publishEvent("WorkoutCompleted", eventDetail);
    }

    private void publishEvent(String detailType, Map<String, Object> eventDetail) {
        try {
            String detailJson = objectMapper.writeValueAsString(eventDetail);

            PutEventsRequestEntry entry = PutEventsRequestEntry.builder()
                .source(eventSource)
                .detailType(detailType)
                .detail(detailJson)
                .eventBusName(eventBusName)
                .build();

            PutEventsRequest request = PutEventsRequest.builder()
                .entries(entry)
                .build();

            PutEventsResponse response = eventBridgeClient.putEvents(request);

            if (response.failedEntryCount() > 0) {
                log.error("Failed to publish event: {}, failures: {}",
                    detailType, response.entries());
                throw new RuntimeException("Failed to publish event to EventBridge");
            }

            log.info("Event published successfully: {}", detailType);

        } catch (JsonProcessingException e) {
            log.error("Error serializing event detail", e);
            throw new RuntimeException("Failed to serialize event detail", e);
        } catch (Exception e) {
            log.error("Error publishing event to EventBridge", e);
            throw new RuntimeException("Failed to publish event", e);
        }
    }
}
