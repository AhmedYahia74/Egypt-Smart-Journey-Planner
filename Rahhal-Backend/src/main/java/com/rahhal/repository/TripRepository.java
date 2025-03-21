package com.rahhal.repository;

import com.rahhal.entity.Trip;
import com.rahhal.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TripRepository extends JpaRepository<Trip, Integer> {
    List<Trip> findTripByCompany(User company);

}
