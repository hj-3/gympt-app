package com.gympt.backend.service;

import com.gympt.backend.dto.PresignedUrlResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.presigner.S3Presigner;
import software.amazon.awssdk.services.s3.presigner.model.GetObjectPresignRequest;
import software.amazon.awssdk.services.s3.presigner.model.PutObjectPresignRequest;

import java.time.Duration;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class StorageService {

    private final S3Client s3Client;

    @Value("${app.aws.s3.bucket-name}")
    private String bucketName;

    @Value("${app.aws.s3.presigned-url-duration:900}") // 15 minutes default
    private long presignedUrlDuration;

    public PresignedUrlResponse generatePresignedUploadUrl(UUID userId, String fileType, String fileExtension) {
        log.info("Generating presigned upload URL for user: {}, fileType: {}", userId, fileType);

        String s3Key = generateS3Key(userId, fileType, fileExtension);

        try {
            S3Presigner presigner = S3Presigner.builder()
                .region(s3Client.serviceClientConfiguration().region())
                .build();

            PutObjectRequest putObjectRequest = PutObjectRequest.builder()
                .bucket(bucketName)
                .key(s3Key)
                .build();

            PutObjectPresignRequest presignRequest = PutObjectPresignRequest.builder()
                .signatureDuration(Duration.ofSeconds(presignedUrlDuration))
                .putObjectRequest(putObjectRequest)
                .build();

            String url = presigner.presignPutObject(presignRequest).url().toString();

            log.info("Generated presigned upload URL for s3Key: {}", s3Key);
            return PresignedUrlResponse.of(url, s3Key, presignedUrlDuration);

        } catch (Exception e) {
            log.error("Error generating presigned upload URL", e);
            throw new RuntimeException("Failed to generate presigned upload URL", e);
        }
    }

    public PresignedUrlResponse generatePresignedDownloadUrl(String s3Key) {
        log.info("Generating presigned download URL for s3Key: {}", s3Key);

        try {
            S3Presigner presigner = S3Presigner.builder()
                .region(s3Client.serviceClientConfiguration().region())
                .build();

            GetObjectRequest getObjectRequest = GetObjectRequest.builder()
                .bucket(bucketName)
                .key(s3Key)
                .build();

            GetObjectPresignRequest presignRequest = GetObjectPresignRequest.builder()
                .signatureDuration(Duration.ofSeconds(presignedUrlDuration))
                .getObjectRequest(getObjectRequest)
                .build();

            String url = presigner.presignGetObject(presignRequest).url().toString();

            log.info("Generated presigned download URL for s3Key: {}", s3Key);
            return PresignedUrlResponse.of(url, s3Key, presignedUrlDuration);

        } catch (Exception e) {
            log.error("Error generating presigned download URL", e);
            throw new RuntimeException("Failed to generate presigned download URL", e);
        }
    }

    private String generateS3Key(UUID userId, String fileType, String fileExtension) {
        String timestamp = String.valueOf(System.currentTimeMillis());
        String uuid = UUID.randomUUID().toString();

        // Format: {fileType}/{userId}/{timestamp}_{uuid}{extension}
        return String.format("%s/%s/%s_%s%s", fileType, userId, timestamp, uuid, fileExtension);
    }
}
