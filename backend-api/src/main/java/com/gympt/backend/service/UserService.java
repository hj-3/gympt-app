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

import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class UserService {

    private final UserRepository userRepository;

    @Transactional(readOnly = true)
    public UserProfileResponse getProfile(UUID userId) {
        log.info("Getting profile for user: {}", userId);

        User user = userRepository.findById(userId)
            .orElseThrow(() -> new ResourceNotFoundException("User", "id", userId));

        return UserProfileResponse.from(user);
    }

    @Transactional
    public UserProfileResponse updateProfile(UUID userId, UserProfileRequest request) {
        log.info("Updating profile for user: {}", userId);

        User user = userRepository.findById(userId)
            .orElseThrow(() -> new ResourceNotFoundException("User", "id", userId));

        if (request.getName() != null) {
            user.setName(request.getName());
        }
        if (request.getAge() != null) {
            user.setAge(request.getAge());
        }
        if (request.getGender() != null) {
            user.setGender(request.getGender());
        }
        if (request.getFitnessLevel() != null) {
            user.setFitnessLevel(request.getFitnessLevel());
        }

        user = userRepository.save(user);
        log.info("Profile updated successfully for user: {}", userId);

        return UserProfileResponse.from(user);
    }

    @Transactional
    public void deleteAccount(UUID userId) {
        log.info("Deleting account for user: {}", userId);

        User user = userRepository.findById(userId)
            .orElseThrow(() -> new ResourceNotFoundException("User", "id", userId));

        // Soft delete - mark as deleted
        user.setStatus(User.UserStatus.DELETED);
        userRepository.save(user);

        log.info("Account deleted for user: {}", userId);
    }

    @Transactional(readOnly = true)
    public UserProfileResponse getProfileByCognitoSub(String cognitoSub) {
        log.info("Getting profile by Cognito sub: {}", cognitoSub);

        User user = userRepository.findByCognitoSub(cognitoSub)
            .orElseThrow(() -> new ResourceNotFoundException("User", "cognitoSub", cognitoSub));

        return UserProfileResponse.from(user);
    }

    @Transactional
    public UserProfileResponse updateProfileByCognitoSub(String cognitoSub, UserProfileRequest request) {
        log.info("Updating profile by Cognito sub: {}", cognitoSub);

        User user = userRepository.findByCognitoSub(cognitoSub)
            .orElseThrow(() -> new ResourceNotFoundException("User", "cognitoSub", cognitoSub));

        if (request.getName() != null) {
            user.setName(request.getName());
        }
        if (request.getAge() != null) {
            user.setAge(request.getAge());
        }
        if (request.getGender() != null) {
            user.setGender(request.getGender());
        }
        if (request.getFitnessLevel() != null) {
            user.setFitnessLevel(request.getFitnessLevel());
        }

        user = userRepository.save(user);
        log.info("Profile updated successfully for Cognito sub: {}", cognitoSub);

        return UserProfileResponse.from(user);
    }

    @Transactional
    public void deleteAccountByCognitoSub(String cognitoSub) {
        log.info("Deleting account by Cognito sub: {}", cognitoSub);

        User user = userRepository.findByCognitoSub(cognitoSub)
            .orElseThrow(() -> new ResourceNotFoundException("User", "cognitoSub", cognitoSub));

        // Soft delete - mark as deleted
        user.setStatus(User.UserStatus.DELETED);
        userRepository.save(user);

        log.info("Account deleted for Cognito sub: {}", cognitoSub);
    }
}
