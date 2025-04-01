package com.rahhal.repository;

import com.rahhal.dto.TripDto;
import com.rahhal.entity.Company;
import com.rahhal.entity.Trip;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TripRepository extends JpaRepository<Trip, Integer> {
    List<TripDto> findTripByCompany(Company company);
    List<TripDto> findByActiveFalse();

}
