package com.gympt.backend.user;

import lombok.RequiredArgsConstructor;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class CustomUserDetailsService implements UserDetailsService {

    private final UserRepository userRepository;

    @Override
    @Transactional(readOnly = true)
    public UserDetails loadUserByUsername(String usernameOrEmail) throws UsernameNotFoundException {
        User user;

        // Try to parse as UUID first (for JWT authentication with userId)
        try {
            UUID userId = UUID.fromString(usernameOrEmail);
            user = userRepository.findById(userId)
                    .orElseThrow(() -> new UsernameNotFoundException("User not found: " + usernameOrEmail));
        } catch (IllegalArgumentException e) {
            // If not a valid UUID, treat as email (for login authentication)
            user = userRepository.findByEmail(usernameOrEmail)
                    .orElseThrow(() -> new UsernameNotFoundException("User not found: " + usernameOrEmail));
        }

        return org.springframework.security.core.userdetails.User.builder()
                .username(user.getId().toString())
                .password(user.getPassword())
                .authorities(Collections.singletonList(
                        new SimpleGrantedAuthority("ROLE_" + user.getRole().name())
                ))
                .accountExpired(false)
                .accountLocked(user.getStatus() != User.UserStatus.ACTIVE)
                .credentialsExpired(false)
                .disabled(user.getStatus() == User.UserStatus.DELETED)
                .build();
    }

    @Transactional(readOnly = true)
    public UserDetails loadUserByEmail(String email) throws UsernameNotFoundException {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new UsernameNotFoundException("User not found: " + email));

        return org.springframework.security.core.userdetails.User.builder()
                .username(user.getId().toString())
                .password(user.getPassword())
                .authorities(Collections.singletonList(
                        new SimpleGrantedAuthority("ROLE_" + user.getRole().name())
                ))
                .accountExpired(false)
                .accountLocked(user.getStatus() != User.UserStatus.ACTIVE)
                .credentialsExpired(false)
                .disabled(user.getStatus() == User.UserStatus.DELETED)
                .build();
    }
}
