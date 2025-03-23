package com.rahhal.dto;

import jakarta.validation.constraints.*;
import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Builder
public class TripDto {
    @NotBlank
    private String title;

    @NotBlank
    private String description;

    @NotBlank
    private String state;

    @NotNull
    @Min(value = 0, message = "Price cannot be negative")
    private double price;

    @NotBlank
    private String duration;

    @NotNull
    private LocalDateTime date;

    @NotNull
    @Positive
    private int availableSeats;
}
