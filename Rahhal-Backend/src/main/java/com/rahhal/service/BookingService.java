package com.rahhal.service;

import com.rahhal.dto.BookingDto;

import java.util.List;

public interface BookingService {
    List<BookingDto> getBookings(int tripId);
}
