package com.gympt.backend.config;

import com.gympt.backend.service.UserService;
import com.gympt.backend.user.User;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.convert.converter.Converter;
import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.stereotype.Component;

import java.util.Collection;
import java.util.Collections;

@Component
@RequiredArgsConstructor
@Slf4j
public class CognitoJwtAuthenticationConverter implements Converter<Jwt, AbstractAuthenticationToken> {

    private final UserService userService;

    @Override
    public AbstractAuthenticationToken convert(Jwt jwt) {
        String cognitoSub = jwt.getSubject();
        String email = jwt.getClaimAsString("email");
        String name  = jwt.getClaimAsString("name");

        log.debug("Converting JWT - cognitoSub: {}, email: {}", cognitoSub, email);

        // findOrCreateUser is @Transactional and handles DELETED users gracefully
        User user = userService.findOrCreateUser(cognitoSub, email, name);

        Collection<GrantedAuthority> authorities = Collections.singletonList(
            new SimpleGrantedAuthority("ROLE_" + user.getRole().name())
        );

        return new JwtAuthenticationToken(jwt, authorities, user.getId().toString());
    }
}
