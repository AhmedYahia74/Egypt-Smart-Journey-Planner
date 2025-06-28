package com.rahhal.dto;

import jakarta.persistence.Id;
import jakarta.validation.constraints.NotBlank;
import lombok.Builder;
import lombok.Data;


@Data
@Builder
public class UserDto {

    @Id
    private int id;

    @NotBlank
    private String email;

    @NotBlank
    private String name;

    @NotBlank
    private String role;

    private boolean suspended;
}
