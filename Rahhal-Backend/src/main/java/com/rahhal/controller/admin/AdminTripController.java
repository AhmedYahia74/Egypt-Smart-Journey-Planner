package com.rahhal.controller.admin;

import com.rahhal.dto.TripDto;
import com.rahhal.service.TripService;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/admin/trips")
@PreAuthorize("hasRole('ROLE_ADMIN')")
public class AdminTripController {
    private final TripService tripService;

    public AdminTripController(TripService tripService) {
        this.tripService = tripService;
    }


    @GetMapping
    public ResponseEntity<List<TripDto>> viewAllInactiveTrips()
    {
        List<TripDto> trips= tripService.viewAllInactiveTrips();
        return ResponseEntity.ok(trips);
    }

    @GetMapping("/{companyId}")
    public ResponseEntity<List<TripDto>> viewInactiveTripsForCompany(@PathVariable int companyId)
    {
        List<TripDto> trips=tripService.viewInactiveTripsForCompany(companyId);
        return ResponseEntity.ok(trips);
    }

}
