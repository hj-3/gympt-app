package com.gympt.backend.repository;

import com.gympt.backend.domain.BodyProfile;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface BodyProfileRepository extends JpaRepository<BodyProfile, UUID> {

    @Query("SELECT bp FROM BodyProfile bp WHERE bp.user.id = :userId ORDER BY bp.measurementDate DESC")
    List<BodyProfile> findByUser_IdOrderByMeasurementDateDesc(@Param("userId") UUID userId, Pageable pageable);

    @Query("SELECT bp FROM BodyProfile bp WHERE bp.user.id = :userId ORDER BY bp.measurementDate DESC")
    List<BodyProfile> findByUser_IdOrderByMeasurementDateDesc(@Param("userId") UUID userId);
}
