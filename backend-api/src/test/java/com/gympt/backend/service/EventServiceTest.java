package com.gympt.backend.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.gympt.backend.domain.Report;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;
import software.amazon.awssdk.services.eventbridge.EventBridgeClient;
import software.amazon.awssdk.services.eventbridge.model.PutEventsRequest;
import software.amazon.awssdk.services.eventbridge.model.PutEventsResponse;
import software.amazon.awssdk.services.eventbridge.model.PutEventsResultEntry;

import java.util.Collections;
import java.util.UUID;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Unit tests for EventService.
 * Tests EventBridge event publishing for various domain events.
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("EventService Tests")
class EventServiceTest {

    @Mock
    private EventBridgeClient eventBridgeClient;

    @Mock
    private ObjectMapper objectMapper;

    @InjectMocks
    private EventService eventService;

    private String eventBusName = "test-event-bus";
    private String eventSource = "gympt.backend.test";
    private UUID testUserId;
    private UUID testSessionId;

    @BeforeEach
    void setUp() {
        testUserId = UUID.randomUUID();
        testSessionId = UUID.randomUUID();

        ReflectionTestUtils.setField(eventService, "eventBusName", eventBusName);
        ReflectionTestUtils.setField(eventService, "eventSource", eventSource);
    }

    @Test
    @DisplayName("Should publish posture analysis request successfully")
    void shouldPublishPostureAnalysisRequestSuccessfully() throws Exception {
        // Arrange
        String videoS3Key = "videos/user123/workout.mp4";
        String eventDetailJson = "{\"userId\":\"" + testUserId + "\",\"videoS3Key\":\"" + videoS3Key + "\"}";

        when(objectMapper.writeValueAsString(any())).thenReturn(eventDetailJson);
        when(eventBridgeClient.putEvents(any(PutEventsRequest.class)))
            .thenReturn(PutEventsResponse.builder()
                .failedEntryCount(0)
                .entries(Collections.emptyList())
                .build());

        // Act
        eventService.publishPostureAnalysisRequest(testUserId, videoS3Key);

        // Assert
        ArgumentCaptor<PutEventsRequest> requestCaptor = ArgumentCaptor.forClass(PutEventsRequest.class);
        verify(eventBridgeClient, times(1)).putEvents(requestCaptor.capture());

        PutEventsRequest capturedRequest = requestCaptor.getValue();
        assertThat(capturedRequest.entries()).hasSize(1);
        assertThat(capturedRequest.entries().get(0).source()).isEqualTo(eventSource);
        assertThat(capturedRequest.entries().get(0).detailType()).isEqualTo("PostureAnalysisRequested");
        assertThat(capturedRequest.entries().get(0).eventBusName()).isEqualTo(eventBusName);
    }

    @Test
    @DisplayName("Should publish report generation request successfully")
    void shouldPublishReportGenerationSuccessfully() throws Exception {
        // Arrange
        Report.ReportType reportType = Report.ReportType.WORKOUT_SUMMARY;
        String eventDetailJson = "{\"userId\":\"" + testUserId + "\",\"reportType\":\"" + reportType.name() + "\"}";

        when(objectMapper.writeValueAsString(any())).thenReturn(eventDetailJson);
        when(eventBridgeClient.putEvents(any(PutEventsRequest.class)))
            .thenReturn(PutEventsResponse.builder()
                .failedEntryCount(0)
                .entries(Collections.emptyList())
                .build());

        // Act
        eventService.publishReportGeneration(testUserId, reportType);

        // Assert
        ArgumentCaptor<PutEventsRequest> requestCaptor = ArgumentCaptor.forClass(PutEventsRequest.class);
        verify(eventBridgeClient, times(1)).putEvents(requestCaptor.capture());

        PutEventsRequest capturedRequest = requestCaptor.getValue();
        assertThat(capturedRequest.entries()).hasSize(1);
        assertThat(capturedRequest.entries().get(0).detailType()).isEqualTo("ReportGenerationRequested");
    }

    @Test
    @DisplayName("Should publish workout completed event successfully")
    void shouldPublishWorkoutCompletedSuccessfully() throws Exception {
        // Arrange
        String eventDetailJson = "{\"userId\":\"" + testUserId + "\",\"sessionId\":\"" + testSessionId + "\"}";

        when(objectMapper.writeValueAsString(any())).thenReturn(eventDetailJson);
        when(eventBridgeClient.putEvents(any(PutEventsRequest.class)))
            .thenReturn(PutEventsResponse.builder()
                .failedEntryCount(0)
                .entries(Collections.emptyList())
                .build());

        // Act
        eventService.publishWorkoutCompleted(testUserId, testSessionId);

        // Assert
        ArgumentCaptor<PutEventsRequest> requestCaptor = ArgumentCaptor.forClass(PutEventsRequest.class);
        verify(eventBridgeClient, times(1)).putEvents(requestCaptor.capture());

        PutEventsRequest capturedRequest = requestCaptor.getValue();
        assertThat(capturedRequest.entries()).hasSize(1);
        assertThat(capturedRequest.entries().get(0).detailType()).isEqualTo("WorkoutCompleted");
    }

