package com.rahhal.service;

import com.rahhal.dto.BookingRequestDTO;
import com.rahhal.dto.TripDto;
import com.stripe.exception.StripeException;

import java.util.List;

public interface TripService {
    // company methods
    void createTrip(TripDto tripDto);
    TripDto updateTrip(int tripId, TripDto tripDto);
    void deleteTrip(int tripId);
    List<TripDto> viewTripsForCurrentCompany();
    void deleteInactiveTrip(int tripId);

    //admin methods
    List<TripDto> viewAllInactiveTrips();
    List<TripDto> viewInactiveTripsForCompany(int companyId);
    void activeTrip(int tripId);

    //tourist methods
    List<TripDto> viewAllActiveTrips();
    String bookTrip(BookingRequestDTO bookingRequest) throws StripeException;
}
