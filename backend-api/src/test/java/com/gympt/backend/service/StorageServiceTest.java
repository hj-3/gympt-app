package com.gympt.backend.service;

import com.gympt.backend.dto.PresignedUrlResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;
import software.amazon.awssdk.core.client.config.ClientOverrideConfiguration;
import software.amazon.awssdk.core.client.config.SdkClientConfiguration;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.S3ServiceClientConfiguration;

import java.net.URI;
import java.util.UUID;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for StorageService.
 * Tests S3 presigned URL generation for upload and download operations.
 */
@ExtendWith(MockitoExtension.class)
@DisplayName("StorageService Tests")
class StorageServiceTest {

    @Mock
    private S3Client s3Client;

    @InjectMocks
    private StorageService storageService;

    private String testBucketName = "test-bucket";
    private long presignedUrlDuration = 900L; // 15 minutes
    private UUID testUserId;

    @BeforeEach
    void setUp() {
        testUserId = UUID.randomUUID();

        // Set private fields using reflection
        ReflectionTestUtils.setField(storageService, "bucketName", testBucketName);
        ReflectionTestUtils.setField(storageService, "presignedUrlDuration", presignedUrlDuration);

        // Mock S3Client configuration
        S3ServiceClientConfiguration mockConfig = S3ServiceClientConfiguration.builder()
            .region(Region.US_EAST_1)
            .build();

        when(s3Client.serviceClientConfiguration()).thenReturn(mockConfig);
    }

    @Test
    @DisplayName("Should generate presigned upload URL successfully")
    void shouldGeneratePresignedUploadUrlSuccessfully() {
        // Arrange
        String fileType = "workout-videos";
        String fileExtension = ".mp4";

        // Act
        PresignedUrlResponse response = storageService.generatePresignedUploadUrl(
            testUserId,
            fileType,
            fileExtension
        );

        // Assert
        assertThat(response).isNotNull();
        assertThat(response.getUrl()).isNotNull();
        assertThat(response.getS3Key()).isNotNull();
        assertThat(response.getS3Key()).startsWith(fileType + "/" + testUserId);
        assertThat(response.getS3Key()).endsWith(fileExtension);
        assertThat(response.getExpiresIn()).isEqualTo(presignedUrlDuration);

        verify(s3Client, times(1)).serviceClientConfiguration();
    }

    @Test
    @DisplayName("Should generate presigned upload URL with different file types")
    void shouldGeneratePresignedUploadUrlWithDifferentFileTypes() {
        // Arrange
        String fileType = "profile-images";
        String fileExtension = ".jpg";

        // Act
        PresignedUrlResponse response = storageService.generatePresignedUploadUrl(
            testUserId,
            fileType,
            fileExtension
        );

        // Assert
        assertThat(response.getS3Key()).startsWith(fileType + "/" + testUserId);
        assertThat(response.getS3Key()).endsWith(fileExtension);
    }

    @Test
    @DisplayName("Should generate unique S3 keys for multiple requests")
    void shouldGenerateUniqueS3KeysForMultipleRequests() {
        // Arrange
        String fileType = "workout-videos";
        String fileExtension = ".mp4";

        // Act
        PresignedUrlResponse response1 = storageService.generatePresignedUploadUrl(
            testUserId,
            fileType,
            fileExtension
        );
        PresignedUrlResponse response2 = storageService.generatePresignedUploadUrl(
            testUserId,
            fileType,
            fileExtension
        );

        // Assert
        assertThat(response1.getS3Key()).isNotEqualTo(response2.getS3Key());
    }

    @Test
    @DisplayName("Should generate presigned download URL successfully")
    void shouldGeneratePresignedDownloadUrlSuccessfully() {
        // Arrange
        String s3Key = "workout-videos/" + testUserId + "/1234567890_uuid.mp4";

        // Act
        PresignedUrlResponse response = storageService.generatePresignedDownloadUrl(s3Key);

        // Assert
        assertThat(response).isNotNull();
        assertThat(response.getUrl()).isNotNull();
        assertThat(response.getS3Key()).isEqualTo(s3Key);
        assertThat(response.getExpiresIn()).isEqualTo(presignedUrlDuration);

        verify(s3Client, times(1)).serviceClientConfiguration();
    }

    @Test
    @DisplayName("Should handle S3 key format correctly in upload URL")
    void shouldHandleS3KeyFormatCorrectlyInUploadUrl() {
        // Arrange
        String fileType = "reports";
        String fileExtension = ".pdf";

        // Act
        PresignedUrlResponse response = storageService.generatePresignedUploadUrl(
            testUserId,
            fileType,
            fileExtension
        );

        // Assert
        String[] keyParts = response.getS3Key().split("/");
        assertThat(keyParts).hasSize(3); // fileType/userId/filename
        assertThat(keyParts[0]).isEqualTo(fileType);
        assertThat(keyParts[1]).isEqualTo(testUserId.toString());
        assertThat(keyParts[2]).contains("_").endsWith(fileExtension);
    }

    @Test
    @DisplayName("Should set correct expiration time")
    void shouldSetCorrectExpirationTime() {
        // Arrange
        long customDuration = 1800L; // 30 minutes
        ReflectionTestUtils.setField(storageService, "presignedUrlDuration", customDuration);

        String fileType = "workout-videos";
        String fileExtension = ".mp4";

        // Act
        PresignedUrlResponse response = storageService.generatePresignedUploadUrl(
            testUserId,
            fileType,
            fileExtension
        );

        // Assert
        assertThat(response.getExpiresIn()).isEqualTo(customDuration);
    }

    @Test
    @DisplayName("Should handle different file extensions")
    void shouldHandleDifferentFileExtensions() {
        // Test different file extensions
        String[] extensions = {".mp4", ".jpg", ".png", ".pdf", ".json"};

        for (String extension : extensions) {
            // Act
            PresignedUrlResponse response = storageService.generatePresignedUploadUrl(
                testUserId,
                "test-files",
                extension
            );

            // Assert
            assertThat(response.getS3Key()).endsWith(extension);
        }
    }

    @Test
    @DisplayName("Should generate URL for different users")
    void shouldGenerateUrlForDifferentUsers() {
        // Arrange
        UUID userId1 = UUID.randomUUID();
        UUID userId2 = UUID.randomUUID();
        String fileType = "workout-videos";
        String fileExtension = ".mp4";

        // Act
        PresignedUrlResponse response1 = storageService.generatePresignedUploadUrl(
            userId1,
            fileType,
            fileExtension
        );
        PresignedUrlResponse response2 = storageService.generatePresignedUploadUrl(
            userId2,
            fileType,
            fileExtension
        );

        // Assert
        assertThat(response1.getS3Key()).contains(userId1.toString());
        assertThat(response2.getS3Key()).contains(userId2.toString());
        assertThat(response1.getS3Key()).isNotEqualTo(response2.getS3Key());
    }
}
