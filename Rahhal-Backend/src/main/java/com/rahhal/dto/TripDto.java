package com.rahhal.dto;

import jakarta.validation.constraints.*;
import lombok.Builder;
import lombok.Data;

import java.time.LocalDate;

@Data
@Builder
public class TripDto {
    @NotBlank
    private String title;

    private String description;

    @NotBlank
    private String state;

    @NotNull
    @Min(value = 0, message = "Price cannot be negative")
    private double price;

    @NotNull
    private LocalDate date;

    @NotNull
    @Positive
    private int availableSeats;

    @NotNull
    private Boolean active;
}
