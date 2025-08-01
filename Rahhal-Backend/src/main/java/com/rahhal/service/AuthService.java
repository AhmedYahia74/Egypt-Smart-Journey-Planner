package com.rahhal.service;

import com.rahhal.dto.AuthenticationResponseDto;
import com.rahhal.dto.LogInRequestDto;
import com.rahhal.dto.TouristDto;

public interface AuthService {
    void signUp(TouristDto request);
    AuthenticationResponseDto logIn(LogInRequestDto request);
}
