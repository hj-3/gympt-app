package com.gympt.backend.controller;

import com.gympt.backend.dto.PresignedUrlRequest;
import com.gympt.backend.dto.PresignedUrlResponse;
import com.gympt.backend.service.StorageService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/storage")
@RequiredArgsConstructor
@Slf4j
@Tag(name = "Storage", description = "File storage and presigned URL endpoints")
@SecurityRequirement(name = "bearerAuth")
public class StorageController {

    private final StorageService storageService;

    @PostMapping("/upload-url")
    @PreAuthorize("hasRole('USER')")
    @Operation(summary = "Generate presigned URL for file upload")
    public ResponseEntity<PresignedUrlResponse> generateUploadUrl(
            @Valid @RequestBody PresignedUrlRequest request,
            Authentication authentication
    ) {
        UUID userId = UUID.fromString(authentication.getName());
        log.info("POST /api/v1/storage/upload-url - userId: {}, fileType: {}",
            userId, request.getFileType());

        PresignedUrlResponse response = storageService.generatePresignedUploadUrl(
            userId,
            request.getFileType(),
            request.getFileExtension()
        );

        return ResponseEntity.ok(response);
    }

    @GetMapping("/download-url")
    @PreAuthorize("hasRole('USER')")
    @Operation(summary = "Generate presigned URL for file download")
    public ResponseEntity<PresignedUrlResponse> generateDownloadUrl(
            @RequestParam String s3Key
    ) {
        log.info("GET /api/v1/storage/download-url - s3Key: {}", s3Key);
        PresignedUrlResponse response = storageService.generatePresignedDownloadUrl(s3Key);
        return ResponseEntity.ok(response);
    }
}
