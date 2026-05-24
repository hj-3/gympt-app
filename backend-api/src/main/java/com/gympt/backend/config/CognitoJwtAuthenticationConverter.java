package com.gympt.backend.config;

import com.gympt.backend.user.User;
import com.gympt.backend.user.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.convert.converter.Converter;
import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.Collection;
import java.util.Collections;

@Component
@RequiredArgsConstructor
@Slf4j
public class CognitoJwtAuthenticationConverter implements Converter<Jwt, AbstractAuthenticationToken> {

    private final UserRepository userRepository;

    @Override
    public AbstractAuthenticationToken convert(Jwt jwt) {
        // Extract claims from Cognito JWT
        String cognitoSub = jwt.getSubject(); // Cognito user ID (sub claim)
        String email = jwt.getClaimAsString("email");
        String name = jwt.getClaimAsString("name");

        log.debug("Converting JWT - cognitoSub: {}, email: {}", cognitoSub, email);

        // Find or create user in database
        User user = userRepository.findByCognitoSub(cognitoSub)
                .orElseGet(() -> {
                    log.info("Creating new user from Cognito: cognitoSub={}, email={}", cognitoSub, email);
                    User newUser = User.builder()
                            .cognitoSub(cognitoSub)
                            .email(email)
                            .name(name)
                            .role(User.Role.USER)
                            .status(User.UserStatus.ACTIVE)
                            .lastLoginAt(Instant.now())
                            .build();
                    return userRepository.save(newUser);
                });

        // Update last login time
        if (user.getLastLoginAt() == null ||
            user.getLastLoginAt().isBefore(Instant.now().minusSeconds(300))) {
            user.setLastLoginAt(Instant.now());
            userRepository.save(user);
        }

        // Create authorities from user role
        Collection<GrantedAuthority> authorities = Collections.singletonList(
                new SimpleGrantedAuthority("ROLE_" + user.getRole().name())
        );

        // Use user.id as the principal name (this is what Authentication.getName() will return)
        return new JwtAuthenticationToken(jwt, authorities, user.getId().toString());
    }
}
