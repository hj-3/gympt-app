package com.gympt.backend.repository;

import com.gympt.backend.domain.Report;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ReportRepository extends JpaRepository<Report, UUID> {

    List<Report> findByUserIdOrderByGeneratedDateDesc(UUID userId);

    List<Report> findByUserIdAndReportType(UUID userId, Report.ReportType reportType);

    List<Report> findByStatus(Report.ReportStatus status);
}
