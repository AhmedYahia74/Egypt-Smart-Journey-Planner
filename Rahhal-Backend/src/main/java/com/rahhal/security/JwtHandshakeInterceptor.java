package com.rahhal.security;

import com.rahhal.entity.User;
import com.rahhal.exception.EntityNotFoundException;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.http.server.ServletServerHttpRequest;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.socket.WebSocketHandler;
import org.springframework.web.socket.server.HandshakeInterceptor;

import java.util.Map;

public class JwtHandshakeInterceptor implements HandshakeInterceptor {

    private final JwtService jwtService;
    private final CustomUserDetailsService userDetailsService;
    public JwtHandshakeInterceptor(JwtService jwtService, CustomUserDetailsService userDetailsService) {
        this.jwtService = jwtService;
        this.userDetailsService = userDetailsService;
    }

    @Override
    public boolean beforeHandshake(ServerHttpRequest request,
                                   ServerHttpResponse response,
                                   WebSocketHandler wsHandler,
                                   Map<String, Object> attributes) {
        if (request instanceof ServletServerHttpRequest servletRequest) {
            var httpRequest = servletRequest.getServletRequest();
            String token = httpRequest.getParameter("token");

            if (token == null || token.isBlank()) {
                response.setStatusCode(HttpStatus.UNAUTHORIZED);
                return false;
            }

            String userEmail = jwtService.extractUsername(token);
            if (userEmail == null) {
                response.setStatusCode(HttpStatus.UNAUTHORIZED);
                return false;
            }

            User user = null;
            try {
                user = this.userDetailsService.loadUserByUsername(userEmail)
                        .orElseThrow(() -> new EntityNotFoundException("User not found"));
            } catch (EntityNotFoundException e) {
                response.setStatusCode(HttpStatus.UNAUTHORIZED);
                return false;
            }

            if (!jwtService.isTokenValid(token, user)) {
                response.setStatusCode(HttpStatus.UNAUTHORIZED);
                return false;
            }

            attributes.put("user", new StompPrincipal(user.getEmail(), user.getUserId()));
            return true;
        }
        return false;
    }

    @Override
    public void afterHandshake(ServerHttpRequest request, ServerHttpResponse response, WebSocketHandler wsHandler, Exception exception) {
        // No implementation needed
    }

}
