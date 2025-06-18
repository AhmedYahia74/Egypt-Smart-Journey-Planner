package com.rahhal.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class AuthenticationResponseDto {
    @NotNull
    private String authToken;
    @NotNull
    private int userId;
}
