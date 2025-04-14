package com.rahhal.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class CompanyDto {

    @Email
    @NotBlank
    private String email;

    @NotBlank
    @Size(min = 2, message = "password must be at least 2 characters long")
    private String password;

    @NotBlank
    private String name;
}
