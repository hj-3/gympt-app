package com.gympt.backend.service;

import com.gympt.backend.domain.BodyProfile;
import com.gympt.backend.dto.BodyProfileRequest;
import com.gympt.backend.dto.BodyProfileResponse;
import com.gympt.backend.exception.ResourceNotFoundException;
import com.gympt.backend.repository.BodyProfileRepository;
import com.gympt.backend.user.User;
import com.gympt.backend.user.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class BodyProfileService {

    private final BodyProfileRepository bodyProfileRepository;
    private final UserRepository userRepository;

    @Transactional
    public BodyProfileResponse createBodyProfile(UUID userId, BodyProfileRequest request) {
        log.info("Creating body profile for user: {}", userId);

        User user = userRepository.findById(userId)
            .orElseThrow(() -> new ResourceNotFoundException("User", "id", userId));

        BodyProfile profile = BodyProfile.builder()
            .user(user)
            .height(request.getHeight())
            .weight(request.getWeight())
            .bodyFat(request.getBodyFat())
            .muscleMass(request.getMuscleMass())
            .postureType(request.getPostureType())
            .measurementDate(request.getMeasurementDate())
            .build();

        profile = bodyProfileRepository.save(profile);
        log.info("Body profile created with id: {}", profile.getId());

        return BodyProfileResponse.from(profile);
    }

    @Transactional(readOnly = true)
    public List<BodyProfileResponse> getHistory(UUID userId, Integer limit) {
        log.info("Getting body profile history for user: {} with limit: {}", userId, limit);

        List<BodyProfile> profiles;
        if (limit != null && limit > 0) {
            profiles = bodyProfileRepository.findByUserIdOrderByMeasurementDateDesc(
                userId,
                PageRequest.of(0, limit)
            );
        } else {
            profiles = bodyProfileRepository.findByUserIdOrderByMeasurementDateDesc(userId);
        }

        return profiles.stream()
            .map(BodyProfileResponse::from)
            .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public BodyProfileResponse getLatest(UUID userId) {
        log.info("Getting latest body profile for user: {}", userId);

        List<BodyProfile> profiles = bodyProfileRepository.findByUserIdOrderByMeasurementDateDesc(
            userId,
            PageRequest.of(0, 1)
        );

        if (profiles.isEmpty()) {
            throw new ResourceNotFoundException("No body profile found for user: " + userId);
        }

        return BodyProfileResponse.from(profiles.get(0));
    }
}
