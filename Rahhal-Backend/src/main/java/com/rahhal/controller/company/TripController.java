package com.rahhal.controller.company;

import com.rahhal.dto.BookingDto;
import com.rahhal.dto.TripDto;
import com.rahhal.service.BookingService;
import com.rahhal.service.TripService;
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

    @PostMapping
    public ResponseEntity<Void> createTrip(@Valid @RequestBody TripDto tripDto) {
        tripService.createTrip(tripDto);
        return ResponseEntity.status(HttpStatus.CREATED).build();
    }


    @PutMapping("/{tripId}")
    public ResponseEntity<TripDto> updateTrip(@PathVariable int tripId, @Valid @RequestBody TripDto tripDto) {
        return ResponseEntity.ok(tripService.updateTrip(tripId, tripDto));
    }


    @DeleteMapping("/{tripId}")
    public ResponseEntity<Void>deleteTrip(@PathVariable int tripId)
    {
        tripService.deleteTrip(tripId);
        return ResponseEntity.noContent().build();
    }

    @GetMapping
    public ResponseEntity<List<TripDto>> viewTrip()
    {
        List<TripDto> trips= tripService.viewTrip();
        return ResponseEntity.ok(trips);
    }

    @GetMapping("/bookings/{tripId}")
    public ResponseEntity<List<BookingDto>> viewBookings(@PathVariable int tripId) {
        List<BookingDto> bookings= bookingService.getBookings(tripId);
        return ResponseEntity.ok(bookings);
    }

}
