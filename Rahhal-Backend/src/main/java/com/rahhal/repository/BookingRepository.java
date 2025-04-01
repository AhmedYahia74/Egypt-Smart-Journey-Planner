package com.rahhal.repository;

import com.rahhal.dto.BookingDto;
import com.rahhal.entity.Booking;
import com.rahhal.entity.Trip;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface BookingRepository extends JpaRepository<Booking, Integer> {
    List<BookingDto> findByTrip(Trip trip);
}
