package com.rahhal.controller.tourist;

import com.rahhal.dto.BookingRequestDTO;
import com.rahhal.dto.TripDto;
import com.rahhal.service.TripService;
import com.stripe.exception.StripeException;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/tourist/trips")
@PreAuthorize("hasRole('ROLE_TOURIST')")
public class TripTouristController {
    private final TripService tripService;

    public TripTouristController(TripService tripService) {
        this.tripService = tripService;
    }

    @Tag(name = "Trip Management - Tourist side")
    @Operation(summary = "Get available trips for tourists",
            description = "Allows tourists to view all available trips.")
    @GetMapping
    public ResponseEntity<List<TripDto>> getAvailableTrips() {
        return ResponseEntity.ok(tripService.viewAllActiveTrips());
    }

    @Tag(name = "Trip Management - Tourist side")
    @Operation(summary = "book a trip",
            description = "Allows tourists to book a specific trip by its ID.")
    @GetMapping("/book")
    public ResponseEntity<String> bookTrip(@RequestBody BookingRequestDTO bookingRequest) throws StripeException {
        return ResponseEntity.ok(tripService.bookTrip(bookingRequest));
    }
}
