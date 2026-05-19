package com.gympt.backend.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PresignedUrlRequest {

    @NotBlank(message = "File type is required")
    @Pattern(regexp = "^(video|image|report)$", message = "File type must be video, image, or report")
    private String fileType;

    @NotBlank(message = "File extension is required")
    @Pattern(regexp = "^\\.(mp4|mov|avi|jpg|jpeg|png|pdf)$", message = "Invalid file extension")
    private String fileExtension;
}
