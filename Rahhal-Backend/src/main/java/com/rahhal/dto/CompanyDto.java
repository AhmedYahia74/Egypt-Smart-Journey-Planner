package com.rahhal.dto;

import jakarta.persistence.Id;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Builder
public class CompanyDto {

//    int companyId;


    @Email
    @NotBlank
    private String email;

    @NotBlank
    @Size(min = 2, message = "password must be at least 2 characters long")
    private String password;

    @NotBlank
    private String name;

    private LocalDateTime subscriptionExpired;

    private String description;

}
