package com.rahhal.repository;

import com.rahhal.entity.CompanyProfile;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface CompanyProfileRepository extends JpaRepository<CompanyProfile, Integer> {
    Optional<CompanyProfile> findByName(String name);
}
