package com.rahhal.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.*;

import java.time.LocalDateTime;

@Data
@Builder
public class BookingDto {
    private String touristName;

    private String touristEmail;

    @NotBlank
    private LocalDateTime date;
}