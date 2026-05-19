package com.gympt.backend.util;

import com.gympt.backend.auth.JwtTokenProvider;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;

import java.util.Base64;
import java.util.Collections;
import java.util.UUID;

/**
 * Utility class for generating JWT tokens in tests.
 */
public class JwtTestUtil {

    private static final String TEST_SECRET = Base64.getEncoder().encodeToString(
        "test-secret-key-for-jwt-token-signing-must-be-at-least-256-bits".getBytes()
    );
    private static final long ACCESS_TOKEN_TTL = 3600;
    private static final long REFRESH_TOKEN_TTL = 86400;

    private static JwtTokenProvider jwtTokenProvider;

    static {
        jwtTokenProvider = new JwtTokenProvider(TEST_SECRET, ACCESS_TOKEN_TTL, REFRESH_TOKEN_TTL);
    }

    /**
     * Generate an access token for a given user ID.
     */
    public static String generateAccessToken(UUID userId) {
        Authentication authentication = new UsernamePasswordAuthenticationToken(
            userId.toString(),
            null,
            Collections.singletonList(new SimpleGrantedAuthority("ROLE_USER"))
        );
        return jwtTokenProvider.generateAccessToken(authentication);
    }

    /**
     * Generate an access token for a given user ID with custom role.
     */
    public static String generateAccessToken(UUID userId, String role) {
        Authentication authentication = new UsernamePasswordAuthenticationToken(
            userId.toString(),
            null,
            Collections.singletonList(new SimpleGrantedAuthority("ROLE_" + role))
        );
        return jwtTokenProvider.generateAccessToken(authentication);
    }

    /**
     * Generate a refresh token for a given user ID.
     */
    public static String generateRefreshToken(UUID userId) {
        Authentication authentication = new UsernamePasswordAuthenticationToken(
            userId.toString(),
            null,
            Collections.singletonList(new SimpleGrantedAuthority("ROLE_USER"))
        );
        return jwtTokenProvider.generateRefreshToken(authentication);
    }

    /**
     * Validate a token.
     */
    public static boolean validateToken(String token) {
        return jwtTokenProvider.validateToken(token);
    }

    /**
     * Extract user ID from token.
     */
    public static String getUserIdFromToken(String token) {
        return jwtTokenProvider.getUserIdFromToken(token);
    }

    /**
     * Get the JWT token provider instance.
     */
    public static JwtTokenProvider getTokenProvider() {
        return jwtTokenProvider;
    }
}
