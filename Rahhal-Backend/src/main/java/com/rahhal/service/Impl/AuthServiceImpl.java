package com.rahhal.service.Impl;

import com.rahhal.dto.AuthenticationResponseDto;
import com.rahhal.dto.LogInRequestDto;
import com.rahhal.dto.TouristDto;
import com.rahhal.entity.User;
import com.rahhal.exception.EntityAlreadyExistsException;
import com.rahhal.exception.EntityNotFoundException;
import com.rahhal.mapper.TouristMapper;
import com.rahhal.repository.UserRepository;
import com.rahhal.security.JwtService;
import com.rahhal.service.AuthService;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.stereotype.Service;

@Service
public class AuthServiceImpl implements AuthService {
    private final UserRepository userRepository;
    private final TouristMapper touristMapper;
    private final AuthenticationManager authenticationManager;
    private final JwtService jwtService;

    public AuthServiceImpl(UserRepository userRepository, TouristMapper touristMapper, AuthenticationManager authenticationManager, JwtService jwtService) {
        this.userRepository = userRepository;
        this.touristMapper = touristMapper;
        this.authenticationManager = authenticationManager;
        this.jwtService = jwtService;
    }

    @Override
    public void signUp(TouristDto request) {
        userRepository.findByEmail(request.getEmail())
                .ifPresent(user ->
                {
                    throw new EntityAlreadyExistsException("User with email " + user.getEmail() + " already exists");
                });

        userRepository.save(touristMapper.mapToEntity(request));
    }

    @Override
    public AuthenticationResponseDto logIn(LogInRequestDto request) {
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.getEmail(), request.getPassword())
        );
        User user = userRepository.findByEmail(request.getEmail())
                .orElseThrow(() -> new EntityNotFoundException("User not found"));
        String jwtToken = jwtService.generateToken(user);
        return AuthenticationResponseDto.builder()
                .accessToken(jwtToken)
                .userId(user.getUserId())
                .build();
    }
}