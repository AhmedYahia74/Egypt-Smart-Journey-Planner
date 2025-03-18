package com.rahhal.service;

import com.rahhal.dto.TripDto;
import com.rahhal.entity.Trip;

public interface TripService {
    Trip createTrip(TripDto tripDto);
}
