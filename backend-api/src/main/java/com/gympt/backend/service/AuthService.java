package com.gympt.backend.service;

import com.gympt.backend.auth.JwtTokenProvider;
import com.gympt.backend.domain.RefreshToken;
import com.gympt.backend.dto.AuthRequest;
import com.gympt.backend.dto.AuthResponse;
import com.gympt.backend.dto.RegisterRequest;
import com.gympt.backend.exception.ResourceNotFoundException;
import com.gympt.backend.exception.UnauthorizedException;
import com.gympt.backend.exception.ValidationException;
import com.gympt.backend.repository.RefreshTokenRepository;
import com.gympt.backend.user.User;
import com.gympt.backend.user.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.Collections;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class AuthService {

    private final UserRepository userRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;
    private final AuthenticationManager authenticationManager;

    @Value("${app.jwt.access-token-ttl}")
    private long accessTokenTtl;

    @Value("${app.jwt.refresh-token-ttl}")
    private long refreshTokenTtl;

    @Transactional
    public AuthResponse register(RegisterRequest request) {
        log.info("Registering new user with email: {}", request.getEmail());

        if (userRepository.findByEmail(request.getEmail()).isPresent()) {
            throw new ValidationException("Email already exists");
        }

        User user = User.builder()
            .email(request.getEmail())
            .password(passwordEncoder.encode(request.getPassword()))
            .name(request.getName())
            .age(request.getAge())
            .gender(request.getGender())
            .fitnessLevel(request.getFitnessLevel())
            .role(User.Role.USER)
            .status(User.UserStatus.ACTIVE)
            .build();

        user = userRepository.save(user);
        log.info("User registered successfully with id: {}", user.getId());

        // Generate tokens
        Authentication authentication = new UsernamePasswordAuthenticationToken(
            user.getId().toString(),
            null,
            Collections.singletonList(new SimpleGrantedAuthority("ROLE_" + user.getRole().name()))
        );

        String accessToken = jwtTokenProvider.generateAccessToken(authentication);
        String refreshToken = jwtTokenProvider.generateRefreshToken(authentication);

        // Save refresh token
        saveRefreshToken(user.getId(), refreshToken);

        return AuthResponse.of(user.getId(), accessToken, refreshToken, accessTokenTtl);
    }

    @Transactional
    public AuthResponse login(AuthRequest request) {
        log.info("User login attempt: {}", request.getEmail());

        Authentication authentication = authenticationManager.authenticate(
            new UsernamePasswordAuthenticationToken(request.getEmail(), request.getPassword())
        );

        User user = userRepository.findByEmail(request.getEmail())
            .orElseThrow(() -> new ResourceNotFoundException("User", "email", request.getEmail()));

        // Update last login
        user.setLastLoginAt(Instant.now());
        userRepository.save(user);

        // Generate tokens
        Authentication tokenAuth = new UsernamePasswordAuthenticationToken(
            user.getId().toString(),
            null,
            Collections.singletonList(new SimpleGrantedAuthority("ROLE_" + user.getRole().name()))
        );

        String accessToken = jwtTokenProvider.generateAccessToken(tokenAuth);
        String refreshToken = jwtTokenProvider.generateRefreshToken(tokenAuth);

        // Save refresh token
        saveRefreshToken(user.getId(), refreshToken);

        log.info("User logged in successfully: {}", user.getId());
        return AuthResponse.of(user.getId(), accessToken, refreshToken, accessTokenTtl);
    }

    @Transactional
    public AuthResponse refreshToken(String token) {
        log.info("Refreshing access token");

        RefreshToken refreshToken = refreshTokenRepository.findByToken(token)
            .orElseThrow(() -> new UnauthorizedException("Invalid refresh token"));

        if (refreshToken.getRevoked()) {
            throw new UnauthorizedException("Refresh token has been revoked");
        }

        if (refreshToken.isExpired()) {
            refreshTokenRepository.delete(refreshToken);
            throw new UnauthorizedException("Refresh token has expired");
        }

        User user = userRepository.findById(refreshToken.getUserId())
            .orElseThrow(() -> new ResourceNotFoundException("User", "id", refreshToken.getUserId()));

        // Generate new tokens
        Authentication authentication = new UsernamePasswordAuthenticationToken(
            user.getId().toString(),
            null,
            Collections.singletonList(new SimpleGrantedAuthority("ROLE_" + user.getRole().name()))
        );

        String newAccessToken = jwtTokenProvider.generateAccessToken(authentication);
        String newRefreshToken = jwtTokenProvider.generateRefreshToken(authentication);

        // Revoke old refresh token
        refreshToken.setRevoked(true);
        refreshTokenRepository.save(refreshToken);

        // Save new refresh token
        saveRefreshToken(user.getId(), newRefreshToken);

        log.info("Access token refreshed for user: {}", user.getId());
        return AuthResponse.of(user.getId(), newAccessToken, newRefreshToken, accessTokenTtl);
    }

    @Transactional
    public void logout(String token) {
        log.info("User logout");

        refreshTokenRepository.findByToken(token).ifPresent(refreshToken -> {
            refreshToken.setRevoked(true);
            refreshTokenRepository.save(refreshToken);
            log.info("Refresh token revoked for user: {}", refreshToken.getUserId());
        });
    }

    private void saveRefreshToken(UUID userId, String token) {
        RefreshToken refreshToken = RefreshToken.builder()
            .userId(userId)
            .token(token)
            .expiresAt(Instant.now().plusSeconds(refreshTokenTtl))
            .revoked(false)
            .build();

        refreshTokenRepository.save(refreshToken);
    }
}
