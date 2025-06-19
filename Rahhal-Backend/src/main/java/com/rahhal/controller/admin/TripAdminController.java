package com.rahhal.controller.admin;

import com.rahhal.dto.TripDto;
import com.rahhal.service.TripService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/admin/trips")
@PreAuthorize("hasRole('ROLE_ADMIN')")
public class TripAdminController {
    private final TripService tripService;

    public TripAdminController(TripService tripService) {
        this.tripService = tripService;
    }

    @Tag(name = "Trip Management - Admin side")
    @Operation(summary = "View all inactive trips",
            description = "allows an admin to view all inactive trips.<br><br>" +
                    "returns a list of TripDto (check schemas section).")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "List of inactive trips"),
    })
    @GetMapping
    public ResponseEntity<List<TripDto>> viewAllInactiveTrips()
    {
        List<TripDto> trips= tripService.viewAllInactiveTrips();
        return ResponseEntity.ok(trips);
    }

    @Tag(name = "Trip Management - Admin side")
    @Operation(summary = "View inactive trips for a company",
            description = "allows an admin to view all inactive trips for a specific company.<br><br>" +
                    "returns a list of TripDto (check schemas section).")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "List of inactive trips for the company"),
            @ApiResponse(responseCode = "404", description = "Company Has No Inactive Trips")
    })
    @GetMapping("/{companyId}")
    public ResponseEntity<List<TripDto>> viewInactiveTripsForCompany(@PathVariable int companyId)
    {
        List<TripDto> trips=tripService.viewInactiveTripsForCompany(companyId);
        return ResponseEntity.ok(trips);
    }

    @Tag(name = "Trip Management - Admin side")
    @Operation(summary = "Activate a trip",
            description = "allows an admin to activate a specific trip (must be inactive).")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "Trip activated successfully"),
            @ApiResponse(responseCode = "409", description = "Trip is already activated"),
            @ApiResponse(responseCode = "404", description = "Trip not found")
    })
    @PutMapping("/{tripId}")
    public ResponseEntity<String> activeTrip(@PathVariable int tripId)
    {
        tripService.activeTrip(tripId);

        return ResponseEntity.ok("Trip activated successfully");
    }

    @Tag(name = "Trip Management - Admin side")
    @Operation(summary = "Delete a trip",
            description = "allows an admin to delete a specific trip (must be inactive).")
    @ApiResponses({
            @ApiResponse(responseCode = "204"),
            @ApiResponse(responseCode = "403", description = "Can't delete this trip is activated"),
            @ApiResponse(responseCode = "404", description = "Trip not found")
    })
    @DeleteMapping("/{tripId}")
    public ResponseEntity<Void> deleteInactiveTrip(@PathVariable int tripId)
    {
        tripService.deleteInactiveTrip(tripId);
        return ResponseEntity.noContent().build();
    }

}
