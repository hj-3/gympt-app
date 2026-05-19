package com.gympt.backend.domain;

import com.gympt.backend.common.BaseEntity;
import com.gympt.backend.user.User;
import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(name = "reports",
    indexes = {
        @Index(name = "idx_report_user", columnList = "user_id"),
        @Index(name = "idx_report_type", columnList = "report_type"),
        @Index(name = "idx_report_generated_date", columnList = "generated_date")
    }
)
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Report extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Enumerated(EnumType.STRING)
    @Column(name = "report_type", nullable = false, length = 20)
    private ReportType reportType;

    @Column(name = "generated_date", nullable = false)
    private LocalDate generatedDate;

    @Column(name = "s3_key", nullable = false, length = 500)
    private String s3Key;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    @Builder.Default
    private ReportStatus status = ReportStatus.PENDING;

    @Column(name = "file_size")
    private Long fileSize;

    @Column(length = 1000)
    private String metadata;

    public enum ReportType {
        WEEKLY,
        MONTHLY,
        QUARTERLY,
        ANNUAL
    }

    public enum ReportStatus {
        PENDING,
        GENERATING,
        COMPLETED,
        FAILED
    }
}
