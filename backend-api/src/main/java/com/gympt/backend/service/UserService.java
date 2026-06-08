package com.gympt.backend.service;

import com.gympt.backend.dto.UserProfileRequest;
import com.gympt.backend.dto.UserProfileResponse;
import com.gympt.backend.exception.ResourceNotFoundException;
import com.gympt.backend.user.User;
import com.gympt.backend.user.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class UserService {

    private final UserRepository userRepository;

    @Transactional(readOnly = true)
    public UserProfileResponse getProfile(UUID userId) {
        User user = userRepository.findById(userId)
            .orElseThrow(() -> new ResourceNotFoundException("User", "id", userId));
        return UserProfileResponse.from(user);
    }

    @Transactional
    public UserProfileResponse updateProfile(UUID userId, UserProfileRequest request) {
        User user = userRepository.findById(userId)
            .orElseThrow(() -> new ResourceNotFoundException("User", "id", userId));
        applyProfileUpdates(user, request);
        return UserProfileResponse.from(userRepository.save(user));
    }

    @Transactional
    public void deleteAccount(UUID userId) {
        log.info("Hard-deleting account for user: {}", userId);
        User user = userRepository.findById(userId)
            .orElseThrow(() -> new ResourceNotFoundException("User", "id", userId));
        userRepository.delete(user); // DB CASCADE removes all related data
        log.info("Account hard-deleted for user: {}", userId);
    }

    @Transactional(readOnly = true)
    public UserProfileResponse getProfileByCognitoSub(String cognitoSub) {
        User user = userRepository.findByCognitoSub(cognitoSub)
            .orElseThrow(() -> new ResourceNotFoundException("User", "cognitoSub", cognitoSub));
        return UserProfileResponse.from(user);
    }

    @Transactional
    public UserProfileResponse updateProfileByCognitoSub(String cognitoSub, UserProfileRequest request) {
        User user = userRepository.findByCognitoSub(cognitoSub)
            .orElseThrow(() -> new ResourceNotFoundException("User", "cognitoSub", cognitoSub));
        applyProfileUpdates(user, request);
        return UserProfileResponse.from(userRepository.save(user));
    }

    @Transactional
    public void deleteAccountByCognitoSub(String cognitoSub) {
        log.info("Hard-deleting account by Cognito sub: {}", cognitoSub);
        User user = userRepository.findByCognitoSub(cognitoSub)
            .orElseThrow(() -> new ResourceNotFoundException("User", "cognitoSub", cognitoSub));
        userRepository.delete(user); // DB CASCADE removes all related data
        log.info("Account hard-deleted for Cognito sub: {}", cognitoSub);
    }

    /**
     * Find or create a user by Cognito sub. Called by the JWT auth converter on every request.
     * If a DELETED record exists (from the old soft-delete era), it is hard-deleted so the
     * returning user gets a clean slate.
     */
    @Transactional
    public User findOrCreateUser(String cognitoSub, String email, String name) {
        User user = userRepository.findByCognitoSub(cognitoSub).orElse(null);

        if (user != null && user.getStatus() == User.UserStatus.DELETED) {
            log.info("Re-activating deleted user as fresh account: cognitoSub={}", cognitoSub);
            userRepository.delete(user);
            userRepository.flush();
            user = null;
        }

        if (user == null) {
            log.info("Creating new user from Cognito: cognitoSub={}, email={}", cognitoSub, email);
            user = userRepository.save(User.builder()
                .cognitoSub(cognitoSub)
                .email(email != null ? email : cognitoSub)
                .name(name != null ? name : (email != null ? email : "사용자"))
                .role(User.Role.USER)
                .status(User.UserStatus.ACTIVE)
                .lastLoginAt(Instant.now())
                .build());
        } else if (user.getLastLoginAt() == null ||
                   user.getLastLoginAt().isBefore(Instant.now().minusSeconds(300))) {
            user.setLastLoginAt(Instant.now());
            userRepository.save(user);
        }

        return user;
    }

    private void applyProfileUpdates(User user, UserProfileRequest request) {
        if (request.getName() != null) user.setName(request.getName());
        if (request.getAge() != null) user.setAge(request.getAge());
        if (request.getGender() != null) user.setGender(request.getGender());
        if (request.getFitnessLevel() != null) user.setFitnessLevel(request.getFitnessLevel());
    }
}
