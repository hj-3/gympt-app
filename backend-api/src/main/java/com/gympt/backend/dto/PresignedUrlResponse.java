package com.gympt.backend.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PresignedUrlResponse {

    private String url;
    private String s3Key;
    private Long expiresIn;

    public static PresignedUrlResponse of(String url, String s3Key, Long expiresIn) {
        return PresignedUrlResponse.builder()
            .url(url)
            .s3Key(s3Key)
            .expiresIn(expiresIn)
            .build();
    }
}
