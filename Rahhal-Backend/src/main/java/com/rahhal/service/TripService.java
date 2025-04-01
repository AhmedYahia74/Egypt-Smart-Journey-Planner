package com.rahhal.service;

import com.rahhal.dto.TripDto;
import com.rahhal.entity.Trip;

import java.util.List;

public interface TripService {
    void createTrip(TripDto tripDto);
    TripDto updateTrip(int tripId, TripDto tripDto);
    void deleteTrip(int tripId);
    List<TripDto> viewTrip();

    List<TripDto> viewAllInactiveTrips();
}
