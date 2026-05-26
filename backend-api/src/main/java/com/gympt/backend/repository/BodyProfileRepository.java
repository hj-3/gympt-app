package com.gympt.backend.repository;

import com.gympt.backend.domain.BodyProfile;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface BodyProfileRepository extends JpaRepository<BodyProfile, UUID> {

    List<BodyProfile> findByUser_IdOrderByMeasurementDateDesc(UUID userId, Pageable pageable);

    List<BodyProfile> findByUser_IdOrderByMeasurementDateDesc(UUID userId);
}
