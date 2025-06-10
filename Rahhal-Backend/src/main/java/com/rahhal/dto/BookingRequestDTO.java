package com.rahhal.dto;

import com.rahhal.entity.Tourist;
import com.rahhal.entity.Trip;
import jakarta.validation.constraints.Min;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class BookingRequestDTO {
    private int tripId;
    @Min(value = 1, message = "Number of tickets must be at least 1")
    private int numberOfTickets;
    private Tourist tourist;
    private Trip trip;
}
