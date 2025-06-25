package com.rahhal.dto;

import jakarta.validation.constraints.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Builder
@AllArgsConstructor
public class TripDto {

    int tripId;

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

    private LocalDateTime date;

    private int availableSeats;
}
