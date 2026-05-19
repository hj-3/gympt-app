package com.gympt.backend.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import software.amazon.awssdk.services.eventbridge.EventBridgeClient;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.sqs.SqsClient;

import java.net.URI;

@Configuration
public class AwsConfig {

    @Value("${app.aws.region:ap-northeast-2}")
    private String region;

    @Value("${app.aws.s3.endpoint-url:#{null}}")
    private String s3EndpointUrl;

    @Value("${app.aws.dynamodb.endpoint-url:#{null}}")
    private String dynamoDbEndpointUrl;

    @Value("${app.aws.sqs.endpoint-url:#{null}}")
    private String sqsEndpointUrl;

    @Value("${app.aws.eventbridge.endpoint-url:#{null}}")
    private String eventBridgeEndpointUrl;

    @Value("${cloud.aws.credentials.access-key:#{null}}")
    private String accessKey;

    @Value("${cloud.aws.credentials.secret-key:#{null}}")
    private String secretKey;

    @Bean
    public S3Client s3Client() {
        var builder = S3Client.builder().region(Region.of(region));
        
        if (s3EndpointUrl != null && !s3EndpointUrl.isEmpty()) {
            builder.endpointOverride(URI.create(s3EndpointUrl));
            if (accessKey != null && secretKey != null) {
                builder.credentialsProvider(StaticCredentialsProvider.create(
                    AwsBasicCredentials.create(accessKey, secretKey)
                ));
            }
        }
        
        return builder.build();
    }

    @Bean
    public DynamoDbClient dynamoDbClient() {
        var builder = DynamoDbClient.builder().region(Region.of(region));
        
        if (dynamoDbEndpointUrl != null && !dynamoDbEndpointUrl.isEmpty()) {
            builder.endpointOverride(URI.create(dynamoDbEndpointUrl));
            if (accessKey != null && secretKey != null) {
                builder.credentialsProvider(StaticCredentialsProvider.create(
                    AwsBasicCredentials.create(accessKey, secretKey)
                ));
            }
        }
        
        return builder.build();
    }

    @Bean
    public SqsClient sqsClient() {
        var builder = SqsClient.builder().region(Region.of(region));
        
        if (sqsEndpointUrl != null && !sqsEndpointUrl.isEmpty()) {
            builder.endpointOverride(URI.create(sqsEndpointUrl));
            if (accessKey != null && secretKey != null) {
                builder.credentialsProvider(StaticCredentialsProvider.create(
                    AwsBasicCredentials.create(accessKey, secretKey)
                ));
            }
        }
        
        return builder.build();
    }

    @Bean
    public EventBridgeClient eventBridgeClient() {
        var builder = EventBridgeClient.builder().region(Region.of(region));
        
        if (eventBridgeEndpointUrl != null && !eventBridgeEndpointUrl.isEmpty()) {
            builder.endpointOverride(URI.create(eventBridgeEndpointUrl));
            if (accessKey != null && secretKey != null) {
                builder.credentialsProvider(StaticCredentialsProvider.create(
                    AwsBasicCredentials.create(accessKey, secretKey)
                ));
            }
        }
        
        return builder.build();
    }
}
