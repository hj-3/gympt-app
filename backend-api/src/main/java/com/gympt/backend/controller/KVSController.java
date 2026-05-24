package com.gympt.backend.controller;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@Slf4j
@RestController
@RequestMapping("/api/v1/kvs")
@RequiredArgsConstructor
public class KVSController {

    @Value("${app.aws.region:ap-northeast-2}")
    private String awsRegion;

    @Value("${app.kvs.stream-name:gympt-prod-live-sessions}")
    private String kvsStreamName;

    @Value("${app.kvs.signaling-channel-name:prod-live-sessions-signaling}")
    private String signalingChannelName;

    @GetMapping("/credentials/{sessionId}")
    public ResponseEntity<Map<String, Object>> getKVSCredentials(
            @PathVariable String sessionId,
            @AuthenticationPrincipal UserDetails userDetails) {

        log.info("Get KVS credentials for session: {}", sessionId);

        // TODO: Implement actual KVS credentials generation
        // This should:
        // 1. Generate WebRTC signaling channel credentials
        // 2. Create ICE server configuration
        // 3. Return credentials with limited TTL

        Map<String, Object> credentials = new HashMap<>();
        credentials.put("region", awsRegion);
        credentials.put("streamName", kvsStreamName);
        credentials.put("signalingChannelName", signalingChannelName);
        credentials.put("sessionId", sessionId);

        // WebRTC ICE servers configuration
        List<Map<String, Object>> iceServers = new ArrayList<>();

        // STUN server
        Map<String, Object> stunServer = new HashMap<>();
        stunServer.put("urls", "stun:stun.l.google.com:19302");
        iceServers.add(stunServer);

        credentials.put("iceServers", iceServers);
        credentials.put("expiresAt", System.currentTimeMillis() + (3600 * 1000)); // 1 hour

        log.warn("KVS credentials generation not fully implemented - using placeholder");

        return ResponseEntity.ok(credentials);
    }
}