    @Test
    @DisplayName("Should throw exception when EventBridge returns failures")
    void shouldThrowExceptionWhenEventBridgeReturnsFailures() throws Exception {
        // Arrange
        String videoS3Key = "videos/user123/workout.mp4";
        String eventDetailJson = "{\"userId\":\"" + testUserId + "\"}";

        when(objectMapper.writeValueAsString(any())).thenReturn(eventDetailJson);
        when(eventBridgeClient.putEvents(any(PutEventsRequest.class)))
            .thenReturn(PutEventsResponse.builder()
                .failedEntryCount(1)
                .entries(PutEventsResultEntry.builder()
                    .errorCode("InternalException")
                    .errorMessage("Internal error")
                    .build())
                .build());

        // Act & Assert
        assertThatThrownBy(() -> eventService.publishPostureAnalysisRequest(testUserId, videoS3Key))
            .isInstanceOf(RuntimeException.class)
            .hasMessageContaining("Failed to publish event to EventBridge");

        verify(eventBridgeClient, times(1)).putEvents(any(PutEventsRequest.class));
    }

    @Test
    @DisplayName("Should throw exception when JSON serialization fails")
    void shouldThrowExceptionWhenJsonSerializationFails() throws Exception {
        // Arrange
        String videoS3Key = "videos/user123/workout.mp4";

        when(objectMapper.writeValueAsString(any()))
            .thenThrow(new com.fasterxml.jackson.core.JsonProcessingException("Serialization error") {});

        // Act & Assert
        assertThatThrownBy(() -> eventService.publishPostureAnalysisRequest(testUserId, videoS3Key))
            .isInstanceOf(RuntimeException.class)
            .hasMessageContaining("Failed to serialize event detail");

        verify(eventBridgeClient, never()).putEvents(any(PutEventsRequest.class));
    }

    @Test
    @DisplayName("Should throw exception when EventBridge client fails")
    void shouldThrowExceptionWhenEventBridgeClientFails() throws Exception {
        // Arrange
        String videoS3Key = "videos/user123/workout.mp4";
        String eventDetailJson = "{\"userId\":\"" + testUserId + "\"}";

        when(objectMapper.writeValueAsString(any())).thenReturn(eventDetailJson);
        when(eventBridgeClient.putEvents(any(PutEventsRequest.class)))
            .thenThrow(new RuntimeException("EventBridge connection error"));

        // Act & Assert
        assertThatThrownBy(() -> eventService.publishPostureAnalysisRequest(testUserId, videoS3Key))
            .isInstanceOf(RuntimeException.class)
            .hasMessageContaining("Failed to publish event");

        verify(eventBridgeClient, times(1)).putEvents(any(PutEventsRequest.class));
    }

    @Test
    @DisplayName("Should publish event with correct event bus name")
    void shouldPublishEventWithCorrectEventBusName() throws Exception {
        // Arrange
        String customEventBusName = "custom-event-bus";
        ReflectionTestUtils.setField(eventService, "eventBusName", customEventBusName);

        String videoS3Key = "videos/user123/workout.mp4";
        String eventDetailJson = "{\"userId\":\"" + testUserId + "\"}";

        when(objectMapper.writeValueAsString(any())).thenReturn(eventDetailJson);
        when(eventBridgeClient.putEvents(any(PutEventsRequest.class)))
            .thenReturn(PutEventsResponse.builder()
                .failedEntryCount(0)
                .build());

        // Act
        eventService.publishPostureAnalysisRequest(testUserId, videoS3Key);

        // Assert
        ArgumentCaptor<PutEventsRequest> requestCaptor = ArgumentCaptor.forClass(PutEventsRequest.class);
        verify(eventBridgeClient).putEvents(requestCaptor.capture());

        assertThat(requestCaptor.getValue().entries().get(0).eventBusName())
            .isEqualTo(customEventBusName);
    }

    @Test
    @DisplayName("Should publish event with correct event source")
    void shouldPublishEventWithCorrectEventSource() throws Exception {
        // Arrange
        String customEventSource = "custom.backend";
        ReflectionTestUtils.setField(eventService, "eventSource", customEventSource);

        String videoS3Key = "videos/user123/workout.mp4";
        String eventDetailJson = "{\"userId\":\"" + testUserId + "\"}";

        when(objectMapper.writeValueAsString(any())).thenReturn(eventDetailJson);
        when(eventBridgeClient.putEvents(any(PutEventsRequest.class)))
            .thenReturn(PutEventsResponse.builder()
                .failedEntryCount(0)
                .build());

        // Act
        eventService.publishPostureAnalysisRequest(testUserId, videoS3Key);

        // Assert
        ArgumentCaptor<PutEventsRequest> requestCaptor = ArgumentCaptor.forClass(PutEventsRequest.class);
        verify(eventBridgeClient).putEvents(requestCaptor.capture());

        assertThat(requestCaptor.getValue().entries().get(0).source())
            .isEqualTo(customEventSource);
    }
}
