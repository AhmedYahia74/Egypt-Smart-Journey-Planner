package com.rahhal.service;

import com.rahhal.dto.AuthenticationResponseDto;
import com.rahhal.dto.LogInRequestDto;
import com.rahhal.dto.UserDto;

public interface AuthService {
    void signUp(UserDto request);

    AuthenticationResponseDto logIn(LogInRequestDto request);
}
