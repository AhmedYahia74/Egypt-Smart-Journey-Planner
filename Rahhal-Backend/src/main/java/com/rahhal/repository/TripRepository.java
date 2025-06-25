package com.rahhal.repository;

import com.rahhal.dto.TripDto;
import com.rahhal.entity.Company;
import com.rahhal.entity.Trip;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TripRepository extends JpaRepository<Trip, Integer> {
    List<TripDto> findTripByCompany(Company company);
    List<TripDto> findByActiveFalse();
    List<TripDto> findByActiveFalseAndCompany_UserId(int companyId);
    @Query("SELECT new com.rahhal.dto.TripDto(t.tripId, t.title, t.description, t.state, t.price, t.duration, t.date, t.availableSeats) " +
            "FROM Trip t WHERE t.active = true AND t.availableSeats IS NOT NULL")
    List<TripDto> findByActiveTrue();
}
