package com.rahhal.security;

import org.springframework.security.core.userdetails.UserDetails;

public interface JwtService {
    String generateToken(UserDetails userDetails);
    boolean isTokenValid(String token, UserDetails userDetails);
    long getExpirationTime();
    String extractUsername(String token);
}
