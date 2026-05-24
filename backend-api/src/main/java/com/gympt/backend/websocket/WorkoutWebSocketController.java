package com.gympt.backend.websocket;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.messaging.handler.annotation.DestinationVariable;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.SendTo;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDateTime;

/**
 * WebSocket controller for real-time posture feedback
 */
@Slf4j
@Controller
public class WorkoutWebSocketController {

    private final SimpMessagingTemplate messagingTemplate;

    public WorkoutWebSocketController(SimpMessagingTemplate messagingTemplate) {
        this.messagingTemplate = messagingTemplate;
    }

    /**
     * Handle client subscription to workout session
     */
    @MessageMapping("/workout/subscribe/{sessionId}")
    @SendTo("/topic/workout/{sessionId}")
    public String subscribeToWorkout(@DestinationVariable String sessionId) {
        log.info("Client subscribed to workout session: {}", sessionId);
        return "Subscribed to session: " + sessionId;
    }

    /**
     * Send posture feedback to specific session
     * This will be called by REST endpoint from posture-analysis-service
     */
    public void sendPostureFeedback(String sessionId, PostureFeedbackMessage message) {
        log.debug("Sending posture feedback to session {}: score={}, valid={}",
            sessionId, message.getFormScore(), message.getIsValid());

        message.setTimestamp(LocalDateTime.now());
        messagingTemplate.convertAndSend("/topic/workout/" + sessionId, message);
    }

    /**
     * Broadcast to all clients (for system messages)
     */
    public void broadcastMessage(String message) {
        messagingTemplate.convertAndSend("/topic/broadcast", message);
    }
}

/**
 * REST endpoint to receive feedback from posture-analysis-service
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/ws")
@RequiredArgsConstructor
class WorkoutWebSocketRestController {

    private final WorkoutWebSocketController webSocketController;

    /**
     * REST endpoint to push posture feedback to WebSocket
     * Called by posture-analysis-service
     */
    @PostMapping("/feedback")
    public void pushFeedback(@RequestBody PostureFeedbackMessage message) {
        log.info("Received posture feedback for session {}: score={}",
            message.getSessionId(), message.getFormScore());

        webSocketController.sendPostureFeedback(message.getSessionId(), message);
    }
}
