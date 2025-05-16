package com.rahhal.controller.company;

import com.rahhal.dto.BookingDto;
import com.rahhal.dto.TripDto;
import com.rahhal.service.BookingService;
import com.rahhal.service.TripService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;


@RestController
@RequestMapping("/api/company/trips")
@PreAuthorize("hasRole('ROLE_COMPANY')")
public class TripController {
    private final TripService tripService;
    private final BookingService bookingService;

    public TripController(TripService tripService, BookingService bookingService) {
        this.tripService = tripService;
        this.bookingService = bookingService;
    }

    @Tag(name = "Trip Management - Company side")
    @Operation(summary = "Create a trip",
            description = "allows a company to create a new trip.")
    @ApiResponse(responseCode = "201")
    @PostMapping
    public ResponseEntity<Void> createTrip(@Valid @RequestBody TripDto tripDto) {
        tripService.createTrip(tripDto);
        return ResponseEntity.status(HttpStatus.CREATED).build();
    }

    @Tag(name = "Trip Management - Company side")
    @Operation(summary = "Update a trip",
            description = "allows a company to update a specific trip belonging to it, only trips that are not booked.")
    @ApiResponses({
            @ApiResponse(responseCode = "200"),
            @ApiResponse(responseCode = "403", description = "don't have access to update this trip, or its booked"),
            @ApiResponse(responseCode = "404", description = "Trip not found")
    })
    @PutMapping("/{tripId}")
    public ResponseEntity<TripDto> updateTrip(@PathVariable int tripId, @Valid @RequestBody TripDto tripDto) {
        return ResponseEntity.ok(tripService.updateTrip(tripId, tripDto));
    }

    @Tag(name = "Trip Management - Company side")
    @Operation(summary = "Delete a trip",
            description = "allows a company to delete a specific trip belonging to it, only trips that are not booked.")
    @ApiResponses({
            @ApiResponse(responseCode = "204", description = "Trip deleted"),
            @ApiResponse(responseCode = "403", description = "don't have access to delete this trip, or its booked"),
            @ApiResponse(responseCode = "404", description = "Trip not found")
    })
    @DeleteMapping("/{tripId}")
    public ResponseEntity<Void>deleteTrip(@PathVariable int tripId)
    {
        tripService.deleteTrip(tripId);
        return ResponseEntity.noContent().build();
    }

    @Tag(name = "Trip Management - Company side")
    @Operation(summary = "View all trips",
            description = "allows a company to view all trips belonging to it.<br><br>" +
                    "returns a list of TripDto (check schemas section).")
    @ApiResponse(responseCode = "200", description = "List of trips")
    @GetMapping
    public ResponseEntity<List<TripDto>> viewTrip()
    {
        List<TripDto> trips= tripService.viewTrip();
        return ResponseEntity.ok(trips);
    }

    @Tag(name = "Trip Management - Company side")
    @Operation(summary = "View booking for a trip",
            description = "allows a company to view all bookings for a specific trip belonging to it.<br><br> "+
                    "returns a list of BookingDto (check schemas section).")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "List of bookings for the trip"),
            @ApiResponse(responseCode = "403", description = "You don't have access to view bookings for this trip"),
            @ApiResponse(responseCode = "404", description = "Trip not found")
    })
    @GetMapping("/bookings/{tripId}")
    public ResponseEntity<List<BookingDto>> viewBookings(@PathVariable int tripId) {
        List<BookingDto> bookings= bookingService.getBookings(tripId);
        return ResponseEntity.ok(bookings);
    }

}
